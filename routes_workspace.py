from flask import Blueprint, request, jsonify
import requests

# 定义一个属于工作台模块的蓝图
workspace_bp = Blueprint('workspace', __name__)

# ✅ 把刚才新增的接口移到这里
@workspace_bp.route('/api/bind_bot', methods=['POST'])
def bind_bot():
    data = request.get_json()
    token = data.get('token')
    name = data.get('name')
    tg_id = data.get('telegram_id')

    if not token:
        return jsonify({'ok': False, 'msg': '请输入 Bot Token'})
    if not tg_id:
        return jsonify({'ok': False, 'msg': '请输入你的 Telegram 账号 ID，用于接收通知'})
        
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": tg_id, "text": "机器人已连接宫水编辑器"}
        resp = requests.post(url, json=payload, timeout=10)
        
        if resp.status_code == 200:
            return jsonify({'ok': True, 'msg': '绑定成功，已主动向 Telegram 发送消息！'})
        else:
            return jsonify({'ok': False, 'msg': 'Bot Token 或 ID 无效，发送失败。'})
    except Exception as e:
        return jsonify({'ok': False, 'msg': f'请求异常: {str(e)}'})
