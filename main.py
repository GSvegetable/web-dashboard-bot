import os, requests, asyncio, threading
from flask import Flask, render_template
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

app = Flask(__name__)

# ================= 内存数据存储 =================
ACTIVE_CMDS = {}
ACTIVE_BOTS = {}

@app.route('/')
def index():
    return render_template('index.html')

def delete_webhook(token):
    try:
        url = f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true"
        requests.get(url, timeout=5)
        return True
    except Exception:
        return False

async def generic_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_token = context.bot.token
    cmd_map = ACTIVE_CMDS.get(bot_token, {})
    cmd_text = update.message.text.split()[0]
    if cmd_text in cmd_map:
        await update.message.reply_text(cmd_map[cmd_text])

def start_bot_thread(bot_app):
    def run_async():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        bot_app.run_polling(stop_signals=None)
    thread = threading.Thread(target=run_async, daemon=True)
    thread.start()

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
            delete_webhook(token)
            bot_app = Application.builder().token(token).build()
            bot_app.add_handler(MessageHandler(filters.COMMAND, generic_command_handler))
            start_bot_thread(bot_app)
            ACTIVE_BOTS[token] = bot_app
        if token not in ACTIVE_CMDS:
            ACTIVE_CMDS[token] = {}
        ACTIVE_CMDS[token][command] = response
        return {"ok": True, "desc": f"指令「{command}」绑定成功！"}
    except Exception as e:
        return {"ok": False, "desc": f"操作失败：{str(e)}"}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
