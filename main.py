进口操作系统、请求、异步、线程
从……起烧瓶进口烧瓶，渲染模板(_T)
从……起电报进口更新
从……起电报。ext进口应用程序、MessageHandler、筛选器、ContextTypes

app= flask (__name__)

# ================= 内存数据存储 =================
ACTIVE_CMDS = {}
ACTIVE_BOTS = {}

# ================= 后台核心逻辑 =================
@app.route('/')
定义指数():
    # 这里会自动去读取 templates/index.html
返回渲染模板(_T)('index.html')

定义删除网钩(_W)( token ):
    尝试:
        url = f"https://api.telegram.org/bot{ token }/deleteWebhook?drop_pending_updates=true"
请求。得到(url, timeout=5)
        返回 正确
    除……之外例外：
        返回 假的

异步定义通用命令处理程序(更新：更新，上下文：ContextTypes。default_TYPE):
bot_token=上下文。网上机器人. token 
CMD_map=ACTIVE_CMDS。得到(bot_token, {})
CMD_text=更新。消息.text.split()[0]
    如果CMD_text在...内CMD映射(_M)：
        等候更新。消息.回复文本(_T)(cmd_map[ cmd_text ])

定义start_bot_thread(bot_app):
定义运行异步(_A)():
循环=异步。new_event_loop()
异步。set_event_loop(loop)
bot_app。运行轮询(_P)(stop_signals=没有一个)
thread=螺纹。线(目标=run_async，守护程序=正确)
线。开始()

@app.route('/api/set_custom_command'，方法=['POST'])
定义 set_custom_command():
数据=请求。get_json()
令牌=数据。得到('令牌')
命令=数据。得到('命令')
响应=数据。得到(“响应”)
    如果 不令牌或 不命令或 不响应：
        返回 {"确定": 假的, "描述": "缺少参数，请将内容全部填满。"}
    尝试:
        如果令牌不 在……内active_BOTS：
            删除Webhook(_W)(令牌)
bot_app=应用程序。建造者().令牌(令牌).建立()
bot_app。add_handler(MessageHandler(过滤器。命令，通用命令处理程序))
            start_bot_thread(bot_app)
            ACTIVE_BOTS[令牌]=bot_app
        如果令牌不 在……内active_CMDS：
active_CMDS[令牌]={}
active_CMDS[令牌][命令]=响应
        返回 {"确定": 正确, "描述": F"指令"{命令}」绑定成功！"}
    除……之外例外作为e：
        返回 {"确定": 假的, "描述": F"操作失败：{str(e)}"}

如果__名称__=='__main__'：
应用程序。跑(主办='0.0.0.0'，端口=8080)
