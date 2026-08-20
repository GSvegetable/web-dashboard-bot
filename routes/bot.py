import os
import requests
from datetime import datetime
from flask import request, jsonify
from . import main_bp

@main_bp.route('/api/send_bind_request', methods=['POST'])
def send_bind_request():
    data = request.get_json()
    user_id_input = data.get('user_id', '').strip()
    token = data.get('token', '').strip()

    if not user_id_input or not token:
        return jsonify({'ok': False, 'msg': '用户名和 Token 都不能为空'})
    if not token or not token.startswith('') or ':' not in token:
        return jsonify({'ok': False, 'msg': 'Token 格式无效'})

    # 1. 验证 Token 有效
    try:
        me_resp = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
        if me_resp.status_code != 200:
            return jsonify({'ok': False, 'msg': 'Token 无效或网络错误'})
    except Exception as e:
        return jsonify({'ok': False, 'msg': f'验证异常: {str(e)}'})

    # 2. 构造一条纯通知消息（不再带按钮）
    message_text = (
        f"🔔 机器人绑定通知\n"
        f"你的机器人已被成功绑定到「宫水大世界」工作台。\n"
        f"如果这不是你本人的操作，请立即前往 @BotFather 使用 /revoke 命令重置此 Token。"
    )

    try:
        # ✅ 核心：直接向用户填写的 Telegram 用户名发消息（支持带 @ 或不带）
        send_resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={
                "chat_id": user_id_input,
                "text": message_text
            },
            timeout=15
        )
        if send_resp.status_code == 200:
            return jsonify({'ok': True, 'msg': '通知消息已成功发送'})
        else:
            error_data = send_resp.json()
            return jsonify({'ok': False, 'msg': f'发送失败: {error_data.get("description", "未知错误")}'})
    except Exception as e:
        return jsonify({'ok': False, 'msg': f'发送异常: {str(e)}'})
