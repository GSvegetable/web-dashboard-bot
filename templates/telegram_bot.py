import requests
import random
from tg_config import BOT_TOKEN
from tg_models import db, TelegramCode
from datetime import datetime

def send_verification_code(tg_id):
    # 生成6位随机验证码
    code = str(random.randint(100000, 999999))
    
    # 写入数据库
    record = TelegramCode.query.filter_by(telegram_id=tg_id).first()
    if record:
        record.code = code
        record.created_at = datetime.utcnow()
    else:
        new_record = TelegramCode(telegram_id=tg_id, code=code)
        db.session.add(new_record)
    db.session.commit()
    
    # 通过 Telegram API 发送消息
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": tg_id,
        "text": f"【GsBot验证码】您的登录验证码是：{code}\n请输入验证码完成注册/登录。"
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return True, code
        else:
            return False, None
    except Exception:
        return False, None
