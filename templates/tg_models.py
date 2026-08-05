from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from models import db # 复用 models.py 里的 db 实例

class TelegramCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.String(50), nullable=False) # 存储电报 ID
    code = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
