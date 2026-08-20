from flask import render_template, redirect, url_for, abort, request, jsonify
from models import db, PendingBind
import requests
from . import main_bp

@main_bp.route('/')
def splash():
    return render_template('splash.html')

@main_bp.route('/warehouse')
def warehouse():
    return redirect(url_for('main.workspace'))

@main_bp.route('/workspace')
def workspace():
    return render_template('workspace/workspace.html')

@main_bp.route('/community')
def community():
    return render_template('community.html')

@main_bp.route('/settings')
def settings_redirect():
    return redirect(url_for('main.settings_page', page='profile'))

@main_bp.route('/settings/<string:page>')
def settings_page(page):
    ALLOWED_SETTINGS = ['profile', 'stars', 'appearance', 'accessibility', 'notifications', 'billing', 'email', 'password', 'sessions', 'keys', 'credentials', 'organizations', 'enterprises', 'moderation', 'repositories', 'codespaces', 'packages']
    if page not in ALLOWED_SETTINGS:
        abort(404)
    return render_template('settings.html', active_page=page)

@main_bp.route('/workspace/add_bot')
def add_bot():
    return render_template('workspace/add_bot.html')

# ==========================================
# Telegram Webhook（处理按钮点击）
# ==========================================
@main_bp.route('/tg_webhook', methods=['POST'])
def tg_webhook():
    data = request.get_json()
    if not data: 
        return "Bad Request", 400

    # 1. 处理内联按钮回调
    if 'callback_query' in data:
        query = data['callback_query']
        chat_id = query['message']['chat']['id']
        message_id = query['message']['message_id']
        callback_data = query['data']

        # 解析: 格式如 bind|123|confirm
        parts = callback_data.split('|')
        if len(parts) == 3 and parts[0] == 'bind':
            bind_id = parts[1]
            action = parts[2]  # confirm 或 cancel

            bind_record = PendingBind.query.get(int(bind_id))
            if not bind_record:
                return "Record not found", 404

            if action == 'confirm':
                bind_record.status = 'confirmed'
                db.session.commit()
                # 修改 Telegram 消息，移除按钮
                try:
                    url = f"https://api.telegram.org/bot{bind_record.token}/editMessageText"
                    payload = {
                        "chat_id": chat_id,
                        "message_id": message_id,
                        "text": "✅ 绑定成功 访问宫水.com",
                        "reply_markup": None
                    }
                    requests.post(url, json=payload)
                except Exception as e:
                    print(f"修改消息失败(确定): {e}")

            elif action == 'cancel':
                bind_record.status = 'canceled'
                db.session.commit()
                try:
                    url = f"https://api.telegram.org/bot{bind_record.token}/editMessageText"
                    payload = {
                        "chat_id": chat_id,
                        "message_id": message_id,
                        "text": "❌ 绑定已取消",
                        "reply_markup": None
                    }
                    requests.post(url, json=payload)
                except Exception as e:
                    print(f"修改消息失败(取消): {e}")

        return "OK"

    # 2. 处理普通消息（保留你之前老的功能，这里放你之前的 handle_message 或 /start）
    if 'message' in data:
        # 这里我留空，你把之前写的 /start qr_ 逻辑复制到此处即可
        pass

    return "OK"

# ==========================================
# ✅ 新增：网页端轮询状态 API
# ==========================================
@main_bp.route('/api/bind_status/<token>', methods=['GET'])
def bind_status(token):
    record = PendingBind.query.filter_by(token=token).first()
    if not record:
        return jsonify({'status': 'not_found'})
    
    # 返回数据库中的状态以及机器人信息
    return jsonify({
        'status': record.status,
        'bot_name': record.bot_name,
        'bot_id': record.bot_id,
        'bot_username': record.bot_username
    })
