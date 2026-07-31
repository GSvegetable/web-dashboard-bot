import os
from flask import Flask
from telegram.ext import Application, CommandHandler, ContextTypes
from threading import Thread

TOKEN = os.getenv("BOT_TOKEN")

# 1. 网页部分 (定义你网页后台的样子)
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "<h1>欢迎来到宫水网页后台</h1><p>全屏添加到桌面，就和 APP 一样</p>"

# 2. 机器人部分
async def start(update, context):
    await update.message.reply_text("机器人已启动，网页也在运行！")

# 3. 同时启动网页和机器人的逻辑
def main():
    # 启动网页
    Thread(target=lambda: app_web.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)).start()
    # 启动机器人
    bot_app = Application.builder().token(TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    print("网页和机器人均已启动...")
    bot_app.run_polling()

if __name__ == '__main__':
    main()
