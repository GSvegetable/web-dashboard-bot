from flask import request, jsonify
from . import main_bp
import requests

@main_bp.route('/api/bind_bot', methods=['POST'])
def bind_bot():
    data = request.get_json()
    token, chat_id, bot_name = data.get('token'), data.get('telegram_id'), data.get('name', '宫水编辑器')
    if not token:
        return jsonify({'ok': False, 'msg': '缺少参数'})
    result = execute_bind_bot(token, chat_id, bot_name)
    return jsonify({
        'ok': result.get('ok', False),
        'msg': result.get('msg', ''),
        'bot_name': result.get('bot_name', '未命名'),
        'bot_avatar_url': result.get('avatar'),
        'bot_id': result.get('bot_id', ''),
        'bot_username': result.get('bot_username', '')
    })

def execute_bind_bot(token, chat_id, name='宫水编辑器'):
    try:
        test_resp = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
        if test_resp.status_code != 200:
            return {"ok": False, "msg": "Token 无效或网络错误"}
        getme_data = test_resp.json()
        real_bot_name = name
        bot_avatar_url = None
        bot_id = None
        bot_username = None
        if getme_data.get('ok'):
            result = getme_data.get('result', {})
            real_bot_name = result.get('first_name') or result.get('username') or name
            bot_id = str(result.get('id')) if result.get('id') else None
            bot_username = result.get('username')
            if bot_id:
                try:
                    photos_resp = requests.get(f"https://api.telegram.org/bot{token}/getUserProfilePhotos?user_id={bot_id}&limit=1", timeout=10)
                    if photos_resp.status_code == 200 and photos_resp.json().get('result', {}).get('total_count', 0) > 0:
                        file_id = photos_resp.json()['result']['photos'][0][-1]['file_id']
                        file_resp = requests.get(f"https://api.telegram.org/bot{token}/getFile?file_id={file_id}", timeout=10)
                        if file_resp.status_code == 200:
                            file_path = file_resp.json()['result']['file_path']
                            bot_avatar_url = f"https://api.telegram.org/file/bot{token}/{file_path}"
                except:
                    pass
        try:
            if chat_id:
                send_resp = requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id": chat_id, "text": f"机器人已绑定{real_bot_name}"}, timeout=10)
                if send_resp.status_code == 200:
                    return {"ok": True, "msg": "绑定成功", "bot_name": real_bot_name, "avatar": bot_avatar_url, "bot_id": bot_id, "bot_username": bot_username}
                else:
                    return {"ok": True, "msg": "信息拉取成功，但向该ID发送消息失败，请检查ID", "bot_name": real_bot_name, "avatar": bot_avatar_url, "bot_id": bot_id, "bot_username": bot_username}
            else:
                return {"ok": True, "msg": "信息拉取成功，未提供ID测试", "bot_name": real_bot_name, "avatar": bot_avatar_url, "bot_id": bot_id, "bot_username": bot_username}
        except Exception as e:
            return {"ok": True, "msg": f"信息拉取成功，发送消息异常: {str(e)}", "bot_name": real_bot_name, "avatar": bot_avatar_url, "bot_id": bot_id, "bot_username": bot_username}
    except Exception as e:
        return {"ok": False, "msg": f"执行异常: {str(e)}"}
