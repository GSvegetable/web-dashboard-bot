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
        return jsonify({'ok': False, 'msg': 'ID 和 Token 都不能为空'})
    if not token or not token.startswith('') or ':' not in token:
        return jsonify({'ok': False, 'msg': 'Token 格式无效'})

    # 1. 验证 Token 有效并获取机器人信息
    try:
        me_resp = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
        if me_resp.status_code != 200:
            return jsonify({'ok': False, 'msg': 'Token 无效或网络错误'})
    except Exception as e:
        return jsonify({'ok': False, 'msg': f'验证异常: {str(e)}'})

    # 2. 构造带时间和内联按钮的消息
    now = datetime.now().strftime('%Y年%m月%d日 %H:%M')
    message_text = (
        f"有人想使用宫水.com来编辑你的机器人\n"
        f"{now}\n"
        f"操作人ID {user_id_input}"
    )

    # 构造内联键盘按钮（允许 / 拒绝）
    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "✅ 允许", "callback_data": "allow_bind"},
                {"text": "❌ 拒绝", "callback_data": "deny_bind"}
            ]
        ]
    }

    try:
        send_resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={
                "chat_id": user_id_input,
                "text": message_text,
                "reply_markup": reply_markup
            },
            timeout=15
        )
        if send_resp.status_code == 200:
            return jsonify({'ok': True, 'msg': '授权请求已发送'})
        else:
            error_data = send_resp.json()
            return jsonify({'ok': False, 'msg': f'发送失败: {error_data.get("description", "未知错误")}'})
    except Exception as e:
        return jsonify({'ok': False, 'msg': f'发送异常: {str(e)}'})
