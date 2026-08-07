import os
import random
import re
import requests
import uuid
from datetime import datetime
import io
import base64
import json

from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

import qrcode
from PIL import Image, ImageDraw, ImageFont

from models import db, User, EmailCode, QrLoginSession, TelegramCode
from telegram_bot import send_verification_code, handle_message
from tg_config import BOT_TOKEN
# ✅ 引入新的诊断提示词
from agent_prompts import DISCUSSION_PROMPT, AGENT_PROMPT, DIAGNOSTIC_PROMPT

main_bp = Blueprint('main', __name__)

ZHIPU_API_KEY = os.getenv('ZHIPU_API_KEY')
DOUBAO_API_KEY = os.getenv('DOUBAO_API_KEY')
KIMI_API_KEY = os.getenv('KIMI_API_KEY')

@main_bp.route('/')
def splash():
    return render_template('splash.html')

@main_bp.route('/warehouse')
def warehouse():
    return render_template('warehouse.html')

@main_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.splash'))

@main_bp.route('/admin/dashboard')
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

# ------------------- 核心 AI 接口（支持诊断模式切换） -------------------
@main_bp.route('/api/agent/chat', methods=['POST'])
def agent_chat():
    data = request.get_json()
    user_message = data.get('message', '')
    mode = data.get('mode', 'discussion')
    model_type = data.get('model_type', 'zhipu')
    
    if not user_message:
        return jsonify({'reply': '请先输入消息。'})

    try:
        # ✅ 核心逻辑：如果用户输入以 [执行诊断] 开头，则切换到诊断模式
        if user_message.startswith('[执行诊断]'):
            system_prompt = DIAGNOSTIC_PROMPT
        else:
            system_prompt = AGENT_PROMPT if mode == 'agent' else DISCUSSION_PROMPT

        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.3,
            "enable_search": True
        }

        # 模型路由配置（与之前一致）
        if model_type == 'zhipu':
            if not ZHIPU_API_KEY: return jsonify({'reply': '系统错误：未配置智谱 API Key。'})
            url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {ZHIPU_API_KEY}"}
            payload["model"] = "glm-4-flash"
        elif model_type == 'doubao':
            if not DOUBAO_API_KEY: return jsonify({'reply': '系统错误：未配置豆包 API Key。'})
            url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {DOUBAO_API_KEY}"}
            payload["model"] = "ep-xxxxxxxxxxxx" 
        elif model_type == 'kimi':
            if not KIMI_API_KEY: return jsonify({'reply': '系统错误：未配置 Kimi API Key。'})
            url = "https://api.moonshot.cn/v1/chat/completions"
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {KIMI_API_KEY}"}
            payload["model"] = "moonshot-v1-8k"
        else:
            return jsonify({'reply': '未选择有效的模型。'})

        # 发起请求
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if resp.status_code == 200:
            result = resp.json()
            reply = result['choices'][0]['message']['content']
            
            stripped_reply = reply
            if '```json' in stripped_reply:
                stripped_reply = stripped_reply.replace('```json', '').replace('```', '').strip()
            
            try:
                parsed = json.loads(stripped_reply)
                if isinstance(parsed, dict) and 'reply' in parsed:
                    return jsonify({'reply': parsed['reply'], 'actions': parsed.get('actions', [])})
                if isinstance(parsed, dict) and parsed.get('action') == 'ASK_CONFIRM':
                    return jsonify(parsed)
                if isinstance(parsed, dict) and parsed.get('action'):
                    return jsonify({'reply': parsed.get('reply', '已执行。'), 'actions': [parsed]})
                return jsonify({'reply': stripped_reply})
            except:
                return jsonify({'reply': stripped_reply})
        else:
            return jsonify({'reply': f'API 请求出错 (状态码: {resp.status_code})'})
    except Exception as e:
        print(f"Agent Error: {e}")
        return jsonify({'reply': '请求异常，请稍后重试。'})

# ...（下方其余路由保持不变）
