import os
import requests
from datetime import datetime
from flask import request, jsonify
from models import db, PendingBind
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

    # 1. 验证 Token 有效并获取机器人信息
    try:
        me_resp = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
        if me_resp.status_code != 200:
            return jsonify({'ok': False, 'msg': 'Token 无效或网络错误'})
        bot_info = me_resp.json().get('result', {})
        bot_name = bot_info.get('first_name') or '未命名'
        bot_id = str(bot_info.get('id')) if bot_info.get('id') else ''
        bot_username = bot_info.get('username', '')
    except Exception as e:
        return jsonify({'ok': False, 'msg': f'验证异常: {str(e)}'})

    # 2. 存入数据库绑定请求（防止重复，先删旧的）
    old_bind = PendingBind.query.filter_by(token=token).first()
    if old_bind:
        db.session.delete(old_bind)
        db.session.commit()

    new_bind = PendingBind(
        token=token,
        telegram_id=user_id_input,
        bot_name=bot_name,
        bot_id=bot_id,
        bot_username=bot_username,
        status='pending'
    )
    db.session.add(new_bind)
    db.session.commit()
    bind_id = new_bind.id

    # 3. 构造新版确认通知消息（带 HTML 加粗）
    message_text = (
        "<b>机器人绑定通知</b>\n"
        "机器人正在绑定至「宫水大世界」工作台\n"
        "若此操作非由您本人执行 请忽略本条消息\n\n"
        "请点击下方按钮 以确认绑定"
    )

    # callback_data 带上数据库 ID，长度最长 64 字节，可以用 confirm|123
    confirm_cb = f"bind|{bind_id}|confirm"
    cancel_cb = f"bind|{bind_id}|cancel"
    
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
                "parse_mode": "HTML",
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
