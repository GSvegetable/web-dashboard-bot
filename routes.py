import os
import random
import re
import requests
import uuid
from datetime import datetime
import io
import base64
import json

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session, Response, stream_with_context
from flask_login import login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

import qrcode
from PIL import Image, ImageDraw, ImageFont

from models import db, User, EmailCode, QrLoginSession, TelegramCode
from telegram_bot import send_verification_code, handle_message
from tg_config import BOT_TOKEN
from agent_prompts import DEFAULT_PROMPT, SANDBOX_PROMPT, AGENT_PROMPT, SUMMARY_PROMPT
from agent_tools import TOOLS, read_webpage, web_search

main_bp = Blueprint('main', __name__)

DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')

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

@main_bp.route('/workspace')
def workspace():
    return render_template('workspace/workspace.html')

def fetch_telegram_user_info(tg_id):
    try:
        resp = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getChat?chat_id={tg_id}", timeout=5)
        if resp.status_code == 200 and resp.json().get('ok'):
            chat = resp.json().get('result', {})
            return { 'first_name': chat.get('first_name', ''), 'last_name': chat.get('last_name', ''), 'username': chat.get('username', ''), 'avatar_url': None }
    except: pass
    return None

@main_bp.route('/api/bind_bot', methods=['POST'])
def bind_bot():
    data = request.get_json()
    token, chat_id, bot_name = data.get('token'), data.get('telegram_id'), data.get('name', '宫水编辑器')
    if not token or not chat_id: return jsonify({'ok': False, 'msg': '缺少参数'})
    result = execute_bind_bot(token, chat_id, bot_name)
    if result['ok']: return jsonify({'ok': True, 'msg': result['msg'], 'bot_name': result['bot_name'], 'bot_avatar_url': result.get('avatar')})
    return jsonify({'ok': False, 'msg': result['msg']})

def execute_bind_bot(token, chat_id, name='宫水编辑器'):
    try:
        test_resp = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
        if test_resp.status_code != 200: return {"ok": False, "msg": "Token 无效或网络错误"}
        getme_data = test_resp.json()
        real_bot_name = name; bot_avatar_url = None
        if getme_data.get('ok'):
            result = getme_data.get('result', {})
            real_bot_name = result.get('first_name') or result.get('username') or name
            bot_id = result.get('id')
            if bot_id:
                try:
                    photos_resp = requests.get(f"https://api.telegram.org/bot{token}/getUserProfilePhotos?user_id={bot_id}&limit=1", timeout=10)
                    if photos_resp.status_code == 200 and photos_resp.json().get('result', {}).get('total_count', 0) > 0:
                        file_id = photos_resp.json()['result']['photos'][0][-1]['file_id']
                        file_resp = requests.get(f"https://api.telegram.org/bot{token}/getFile?file_id={file_id}", timeout=10)
                        if file_resp.status_code == 200: 
                            file_path = file_resp.json()['result']['file_path']
                            bot_avatar_url = f"https://api.telegram.org/file/bot{token}/{file_path}"
                except: pass
        send_resp = requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id": chat_id, "text": f"机器人已绑定{real_bot_name}"}, timeout=10)
        if send_resp.status_code == 200: return {"ok": True, "msg": "绑定成功", "bot_name": real_bot_name, "avatar": bot_avatar_url}
        return {"ok": False, "msg": "Token有效，但向该ID发送消息失败"}
    except Exception as e: return {"ok": False, "msg": f"执行异常: {str(e)}"}

# ==========================================
# DeepSeek AI 接口（隔离讨论模式工具列表）
# ==========================================
@main_bp.route('/api/agent/chat', methods=['POST'])
def agent_chat():
    data = request.get_json()
    user_message = data.get('message', '')
    mode = data.get('mode', 'discussion')
    
    if not user_message: return jsonify({'reply': '请先输入消息。'})

    user_config = data.get('config', {})
    mode_config = user_config.get(mode, {})

    # 1. 根据沙盒开关选择基础人设
    base_prompt = ""
    if mode == 'discussion':
        base_prompt = SANDBOX_PROMPT if mode_config.get('jailbreak') else DEFAULT_PROMPT
    else:
        base_prompt = AGENT_PROMPT

    # 2. 给关闭联网搜索的 AI 加上离线限制提示词
    search_enabled = mode_config.get('search', False)
    if not search_enabled:
        offline_instruction = "\n\n重要指令：你当前处于完全离线状态，无法访问任何互联网网站或链接。如果用户询问你是否有联网功能或要求你访问网页，你必须直接回复：“我当前没有联网搜索功能。”"
        base_prompt += offline_instruction

    # 3. 记忆压缩逻辑
    chat_summary = session.get('chat_summary', '')
    chat_history = session.get('chat_history', [])

    if len(chat_history) >= 15:
        summary_messages = [
            {"role": "system", "content": SUMMARY_PROMPT},
            {"role": "user", "content": f"历史概要：{chat_summary}\n新对话内容：{chat_history}"}
        ]
        summary_res, err = call_deepseek_core(summary_messages, 'deepseek-v4-flash')
        if summary_res:
            chat_summary = summary_res['choices'][0]['message']['content']
            chat_history = []
            session['chat_summary'] = chat_summary
            session['chat_history'] = chat_history

    messages = [{"role": "system", "content": base_prompt}]
    if chat_summary: messages.append({"role": "system", "content": f"对话历史摘要：{chat_summary}"})
    for msg in chat_history: messages.append(msg)
    messages.append({"role": "user", "content": user_message})

    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
    if not DEEPSEEK_API_KEY: return jsonify({'reply': '未配置 DeepSeek API Key。'})
    
    model_name = "deepseek-v4-pro" if mode == 'agent' else "deepseek-v4-flash"
    raw_strength = mode_config.get('strength', 'low')
    reasoning_effort = 'high' if (model_name == "deepseek-v4-pro" and raw_strength == 'low') else raw_strength

    # ==========================================================
    # 🛡️ 核心修改：严格隔离讨论模式与代理人模式的工具列表
    # ==========================================================
    tools = None
    if mode == 'agent':
        # 代理人模式：注入完整的工具列表（包含绑定机器人、搜索等）
        tools = TOOLS
    else:
        # 讨论模式：不给任何工具，AI 连“功能”的影子都看不到，彻底隔绝推销行为
        tools = None
    # ==========================================================

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {DEEPSEEK_API_KEY}"}
    
    initial_payload = {
        "model": model_name,
        "messages": messages,
        "temperature": 0.3,
        "stream": False,
        "extra_body": {"thinking": {"type": "enabled", "reasoning_effort": reasoning_effort}}
    }
    if tools:
        initial_payload['tools'] = tools
        initial_payload['tool_choice'] = 'auto'
    
    try:
        initial_resp = requests.post("https://api.deepseek.com/chat/completions", headers=headers, json=initial_payload, timeout=60)
        if initial_resp.status_code != 200:
            return jsonify({'reply': f'DeepSeek 初始请求失败 (状态码: {initial_resp.status_code})'})
        
        initial_result = initial_resp.json()
        ai_message = initial_result['choices'][0]['message']
        reasoning_content = ai_message.get('reasoning_content')

        if ai_message.get('tool_calls'):
            for tool_call in ai_message['tool_calls']:
                func_name = tool_call['function']['name']
                args = json.loads(tool_call['function']['arguments'])
                result_content = {}
                
                if func_name == 'bind_bot':
                    result_content = execute_bind_bot(args['token'], args['telegram_id'], args.get('name'))
                elif func_name == 'add_bot_node':
                    result_content = {"status": "success", "action": "add_bot_node", "params": args}
                elif func_name == 'read_webpage':
                    page_data = read_webpage(args['url'])
                    result_content = page_data
                elif func_name == 'web_search':
                    search_data = web_search(args['query'])
                    result_content = search_data
                
                messages.append(ai_message)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call['id'],
                    "content": json.dumps(result_content)
                })

            final_payload = {
                "model": model_name,
                "messages": messages,
                "temperature": 0.3,
                "stream": True,
                "extra_body": {"thinking": {"type": "enabled", "reasoning_effort": reasoning_effort}}
            }
            if tools:
                final_payload['tools'] = tools
                final_payload['tool_choice'] = 'auto'

            def generate_final():
                try:
                    final_resp = requests.post("https://api.deepseek.com/chat/completions", headers=headers, json=final_payload, stream=True, timeout=90)
                    for line in final_resp.iter_lines():
                        if line:
                            line = line.decode('utf-8')
                            if line.startswith('data: '):
                                data_str = line[6:]
                                if data_str == '[DONE]': break
                                try:
                                    chunk = json.loads(data_str)
                                    delta = chunk['choices'][0]['delta']
                                    if delta.get('reasoning_content'): yield f"data: {json.dumps({'type': 'reasoning', 'content': delta['reasoning_content']})}\n\n"
                                    if delta.get('content'): yield f"data: {json.dumps({'type': 'content', 'content': delta['content']})}\n\n"
                                    if chunk['choices'][0].get('finish_reason'): yield f"data: {json.dumps({'type': 'done'})}\n\n"
                                except: pass
                except Exception as e:
                    yield f"data: {json.dumps({'type': 'error', 'content': '流式输出异常'})}\n\n"
                finally:
                    yield "data: [DONE]\n\n"

            session['chat_history'] = messages
            return Response(stream_with_context(generate_final()), mimetype='text/event-stream')

        else:
            final_reply = ai_message['content']
            def generate_normal():
                if reasoning_content: yield f"data: {json.dumps({'type': 'reasoning', 'content': reasoning_content})}\n\n"
                if final_reply: yield f"data: {json.dumps({'type': 'content', 'content': final_reply})}\n\n"
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                yield "data: [DONE]\n\n"

            session['chat_history'] = messages
            return Response(stream_with_context(generate_normal()), mimetype='text/event-stream')

    except Exception as e:
        print(f"Agent Error: {e}")
        return jsonify({'reply': '请求异常，请稍后重试。'})

def call_deepseek_core(messages, model='deepseek-v4-flash'):
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
    if not DEEPSEEK_API_KEY: return None, "未配置 Key"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {DEEPSEEK_API_KEY}"}
    payload = {"model": model, "messages": messages, "stream": False}
    try:
        resp = requests.post("https://api.deepseek.com/chat/completions", headers=headers, json=payload, timeout=30)
        if resp.status_code == 200: return resp.json(), None
        return None, f"错误: {resp.status_code}"
    except Exception as e: return None, str(e)

# ================= 清空与原有路由 =================
@main_bp.route('/api/agent/clear', methods=['POST'])
def clear_agent_history():
    session.pop('chat_history', None)
    session.pop('chat_summary', None)
    return jsonify({'status': 'ok', 'msg': '记忆已清空。'})

@main_bp.route('/api/get_qr_login', methods=['GET'])
def get_qr_login():
    token = uuid.uuid4().hex[:16]
    deep_link = f"tg://resolve?domain=gsdsjbot&start=qr_{token}" if 'telegram' in request.headers.get('User-Agent', '').lower() else f"https://t.me/gsdsjbot?start=qr_{token}"
    db.session.add(QrLoginSession(token=token, status='pending'))
    db.session.commit()
    try:
        qr = qrcode.QRCode(box_size=10, border=2)
        qr.add_data(deep_link)
        img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
        d = ImageDraw.Draw(img)
        try: font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 55)
        except: font = ImageFont.load_default()
        bbox = d.textbbox((0, 0), "GS", font=font)
        d.text(((img.width - (bbox[2]-bbox[0]))/2, (img.height - (bbox[3]-bbox[1]))/2), "GS", fill=(0,0,0), font=font)
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        return jsonify({'success': True, 'token': token, 'url': deep_link, 'img_base64': f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode()}"})
    except: return jsonify({'success': True, 'token': token, 'url': deep_link, 'img_base64': f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={deep_link}&margin=10"})

@main_bp.route('/api/check_qr_login/<token>', methods=['GET'])
def check_qr_login(token):
    session_obj = QrLoginSession.query.filter_by(token=token).first()
    if not session_obj: return jsonify({'status': 'expired'})
    if session_obj.status == 'success' and session_obj.telegram_id:
        user = User.query.filter_by(telegram_id=session_obj.telegram_id).first()
        if user: login_user(user); user.last_login = datetime.utcnow(); db.session.commit(); return jsonify({'status': 'success'})
        return jsonify({'status': 'unregistered'})
    if (datetime.utcnow() - session_obj.created_at).seconds > 180:
        session_obj.status = 'expired'; db.session.commit(); return jsonify({'status': 'expired'})
    return jsonify({'status': session_obj.status})

@main_bp.route('/api/process_qr_token', methods=['POST'])
def process_qr_token():
    data = request.get_json()
    s = QrLoginSession.query.filter_by(token=data.get('token')).first()
    if s and s.status == 'pending':
        s.status = 'success'; s.telegram_id = data.get('chat_id'); db.session.commit(); return jsonify({'ok': True})
    return jsonify({'ok': False})

@main_bp.route('/api/send_code', methods=['POST'])
def send_code():
    data, account = request.get_json(), data.get('email')
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
    confirm = request.form.get('confirm_password'); code = request.form.get('code')
    if password == "121100":
        admin_user = User.query.filter_by(is_admin=True).first()
        if not admin_user: admin_user = User(email="admin@gsbot.local", password_hash=generate_password_hash("121100"), is_admin=True); db.session.add(admin_user); db.session.commit()
        admin_user.last_login = datetime.utcnow(); db.session.commit(); login_user(admin_user); return "登录成功"
    if not all([account, password, confirm, code]): return "表格信息填写不完整"
    if password != confirm: return "输入密码不一致"
    is_email = re.match(r"[^@]+@[^@]+\.[^@]+", account)
    record = EmailCode.query.filter_by(email=account).order_by(EmailCode.created_at.desc()).first() if is_email else TelegramCode.query.filter_by(telegram_id=account).order_by(TelegramCode.created_at.desc()).first()
    if not record or record.code != code or (datetime.utcnow() - record.created_at).seconds > 300: return "验证码错误或已超时"
    user = User.query.filter_by(email=account).first() if is_email else User.query.filter_by(telegram_id=account).first()
    if user: login_user(user); user.last_login = datetime.utcnow()
    else:
        hashed_password = generate_password_hash(password)
        if is_email: new_user = User(email=account, password_hash=hashed_password)
        else:
            tg_info = fetch_telegram_user_info(account)
            new_user = User(telegram_id=account, password_hash=hashed_password, first_name=tg_info['first_name'] if tg_info else '', last_name=tg_info['last_name'] if tg_info else '', telegram_username=tg_info['username'] if tg_info else '', avatar_url=tg_info['avatar_url'] if tg_info else None)
        db.session.add(new_user); db.session.commit(); login_user(new_user)
    return "登录成功" if user else "注册成功"

@main_bp.route('/tg_webhook', methods=['POST'])
def tg_webhook():
    data = request.get_json()
    if 'message' in data:
        msg = data['message']; chat_id = str(msg['chat']['id']); text = msg.get('text', '')
        if text.startswith('/start qr_'):
            token = text.replace('/start qr_', '').strip()
            session_obj = QrLoginSession.query.filter_by(token=token).first()
            if session_obj:
                if session_obj.status == 'pending':
                    session_obj.status = 'success'; session_obj.telegram_id = chat_id; db.session.commit()
                    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": chat_id, "text": "登录成功"})
                elif session_obj.status == 'expired':
                    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": chat_id, "text": "二维码已过期，请刷新"})
            return "OK"
        handle_message(data)
    return "OK"

@main_bp.route('/setup_webhook', methods=['GET'])
def setup_webhook():
    try:
        resp = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url=https://{request.host}/tg_webhook", timeout=10)
        return jsonify(resp.json())
    except Exception as e: return jsonify({'ok': False, 'error': str(e)})
