import os
import requests
import socket
import urllib3.util.connection as urllib3_util_connection

# 强制 IPv4，忽略代理
urllib3_util_connection.HAS_IPV6 = False
urllib3_util_connection.allowed_gai_family = lambda: socket.AF_INET
requests.packages.urllib3.disable_warnings()

from flask import request, jsonify
from flask_login import current_user
from models import db, MyBot
from . import main_bp

SESSION = requests.Session()
SESSION.trust_env = False

@main_bp.route('/api/send_bind_request', methods=['POST'])
def send_bind_request():
    data = request.get_json()
    user_id_input = data.get('user_id', '').strip().lstrip('@')
    token = data.get('token', '').strip()

    if not current_user.is_authenticated:
        return jsonify({'ok': False, 'msg': '请先登录'}), 401
    if not user_id_input or not token:
        return jsonify({'ok': False, 'msg': 'ID 和 Token 都不能为空'})
    if not token or ':' not in token:
        return jsonify({'ok': False, 'msg': 'Token 格式无效'})

    # 1. 验证 Token 并获取信息
    try:
        me_resp = SESSION.get(f"https://api.telegram.org/bot{token}/getMe", timeout=15, verify=False)
        if me_resp.status_code != 200:
            return jsonify({'ok': False, 'msg': 'Token 无效或网络错误'})
        bot_info = me_resp.json().get('result', {})
        bot_name = bot_info.get('first_name') or '未命名'
        bot_id = str(bot_info.get('id')) if bot_info.get('id') else ''
        bot_username = bot_info.get('username', '')
    except Exception as e:
        return jsonify({'ok': False, 'msg': f'验证异常: {str(e)}'})

    # 2. 发送绑定成功消息
    message_text = "✅ 绑定成功，您的机器人已连接「宫水大世界」"
    try:
        send_resp = SESSION.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": user_id_input, "text": message_text},
            timeout=15, verify=False
        )
        if send_resp.status_code != 200:
            error_data = send_resp.json()
            error_desc = error_data.get("description", "")
            if "chat not found" in error_desc:
                return jsonify({'ok': False, 'msg': '发送失败：请先在 Telegram 中向该机器人发送 "/start" 命令'})
            else:
                return jsonify({'ok': False, 'msg': f'发送失败: {error_desc}'})
    except Exception as e:
        return jsonify({'ok': False, 'msg': f'发送异常: {str(e)}'})

    # 3. 存入数据库（防止重复，先删除旧的）
    old_bot = MyBot.query.filter_by(token=token).first()
    if old_bot:
        db.session.delete(old_bot)
    
    new_bot = MyBot(
        user_id=current_user.id,
        token=token,
        bot_name=bot_name,
        bot_id=bot_id,
        bot_username=bot_username
    )
    db.session.add(new_bot)
    db.session.commit()

    return jsonify({'ok': True, 'msg': '绑定成功！'})
