import os
import random
import re
import requests
import uuid
from datetime import datetime
import io
import base64

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# 新增二维码生成库
import qrcode
from PIL import Image, ImageDraw, ImageFont

from models import db, User, EmailCode, BotConfig, QrLoginSession, TelegramCode
from telegram_bot import send_verification_code, handle_message
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
                    'avatar_url': None
                }
    except:
        pass
    return None

@app.route('/api/get_qr_login', methods=['GET'])
def get_qr_login():
    token = uuid.uuid4().hex[:16]
    user_agent = request.headers.get('User-Agent', '').lower()
    if 'telegram' in user_agent:
        deep_link = f"tg://resolve?domain=gsdsjbot&start=qr_{token}"
    else:
        deep_link = f"https://t.me/gsdsjbot?start=qr_{token}"
        
    new_session = QrLoginSession(token=token, status='pending')
    db.session.add(new_session)
    db.session.commit()

    # ✨ 核心改动：在服务器端生成带 "GS" 水印的二维码
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H, # 高容错率，保证水印不影响扫描
            box_size=10,
            border=2,
        )
        qr.add_data(deep_link)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").convert('RGBA')

        # 创建半透明水印叠加层
        txt = Image.new('RGBA', img.size, (255, 255, 255, 0))
        d = ImageDraw.Draw(txt)
        # 为了隐约可见的效果，使用默认字体
        font = ImageFont.load_default()
        text = "GS"
        
        # 计算文字居中位置
        bbox = d.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        x = (img.width - w) / 2
        y = (img.height - h) / 2
        
        # 颜色为浅灰白色(210,210,210)，透明度设为 120 (0-255) 达到“隐隐约约”
        d.text((x, y), text, fill=(210, 210, 210, 120), font=font)
        
        out = Image.alpha_composite(img, txt)
        buffered = io.BytesIO()
        out.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()

        return jsonify({'success': True, 'token': token, 'url': deep_link, 'img_base64': f"data:image/png;base64,{img_base64}"})
    except Exception as e:
        # 如果生成失败（容错保障），退回 qrserver 外部接口，但会丢失水印
        fallback_url = f"https://api.qrserver.com/v1/create-qr-code/?size=400x400&data={deep_link}&margin=10"
        return jsonify({'success': True, 'token': token, 'url': deep_link, 'img_base64': fallback_url})

@app.route('/api/check_qr_login/<token>', methods=['GET'])
def check_qr_login(token):
    session = QrLoginSession.query.filter_by(token=token).first()
    if not session:
        return jsonify({'status': 'expired'})
    
    if session.status == 'success' and session.telegram_id:
        user = User.query.filter_by(telegram_id=session.telegram_id).first()
        if user:
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            return jsonify({'status': 'success'})
        else:
            return jsonify({'status': 'unregistered'})
    
    if (datetime.utcnow() - session.created_at).seconds > 180:
        session.status = 'expired'
        db.session.commit()
        return jsonify({'status': 'expired'})
    return jsonify({'status': session.status})

@app.route('/api/process_qr_token', methods=['POST'])
def process_qr_token():
    data = request.get_json()
    token = data.get('token')
    chat_id = data.get('chat_id')
    session = QrLoginSession.query.filter_by(token=token).first()
    if session and session.status == 'pending':
        session.status = 'success'
        session.telegram_id = chat_id
        db.session.commit()
        return jsonify({'ok': True})
    return jsonify({'ok': False})

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
        success, _ = send_verification_code(account, code)
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
            if session:
                if session.status == 'pending':
                    session.status = 'success'
                    session.telegram_id = chat_id
                    db.session.commit()
                    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                    requests.post(url, json={"chat_id": chat_id, "text": "登录成功"})
                elif session.status == 'expired':
                    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                    requests.post(url, json={"chat_id": chat_id, "text": "二维码已过期，请刷新"})
            return "OK"
        
        handle_message(data)
        
    return "OK"

@app.route('/setup_webhook', methods=['GET'])
def setup_webhook():
    try:
        webhook_url = f"https://{request.host}/tg_webhook"
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={webhook_url}"
        resp = requests.get(url, timeout=10)
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=8080)
