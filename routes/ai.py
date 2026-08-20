import os
import requests
from flask import request, jsonify
from . import main_bp

DS_API_BASE = "https://xh.v1api.cc/v1/chat/completions"

@main_bp.route('/api/agent/chat', methods=['POST'])
def agent_chat():
    data = request.get_json()
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({'reply': '请先输入消息。'})

    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
    if not DEEPSEEK_API_KEY:
        return jsonify({'reply': '未配置 DeepSeek API Key。'})

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }
    
    # 最普通的对话格式，没有 system 提示词，没有流式，没有记忆
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": user_message}
        ],
        "stream": False
    }

    try:
        resp = requests.post(DS_API_BASE, headers=headers, json=payload, timeout=60)
        if resp.status_code != 200:
            return jsonify({'reply': f'请求失败，状态码: {resp.status_code}'})
        
        result = resp.json()
        # 提取普通回复
        reply = result['choices'][0]['message']['content']
        return jsonify({'reply': reply})
        
    except Exception as e:
        print(f"AI 请求异常: {e}")
        return jsonify({'reply': '请求异常，请稍后重试。'})
