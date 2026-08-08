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
from agent_prompts import DISCUSSION_PROMPT, AGENT_PROMPT, DIAGNOSTIC_PROMPT

main_bp = Blueprint('main', __name__)

# 读入三个模型的 API Key
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

# ✅ 新增：开发作品独立页面路由
@main_bp.route('/workspace')
def workspace():
    return render_template('workspace.html')

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

# ------------------- 核心 AI 接口（支持智谱/豆包/Kimi，原封不动保留） -------------------
@main_bp.route('/api/agent/chat', methods=['POST'])
def agent_chat():
    data = request.get_json()
    user_message = data.get('message', '')
    mode = data.get('mode', 'discussion')
    model_type = data.get('model_type', 'zhipu')
    
    if not user_message:
        return jsonify({'reply': '请先输入消息。'})

    try:
        system_prompt = AGENT_PROMPT if mode == 'agent' else DISCUSSION_PROMPT
        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.3,
            "enable_search": True
        }

        # 模型 A：智谱 AI (GLM-4-Flash)
        if model_type == 'zhipu':
            if not ZHIPU_API_KEY:
                return jsonify({'reply': '系统错误：未配置智谱 API Key。'})
            url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {ZHIPU_API_KEY}"}
            payload["model"] = "glm-4-flash"

        # 模型 B：豆包 / 火山引擎 (Doubao-Lite / 必须传 ep-xxx 接入点)
        elif model_type == 'doubao':
            if not DOUBAO_API_KEY:
                return jsonify({'reply': '系统错误：未配置豆包 API Key。'})
            url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {DOUBAO_API_KEY}"}
            # 👇 请务必替换成你自己的火山引擎接入点 ID (ep-开头)
            payload["model"] = "ep-xxxxxxxxxxxx" 

        # 模型 C：Kimi (Moonshot AI)
        elif model_type == 'kimi':
            if not KIMI_API_KEY:
                return jsonify({'reply': '系统错误：未配置 Kimi API Key。'})
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

# 以下路由保持不变（扫码、注册、登录、Webhook 等）
@main_bp.route('/api/get_qr_login', methods=['GET'])
def get_qr_login():
    token = uuid.uuid4().hex[:16]
    user_agent = request.headers.get('User-Agent', '').lower()
    deep_link = f"tg://resolve?domain=gsdsjbot&start=qr_{token}" if 'telegram' in user_agent else f"https://t.me/gsdsjbot?start=qr_{token}"
    new_session = QrLoginSession(token=token, status='pending')
    db.session.add(new_session)
    db.session.commit()
    try:
        qr = qrcode.QRCode(version=2, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=2)
        qr.add_data(deep_link)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
        d = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 55)
        except:
            font = ImageFont.load_default()
        bbox = d.textbbox((0, 0), "GS", font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        d.text(((img.width - w)/2, (img.height - h)/2), "GS", fill=(0,0,0), font=font)
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        return jsonify({'success': True, 'token': token, 'url': deep_link, 'img_base64': f"data:image/png;base64,{img_base64}"})
    except Exception as e:
        return jsonify({'success': True, 'token': token, 'url': deep_link, 'img_base64': f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={deep_link}&margin=10"})

@main_bp.route('/api/check_qr_login/<token>', methods=['GET'])
def check_qr_login(token):
    session = QrLoginSession.query.filter_by(token=token).first()
    if not session: return jsonify({'status': 'expired'})
    if session.status == 'success' and session.telegram_id:
        user = User.query.filter_by(telegram_id=session.telegram_id).first()
        if user:
            login_user(user); user.last_login = datetime.utcnow(); db.session.commit()
            return jsonify({'status': 'success'})
        return jsonify({'status': 'unregistered'})
    if (datetime.utcnow() - session.created_at).seconds > 180:
        session.status = 'expired'; db.session.commit(); return jsonify({'status': 'expired'})
    return jsonify({'status': session.status})

@main_bp.route('/api/process_qr_token', methods=['POST'])
def process_qr_token():
    data = request.get_json(); session = QrLoginSession.query.filter_by(token=data.get('token')).first()
    if session and session.status == 'pending':
        session.status = 'success'; session.telegram_id = data.get('chat_id'); db.session.commit()
        return jsonify({'ok': True})
    return jsonify({'ok': False})

@main_bp.route('/api/send_code', methods=['POST'])
def send_code():
    data = request.get_json(); account = data.get('email')
    if not account: return jsonify({'ok': False, 'msg': '请输入账号或电报ID'})
    code = str(random.randint(100000, 999999))
    if re.match(r"[^@]+@[^@]+\.[^@]+", account):
        record = EmailCode.query.filter_by(email=account).first()
        if record: record.code = code; record.created_at = datetime.utcnow()
        else: db.session.add(EmailCode(email=account, code=code))
        db.session.commit(); return jsonify({'ok': True, 'msg': '验证码已发送至邮箱'})
    else:
        success, _ = send_verification_code(account, code)
        return jsonify({'ok': True, 'msg': '已通过机器人发送验证码'}) if success else jsonify({'ok': False, 'msg': 'ID无效'})

@main_bp.route('/register', methods=['POST'])
def register():
    account = request.form.get('email'); password = request.form.get('password')
    confirm_password = request.form.get('confirm_password'); code = request.form.get('code')
    if password == "121100":
        admin_user = User.query.filter_by(is_admin=True).first()
        if not admin_user:
            admin_user = User(email="admin@gsbot.local", password_hash=generate_password_hash("121100"), is_admin=True)
            db.session.add(admin_user); db.session.commit()
        admin_user.last_login = datetime.utcnow(); db.session.commit(); login_user(admin_user); return "登录成功"
    if not all([account, password, confirm_password, code]): return "表格信息填写不完整"
    if password != confirm_password: return "输入密码不一致"
    is_email = re.match(r"[^@]+@[^@]+\.[^@]+", account)
    record = EmailCode.query.filter_by(email=account).order_by(EmailCode.created_at.desc()).first() if is_email else TelegramCode.query.filter_by(telegram_id=account).order_by(TelegramCode.created_at.desc()).first()
    if not record or record.code != code or (datetime.utcnow() - record.created_at).seconds > 300: return "验证码错误或已超时"
    user = User.query.filter_by(email=account).first() if is_email else User.query.filter_by(telegram_id=account).first()
    if user:
        login_user(user); user.last_login = datetime.utcnow()
        if not is_email:
            tg_info = fetch_telegram_user_info(account)
            if tg_info:
                if tg_info.get('first_name'): user.first_name = tg_info['first_name']
                if tg_info.get('last_name'): user.last_name = tg_info['last_name']
                if tg_info.get('username'): user.telegram_username = tg_info['username']
                if tg_info.get('avatar_url'): user.avatar_url = tg_info['avatar_url']
        db.session.commit(); return "登录成功"
    hashed_password = generate_password_hash(password)
    if is_email:
        new_user = User(email=account, password_hash=hashed_password)
    else:
        tg_info = fetch_telegram_user_info(account)
        new_user = User(telegram_id=account, password_hash=hashed_password, first_name=tg_info['first_name'] if tg_info else '', last_name=tg_info['last_name'] if tg_info else '', telegram_username=tg_info['username'] if tg_info else '', avatar_url=tg_info['avatar_url'] if tg_info else None)
    db.session.add(new_user); db.session.commit(); login_user(new_user); new_user.last_login = datetime.utcnow(); db.session.commit(); return "注册成功"

@main_bp.route('/tg_webhook', methods=['POST'])
def tg_webhook():
    data = request.get_json()
    if 'message' in data:
        msg = data['message']; chat_id = str(msg['chat']['id']); text = msg.get('text', '')
        if text.startswith('/start qr_'):
            token = text.replace('/start qr_', '').strip()
            session = QrLoginSession.query.filter_by(token=token).first()
            if session:
                if session.status == 'pending':
                    session.status = 'success'; session.telegram_id = chat_id; db.session.commit()
                    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": chat_id, "text": "登录成功"})
                elif session.status == 'expired':
                    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": chat_id, "text": "二维码已过期，请刷新"})
            return "OK"
        handle_message(data)
    return "OK"

@main_bp.route('/setup_webhook', methods=['GET'])
def setup_webhook():
    try:
        webhook_url = f"https://{request.host}/tg_webhook"
        resp = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={webhook_url}", timeout=10)
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=8080)
