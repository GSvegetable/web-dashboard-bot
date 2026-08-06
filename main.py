import os
import random
import re
import requests
import uuid
from datetime import datetime

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# 从 models 导入所有表和表定义
from models import db, User, EmailCode, BotConfig, QrLoginSession, TelegramCode
from telegram_bot import send_verification_code
from tg_config import BOT_TOKEN

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24).hex())
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///local.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def splash():
    return render_template('splash.html')

@app.route('/warehouse')
def warehouse():
    return render_template('warehouse.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('splash'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if not current_user.is_authenticated or not current_user.is_admin:
        return "无权访问，请使用管理员密码登录", 403
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/dashboard.html', users=users)

# --- 🔥 补充完整了原本为空的获取用户信息函数 ---
def fetch_telegram_user_info(tg_id):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChat?chat_id={tg_id}"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('ok'):
                chat = data.get('result', {})
                return {
                    'first_name': chat.get('first_name', ''),
                    'last_name': chat.get('last_name', ''),
                    'username': chat.get('username', ''),
                    'avatar_url': None  # 需要额外下载头像API，此处留空
                }
    except:
        pass
    return None

# --- 扫码登录相关 API ---
@app.route('/api/get_qr_login', methods=['GET'])
def get_qr_login():
    token = uuid.uuid4().hex[:16]
    deep_link = f"https://t.me/gsdsjbot?start=qr_{token}"
    new_session = QrLoginSession(token=token, status='pending')
    db.session.add(new_session)
    db.session.commit()
    return jsonify({'success': True, 'token': token, 'url': deep_link})

@app.route('/api/check_qr_login/<token>', methods=['GET'])
def check_qr_login(token):
    session = QrLoginSession.query.filter_by(token=token).first()
    if not session:
        return jsonify({'status': 'expired'})
    
    # 🔥 核心优化：一旦状态变为 success，立刻执行后端登录（登录用户）
    if session.status == 'success' and session.telegram_id:
        user = User.query.filter_by(telegram_id=session.telegram_id).first()
        if user:
            login_user(user)  # 设置用户会话
            user.last_login = datetime.utcnow()
            db.session.commit()
            return jsonify({'status': 'success'})
        else:
            # 如果扫码了但还没注册，可以通过逻辑引导跳转注册
            return jsonify({'status': 'unregistered'})
    
    if (datetime.utcnow() - session.created_at).seconds > 180:
        session.status = 'expired'
        db.session.commit()
        return jsonify({'status': 'expired'})
    return jsonify({'status': session.status})

@app.route('/api/send_code', methods=['POST'])
def send_code():
    data = request.get_json()
    account = data.get('email')
    if not account: return jsonify({'ok': False, 'msg': '请输入账号或电报ID'})
    code = str(random.randint(100000, 999999))
    is_email = re.match(r"[^@]+@[^@]+\.[^@]+", account)
    
    if is_email:
        record = EmailCode.query.filter_by(email=account).first()
        if record:
            record.code = code; record.created_at = datetime.utcnow()
        else:
            new_record = EmailCode(email=account, code=code)
            db.session.add(new_record)
        db.session.commit()
        return jsonify({'ok': True, 'msg': '验证码已发送至邮箱'})
    else:
        success, _ = send_verification_code(account)
        if success: return jsonify({'ok': True, 'msg': '已通过Telegram机器人发送验证码'})
        else: return jsonify({'ok': False, 'msg': 'ID无效或机器人未响应'})

@app.route('/register', methods=['POST'])
def register():
    account = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    code = request.form.get('code')
    
    if password == "121100":
        admin_user = User.query.filter_by(is_admin=True).first()
        if not admin_user:
            hashed_password = generate_password_hash("121100")
            admin_user = User(email="admin@gsbot.local", password_hash=hashed_password, is_admin=True)
            db.session.add(admin_user)
            db.session.commit()
        admin_user.last_login = datetime.utcnow()
        db.session.commit()
        login_user(admin_user)
        return "登录成功"

    if not all([account, password, confirm_password, code]): return "表格信息填写不完整"
    if password != confirm_password: return "输入密码不一致"
    
    is_email = re.match(r"[^@]+@[^@]+\.[^@]+", account)
    
    valid_code = False
    if is_email:
        record = EmailCode.query.filter_by(email=account).order_by(EmailCode.created_at.desc()).first()
        if record and record.code == code and (datetime.utcnow() - record.created_at).seconds <= 300: valid_code = True
    else:
        record = TelegramCode.query.filter_by(telegram_id=account).order_by(TelegramCode.created_at.desc()).first()
        if record and record.code == code and (datetime.utcnow() - record.created_at).seconds <= 300: valid_code = True
            
    if not valid_code: return "验证码错误或已超时"
    
    user = None
    if is_email: user = User.query.filter_by(email=account).first()
    else: user = User.query.filter_by(telegram_id=account).first()
        
    if user:
        login_user(user)
        user.last_login = datetime.utcnow()
        if not is_email:
            tg_info = fetch_telegram_user_info(account)
            if tg_info:
                if tg_info.get('first_name'): user.first_name = tg_info['first_name']
                if tg_info.get('last_name'): user.last_name = tg_info['last_name']
                if tg_info.get('username'): user.telegram_username = tg_info['username']
                if tg_info.get('avatar_url'): user.avatar_url = tg_info['avatar_url']
        db.session.commit()
        return "登录成功"
    
    hashed_password = generate_password_hash(password)
    if is_email: 
        new_user = User(email=account, password_hash=hashed_password)
    else:
        tg_info = fetch_telegram_user_info(account)
        if tg_info:
            new_user = User(telegram_id=account, password_hash=hashed_password, first_name=tg_info['first_name'], last_name=tg_info['last_name'], telegram_username=tg_info['username'], avatar_url=tg_info['avatar_url'])
        else:
            new_user = User(telegram_id=account, password_hash=hashed_password)
        
    db.session.add(new_user)
    db.session.commit()
    login_user(new_user)
    new_user.last_login = datetime.utcnow()
    db.session.commit()
    return "注册成功"

@app.route('/tg_webhook', methods=['POST'])
def tg_webhook():
    data = request.get_json()
    if 'message' in data:
        msg = data['message']
        chat_id = str(msg['chat']['id'])
        text = msg.get('text', '')
        if text.startswith('/start qr_'):
            token = text.replace('/start qr_', '').strip()
            session = QrLoginSession.query.filter_by(token=token).first()
            if session and session.status == 'pending':
                session.status = 'success'
                session.telegram_id = chat_id
                db.session.commit()
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                requests.post(url, json={"chat_id": chat_id, "text": "✅ 授权成功，请返回网页查看。"})
                return "OK"
    return "OK"

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=8080)
