import os, requests
from flask import Flask, request, render_template_string
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from threading import Thread

app = Flask(__name__)

# ================= 内存数据存储 =================
ACTIVE_CMDS = {}
ACTIVE_BOTS = {}

# ================= 网页前端界面 =================
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

        <label>绑定指令</label>
        <input type="text" id="command" placeholder="例如: /gs" value="/gs" />

        <label>绑定的内容</label>
        <input type="text" id="content" placeholder="例如: 你好" value="你好" />
        
        <button onclick="setCustomCommand()">🚀 运行绑定</button>

        <div id="status">等待操作...</div>
    </div>

    <script>
        async function setCustomCommand() {
            const token = document.getElementById('bot_token').value.trim();
            const cmd = document.getElementById('command').value.trim();
            const resp = document.getElementById('content').value.trim();
            const status = document.getElementById('status');

            if(!token) { status.innerHTML = "❌ 请先填入 Token！"; status.className = "error"; return; }
            if(!cmd) { status.innerHTML = "❌ 请输入绑定指令！"; status.className = "error"; return; }
            if(!resp) { status.innerHTML = "❌ 请输入绑定的内容！"; status.className = "error"; return; }

            status.innerHTML = "⏳ 正在尝试绑定指令并启动机器人...";
            status.className = "";

            try {
                const res = await fetch('/api/set_custom_command', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ token: token, command: cmd, response: resp })
                });
                const data = await res.json();
                
                if(data.ok) {
                    status.innerHTML = "✅ " + data.desc;
                    status.className = "success";
                } else {
                    status.innerHTML = "❌ " + data.desc;
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

# ================= 后端逻辑 =================
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

async def generic_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_token = context.bot.token
    cmd_map = ACTIVE_CMDS.get(bot_token, {})
    cmd_text = update.message.text.split()[0]
    
    if cmd_text in cmd_map:
        await update.message.reply_text(cmd_map[cmd_text])

@app.route('/api/set_custom_command', methods=['POST'])
def set_custom_command():
    data = request.get_json()
    token = data.get('token')
    command = data.get('command')
    response = data.get('response')
    
    if not token or not command or not response:
        return {"ok": False, "desc": "缺少参数，请将内容全部填满。"}

    try:
        if token not in ACTIVE_BOTS:
            bot_app = Application.builder().token(token).build()
            bot_app.add_handler(MessageHandler(filters.COMMAND, generic_command_handler))
            
            thread = Thread(target=bot_app.run_polling, daemon=True)
            thread.start()
            ACTIVE_BOTS[token] = bot_app

        if token not in ACTIVE_CMDS:
            ACTIVE_CMDS[token] = {}
        ACTIVE_CMDS[token][command] = response
        
        return {"ok": True, "desc": f"指令「{command}」绑定成功！去电报给机器人发 {command} 试试吧。"}
        
    except Exception as e:
        return {"ok": False, "desc": f"操作失败：{str(e)}"}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
