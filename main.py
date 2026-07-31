import os, requests
from flask import Flask, request, render_template_string

app = Flask(__name__)

# ================= 网页前端界面 (HTML + CSS + JS) =================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>宫水机器人配置器</title>
    <style>
        body { font-family: -apple-system, sans-serif; background: #0b0d15; color: #fff; padding: 20px; }
        .container { max-width: 450px; margin: 0 auto; background: #1a1c22; padding: 20px; border-radius: 12px; }
        h2 { text-align: center; margin-bottom: 20px; }
        label { display: block; margin: 15px 0 5px; font-weight: bold; }
        input, textarea { width: 100%; padding: 12px; border-radius: 8px; border: 1px solid #333; background: #0b0d15; color: #fff; box-sizing: border-box; margin-bottom: 10px; }
        button { width: 100%; padding: 14px; background: #6c5ce7; color: #fff; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; margin-top: 10px; }
        button:active { transform: scale(0.98); }
        #status { margin-top: 15px; text-align: center; font-size: 14px; padding: 10px; border-radius: 6px; }
        .success { background: #2ed573; }
        .error { background: #ff4757; }
    </style>
</head>
<body>
    <div class="container">
        <h2>🎛️ 宫水配置后台</h2>
        <label>输入你的机器人 Token</label>
        <input type="text" id="bot_token" placeholder="例如: 8506542682:AAH..." />

        <label>设置左下角紫色菜单按钮</label>
        <input type="text" id="menu_button_name" placeholder="按钮名字：打开宫水程序" />
        <button onclick="setMenuButton()">👉 立即生效：添加菜单按钮</button>

        <div id="status">等待操作...</div>
    </div>

    <script>
        async function setMenuButton() {
            const token = document.getElementById('bot_token').value.trim();
            const text = document.getElementById('menu_button_name').value.trim();
            const status = document.getElementById('status');

            if(!token) { status.innerHTML = "❌ 请先填入 Token！"; status.className = "error"; return; }
            if(!text) { status.innerHTML = "❌ 请输入菜单按钮的文字！"; status.className = "error"; return; }

            status.innerHTML = "⏳ 正在向 Telegram 发送指令...";
            status.className = "";

            try {
                // 调用后端的接口
                const res = await fetch('/api/set_menu', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ token: token, text: text })
                });
                const data = await res.json();
                
                if(data.ok) {
                    status.innerHTML = "✅ 设置成功！退出此网页，去 Telegram 看看左下角吧！";
                    status.className = "success";
                } else {
                    status.innerHTML = "❌ 设置失败：" + data.desc;
                    status.className = "error";
                }
            } catch(e) {
                status.innerHTML = "❌ 网络请求异常：" + e.message;
                status.className = "error";
            }
        }
    </script>
</body>
</html>
"""

# ================= 后端逻辑 (接收网页命令，发给 Telegram) =================
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/set_menu', methods=['POST'])
def api_set_menu():
    data = request.get_json()
    token = data.get('token')
    text = data.get('text')
    
    if not token or not text:
        return {"ok": False, "desc": "缺少 Token 或按钮名字"}

    try:
        # 调用 Telegram API 直接给用户的机器人添加左下角菜单
        url = f"https://api.telegram.org/bot{token}/setChatMenuButton"
        payload = {
            "menu_button": {
                "type": "web_app",
                "text": text,
                "web_app": {
                    "url": "https://t.me"  # 因为还没部署你的项目，暂时放个无害的链接
                }
            }
        }
        resp = requests.post(url, json=payload, timeout=10)
        return resp.json()
    except Exception as e:
        return {"ok": False, "desc": str(e)}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
