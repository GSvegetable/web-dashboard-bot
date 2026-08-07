import os
import random
import re
import requests
import uuid
from datetime import datetime
import io
import base64
import json

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

import qrcode
from PIL import Image, ImageDraw, ImageFont

from models import db, User, EmailCode, BotConfig, QrLoginSession, TelegramCode
from telegram_bot import send_verification_code, handle_message
from tg_config import BOT_TOKEN
from agent_prompts import DISCUSSION_PROMPT, AGENT_PROMPT

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24).hex())
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///local.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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
# ✅ 后端：解析泛化指令并返回技术日志
# ==========================================
@app.route('/api/agent/chat', methods=['POST'])
def agent_chat():
    data = request.get_json()
    user_message = data.get('message', '')
    mode = data.get('mode', 'discussion')
    
    if not user_message:
        return jsonify({'reply': '请先输入消息。'})

    if not ZHIPU_API_KEY:
        return jsonify({'reply': '系统错误：未配置智谱 API Key。'})

    try:
        url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {ZHIPU_API_KEY}"
        }
        
        system_prompt = AGENT_PROMPT if mode == 'agent' else DISCUSSION_PROMPT

        payload = {
            "model": "glm-4-flash",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.3
        }
        
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        if resp.status_code == 200:
            result = resp.json()
            reply = result['choices'][0]['message']['content']
            
            try:
                cmd = json.loads(reply)
                
                # 如果是建议跳转的指令
                if cmd.get('action') == 'suggest_agent':
                    return jsonify({
                        'reply': cmd.get('original', ''),
                        'action': 'suggest_agent'
                    })
                
                # 如果是音乐控制指令（含技术日志）
                if cmd.get('action') == 'music':
                    return jsonify({
                        'reply': cmd.get('log', ''),
                        'action': 'music',
                        'sub_action': cmd.get('sub_action'),
                        'delay': cmd.get('delay', 0)
                    })
                    
                return jsonify({'reply': reply, 'action': cmd.get('action')})
            except:
                return jsonify({'reply': reply})
        else:
            return jsonify({'reply': f'API Error: {resp.status_code}'})
    except Exception as e:
        print(f"Agent Error: {e}")
        return jsonify({'reply': 'An error occurred.'})
# ==========================================
# ... 下方保留你原本的 QQ/微信/扫码登录等路由，保持不变 ...
