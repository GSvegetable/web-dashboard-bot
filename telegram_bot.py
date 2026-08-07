import os
import requests
import io
from PIL import Image
from pyzbar.pyzbar import decode
from tg_config import BOT_TOKEN

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
BASE_URL = os.getenv('BASE_URL', 'https://gsbot.up.railway.app')

def send_message(chat_id, text):
    url = f"{TELEGRAM_API}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

def send_verification_code(telegram_id, code):
    url = f"{TELEGRAM_API}/sendMessage"
    text = f"验证码：{code}"
    data = {"chat_id": telegram_id, "text": text}
    resp = requests.post(url, json=data)
    if resp.status_code == 200:
        return True, "发送成功"
    return False, "发送失败"

def trigger_login(token, chat_id):
    """识别到二维码后，调用后端接口，并判断是否过期"""
    try:
        url = f"{BASE_URL}/api/process_qr_token"
        resp = requests.post(url, json={"token": token, "chat_id": chat_id}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('ok'):
                return True
        return False
    except Exception as e:
        print(f"触发登录失败: {e}")
        return False

def handle_message(update):
    message = update.get('message')
    if not message:
        return

    chat_id = str(message['chat']['id'])
    text = message.get('text', '')
    
    # 1. 处理文本
    if text.startswith('/start'):
        send_message(chat_id, "你好，扫码登录请直接发送二维码截图给我。")
        return

    # 2. 处理图片
    if 'photo' in message:
        file_id = message['photo'][-1]['file_id']
        resp = requests.get(f"{TELEGRAM_API}/getFile?file_id={file_id}").json()
        if not resp.get('ok'):
            send_message(chat_id, "获取图片失败，请重新发送。")
            return
            
        file_path = resp['result']['file_path']
        download_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
        
        try:
            img_data = requests.get(download_url).content
            img = Image.open(io.BytesIO(img_data))
            decoded_objs = decode(img)
            
            if decoded_objs:
                for obj in decoded_objs:
                    qr_data = obj.data.decode('utf-8')
                    if 'qr_' in qr_data:
                        start_index = qr_data.find('qr_')
                        token = qr_data[start_index + 3:]
                        
                        # 核心修复：判断过期状态，再决定返回文字
                        is_valid = trigger_login(token, chat_id)
                        if is_valid:
                            send_message(chat_id, "登录成功")
                            return
                        else:
                            send_message(chat_id, "二维码已过期，请刷新")
                            return
                        
                send_message(chat_id, "二维码格式不正确，请发送网页上生成的登录码截图。")
            else:
                send_message(chat_id, "未识别到二维码，请确认图片清晰并重试。")
        except Exception as e:
            print(f"图片解析异常: {e}")
            send_message(chat_id, "解析图片出错，请重新截图发送。")
