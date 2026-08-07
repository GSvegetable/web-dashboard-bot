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

import qrcode
from PIL import Image, ImageDraw, ImageFont

from models import db, User, EmailCode, BotConfig, QrLoginSession, TelegramCode
from telegram_bot import send_verification_code, handle_message
from tg_config import BOT_TOKEN

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24).hex())
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///local.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ✅ 换成智谱 AI 的 API Key 环境变量名
ZHIPU_API_KEY = os.getenv('ZHIPU_API_KEY')

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

# ==========================================
# ✅ 替换为：智谱 AI (GLM-4-Flash) 对话接口
# ==========================================
@app.route('/api/agent/chat', methods=['POST'])
def agent_chat():
    data = request.get_json()
    user_message = data.get('message', '')
    if not user_message:
        return jsonify({'reply': '请先输入消息。'})

    if not ZHIPU_API_KEY:
        return jsonify({'reply': '系统错误：未配置智谱 API Key（请检查环境变量 ZHIPU_API_KEY）。'})

    try:
        # 智谱 AI 官方对话补全接口
        url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {ZHIPU_API_KEY}"
        }
        
        # 使用性价比极高的 glm-4-flash 模型（非常适合 Agent 场景）
        payload = {
            "model": "glm-4-flash",
            "messages": [
                {"role": "system", "content": "你是一个智能助手，名字叫 Agent。用户指令必须严格遵守。如果用户要求打开网页功能，请直接返回对应的操作指令。"},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.3
        }
        
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        if resp.status_code == 200:
            result = resp.json()
            reply = result['choices'][0]['message']['content']
            return jsonify({'reply': reply})
        else:
            return jsonify({'reply': f'API 请求出错 (状态码: {resp.status_code})'})
    except Exception as e:
        print(f"Agent Error: {e}")
        return jsonify({'reply': '请求处理过程中发生异常，请稍后重试。'})
# ==========================================

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

    try:
        qr = qrcode.QRCode(
            version=2,
            error_correction=qrcode.constants.ERROR_CORRECT_H, 
            box_size=10,
            border=2,
        )
        qr.add_data(deep_link)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
        d = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 55)
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 55)
            except:
                font = ImageFont.load_default()
        text = "GS"
        bbox = d.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        x = (img.width - w) / 2
        y = (img.height - h) / 2
        d.text((x, y), text, fill=(0, 0, 0), font=font)
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).
