import os
import requests
import io
from PIL import Image
from pyzbar.pyzbar import decode
from tg_config import BOT_TOKEN

# 机器人的 API 和你的网页域名
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
BASE_URL = os.getenv('BASE_URL', 'https://gsbot.up.railway.app')

def send_message(chat_id, text):
    """给用户发送文本消息的通用函数"""
    url = f"{TELEGRAM_API}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

def send_verification_code(telegram_id, code):
    """发送普通验证码（保留你原有的发送逻辑）"""
    url = f"{TELEGRAM_API}/sendMessage"
    text = f"🔑 你的验证码是：**{code}**"
    data = {"chat_id": telegram_id, "text": text, "parse_mode": "Markdown"}
    resp = requests.post(url, json=data)
    if resp.status_code == 200:
        return True, "发送成功"
    return False, "发送失败"

def trigger_login(token, chat_id):
    """机器人识别到二维码后，调用后端接口完成登录"""
    try:
        # 调用我们在 main.py 里写的专用接口
        url = f"{BASE_URL}/api/process_qr_token"
        requests.post(url, json={"token": token, "chat_id": chat_id}, timeout=10)
    except Exception as e:
        print(f"触发登录失败: {e}")

def handle_message(update):
    """处理来自 Telegram 的所有消息"""
    message = update.get('message')
    if not message:
        return

    chat_id = str(message['chat']['id'])
    text = message.get('text', '')
    
    # 1. 处理普通文本指令（如 /start）
    if text.startswith('/start'):
        send_message(chat_id, "👋 你好！如果想扫码登录，请直接把网页上的二维码截图发送给我，我帮你秒登。")
        return

    # 2. ✨ 核心升级：处理图片（识别并解析二维码）
    if 'photo' in message:
        # 获取分辨率最高的图片文件
        file_id = message['photo'][-1]['file_id']
        
        # 获取图片下载链接
        resp = requests.get(f"{TELEGRAM_API}/getFile?file_id={file_id}").json()
        if not resp.get('ok'):
            send_message(chat_id, "⚠️ 获取图片失败，请重新发送。")
            return
            
        file_path = resp['result']['file_path']
        download_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
        
        # 将图片下载到内存并解析
        try:
            img_data = requests.get(download_url).content
            img = Image.open(io.BytesIO(img_data))
            decoded_objs = decode(img)
            
            if decoded_objs:
                for obj in decoded_objs:
                    qr_data = obj.data.decode('utf-8')
                    # 寻找登录令牌
                    if 'qr_' in qr_data:
                        start_index = qr_data.find('qr_')
                        token = qr_data[start_index + 3:] # 截取 qr_ 后面的部分
                        
                        # 告诉用户已识别
                        send_message(chat_id, "✅ 二维码识别成功！正在为你自动登录网页...")
                        
                        # 触发电报后台处理登录
                        trigger_login(token, chat_id)
                        return
                        
                send_message(chat_id, "⚠️ 图中的二维码不符合登录格式，请发送网页上生成的二维码截图。")
            else:
                send_message(chat_id, "⚠️ 没在图里识别到二维码，请确认图片清晰并重新发送。")
        except Exception as e:
            print(f"图片解析异常: {e}")
            send_message(chat_id, "❌ 解析图片出错，请重新截图发送。")
