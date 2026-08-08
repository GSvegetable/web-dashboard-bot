@main_bp.route('/workspace')
def workspace():
    # ✅ 路径已经改到新建的 workspace 文件夹里了
    return render_template('workspace/workspace.html')

# ✅ 绑定 Bot 的后端 API
@main_bp.route('/api/bind_bot', methods=['POST'])
def bind_bot():
    data = request.get_json()
    token = data.get('token')
    if not token:
        return jsonify({'success': False, 'error': '未提供 Token'})

    try:
        # 1. 获取机器人真实名字
        me_url = f"https://api.telegram.org/bot{token}/getMe"
        me_resp = requests.get(me_url, timeout=10)
        if me_resp.status_code != 200:
            return jsonify({'success': False, 'error': 'Token 无效'})
        bot_info = me_resp.json()
        if not bot_info.get('ok'):
            return jsonify({'success': False, 'error': bot_info.get('description', 'Token 无效')})
        
        bot_name = bot_info['result'].get('first_name') or bot_info['result'].get('username') or '未命名机器人'

        # 2. 给机器人发送接入成功消息
        send_url = f"https://api.telegram.org/bot{token}/sendMessage"
        send_payload = {
            "chat_id": bot_info['result']['id'],
            "text": "机器人已成功接入宫水编辑器"
        }
        requests.post(send_url, json=send_payload, timeout=10)

        # 3. 返回名字给前端
        return jsonify({'success': True, 'name': bot_name})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
