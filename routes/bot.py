import os
import requests
from datetime import datetime
from flask import request, jsonify
from . import main_bp

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
        me_resp = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
        if me_resp.status_code != 200:
            return jsonify({'ok': False, 'msg': 'Token 无效或网络错误'})
    except Exception as e:
        return jsonify({'ok': False, 'msg': f'验证异常: {str(e)}'})

    # 2. 构造新版确认通知消息
    message_text = (
        "🔔 机器人绑定通知\n"
        "您的机器人已成功绑定至「宫水大世界」工作台\n"
        "若此操作非由您本人执行 请忽略本条消息\n\n"
        "请点击下方按钮 以确认绑定状态"
    )

    # ✅ 核心：在按钮的 callback_data 中带上 Token，方便后续修改该消息
    confirm_cb = f"bind_confirm|{token}"
    cancel_cb = f"bind_cancel|{token}"
    
    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "✅ 确定", "callback_data": confirm_cb},
                {"text": "❌ 取消", "callback_data": cancel_cb}
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
            return jsonify({'ok': True, 'msg': '确认通知已发送，请去 Telegram 操作！'})
        else:
            error_data = send_resp.json()
            error_desc = error_data.get("description", "")
            if "chat not found" in error_desc:
                return jsonify({'ok': False, 'msg': '发送失败：机器人找不到该用户。请检查 Token 是否正确，并确保已在 Telegram 中向该机器人发送过 "/start" 命令。'})
            else:
                return jsonify({'ok': False, 'msg': f'发送失败: {error_desc}'})
    except Exception as e:
        return jsonify({'ok': False, 'msg': f'发送异常: {str(e)}'})
