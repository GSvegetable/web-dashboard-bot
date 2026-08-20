from flask import render_template, redirect, url_for, abort, request, jsonify
from . import main_bp
import requests

@main_bp.route('/')
def splash():
    return render_template('splash.html')

# 旧仓库重定向到新工作台
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
# ✅ 核心修改：处理机器人按钮点击的回调事件
# ==========================================
@main_bp.route('/tg_webhook', methods=['POST'])
def tg_webhook():
    data = request.get_json()
    if not data: 
        return "Bad Request", 400

    # 1. 处理按钮点击回调 (CallbackQuery)
    if 'callback_query' in data:
        query = data['callback_query']
        chat_id = query['message']['chat']['id']
        message_id = query['message']['message_id']
        callback_data = query['data']

        # 解析判断点击的是哪个按钮，并取出之前埋下的 Token
        if callback_data.startswith('bind_confirm|'):
            token = callback_data.split('|')[1]
            try:
                # 原地修改该条消息，移除按钮，显示成功文字
                url = f"https://api.telegram.org/bot{token}/editMessageText"
                payload = {
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "text": "✅ 已绑定成功 访问宫水.com",
                    "reply_markup": None  # 清除按钮
                }
                requests.post(url, json=payload)
            except Exception as e:
                print(f"修改消息失败(确定): {e}")

        elif callback_data.startswith('bind_cancel|'):
            token = callback_data.split('|')[1]
            try:
                # 原地修改该条消息，移除按钮，显示取消文字
                url = f"https://api.telegram.org/bot{token}/editMessageText"
                payload = {
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "text": "❌ 绑定已取消",
                    "reply_markup": None  # 清除按钮
                }
                requests.post(url, json=payload)
            except Exception as e:
                print(f"修改消息失败(取消): {e}")
                
        return "OK"

    # 2. 处理普通消息 (如 /start, 扫码登录等)
    if 'message' in data:
        # 此处保留原有的微信机器人逻辑
        # 直接继承之前写的逻辑就好
        pass
        
    return "OK"
