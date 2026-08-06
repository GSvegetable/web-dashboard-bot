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

from models import db, User, EmailCode, BotConfig, QrLoginSession
from tg_models import TelegramCode
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

# --- 页面路由 ---
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

# --- ✨ 扫码登录相关 API ✨ ---
@app.route('/api/get_qr_login', methods=['GET'])
def get_qr_login():
    # 生成唯一的临时 Token
    token = uuid.uuid4().hex[:16]
    # 构建 Telegram 链接 (使用 start 参数传递 token)
    deep_link = f"https://t.me/gsdsjbot?start=qr_{token}"
    
    # 存入数据库
    new_session = QrLoginSession(token=token, status='pending')
    db.session.add(new_session)
    db.session.commit()
    
    return jsonify({'success': True, 'token': token, 'url': deep_link})

@app.route('/api/check_qr_login/<token>', methods=['GET'])
def check_qr_login(token):
    session = QrLoginSession.query.filter_by(token=token).first()
    if not session:
        return jsonify({'status': 'expired'})
    if session.status == 'success':
        return jsonify({'status': 'success'})
    # 如果超过 3 分钟没扫，标记为过期
    if (datetime.utcnow() - session.created_at).seconds > 180:
        session.status = 'expired'
        db.session.commit()
        return jsonify({'status': 'expired'})
    return jsonify({'status': session.status})

# --- 常规逻辑 ---
def fetch_telegram_user_info(tg_id):
    # ... (保持你之前的获取头像代码不变) ...
    pass

@app.route('/api/send_code', methods=['POST'])
def send_code():
    # ... (保持你之前的验证码发送逻辑不变) ...
    pass

@app.route('/register', methods=['POST'])
def register():
    # ... (保持你之前的注册逻辑不变) ...
    pass

# --- ✨ 关键：处理电报机器人回调 ✨ ---
@app.route('/tg_webhook', methods=['POST'])
def tg_webhook():
    data = request.get_json()
    if 'message' in data:
        msg = data['message']
        chat_id = str(msg['chat']['id'])
        text = msg.get('text', '')
        
        # 如果用户发来的是 /start qr_xxxxxx
        if text.startswith('/start qr_'):
            token = text.replace('/start qr_', '').strip()
            session = QrLoginSession.query.filter_by(token=token).first()
            if session and session.status == 'pending':
                # 标记为成功，记录用户的真实 Telegram ID
                session.status = 'success'
                session.telegram_id = chat_id
                db.session.commit()
                # 发送成功提示给用户
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                requests.post(url, json={"chat_id": chat_id, "text": "✅ 授权成功，请返回网页查看。"})
                return "OK"
    return "OK"

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=8080)
