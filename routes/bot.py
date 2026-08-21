import os
import requests
import socket
import urllib3.util.connection as urllib3_util_connection

# 强制只走 IPv4，禁用 SSL 警告，忽略代理
urllib3_util_connection.HAS_IPV6 = False
urllib3_util_connection.allowed_gai_family = lambda: socket.AF_INET
requests.packages.urllib3.disable_warnings()

from flask import request, jsonify
from . import main_bp

SESSION = requests.Session()
SESSION.trust_env = False

@main_bp.route('/api/send_bind_request', methods=['POST'])
def send_bind_request():
    data = request.get_json()
    user_id_input = data.get('user_id', '').strip().lstrip('@')
    token = data.get('token', '').strip()

    if not user_id_input or not token:
        return jsonify({'ok': False, 'msg': 'ID 和 Token 都不能为空'})
    if not token or not token.startswith('') or ':' not in token:
        return jsonify({'ok': False, 'msg': 'Token 格式无效'})

    # 1. 验证 Token 有效
    try:
        me_resp = SESSION.get(f"https://api.telegram.org/bot{token}/getMe", timeout=15, verify=False)
        if me_resp.status_code != 200:
            return jsonify({'ok': False, 'msg': 'Token 无效或网络错误'})
    except Exception as e:
        return jsonify({'ok': False, 'msg': f'验证异常: {str(e)}'})

    # 2. 发送一条纯通知消息（最简单，只发一次）
    message_text = "✅ 绑定成功，您的机器人已连接「宫水大世界」"

    try:
        send_resp = SESSION.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={
                "chat_id": user_id_input,
                "text": message_text
            },
            timeout=15,
            verify=False
        )
        if send_resp.status_code == 200:
            return jsonify({'ok': True, 'msg': '绑定成功！'})
        else:
            error_data = send_resp.json()
            error_desc = error_data.get("description", "")
            if "chat not found" in error_desc:
                return jsonify({'ok': False, 'msg': '发送失败：机器人找不到该用户。请检查 Token 是否正确，并确保已在 Telegram 中向该机器人发送过 "/start" 命令。'})
            else:
                return jsonify({'ok': False, 'msg': f'发送失败: {error_desc}'})
    except Exception as e:
        return jsonify({'ok': False, 'msg': f'发送异常: {str(e)}'})
