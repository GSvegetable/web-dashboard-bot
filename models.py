from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

# 全局数据库实例
db = SQLAlchemy()

# 用户表
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    telegram_id = db.Column(db.String(50), unique=True, nullable=True)
    password_hash = db.Column(db.String(512), nullable=False)
    
    # 专门存放用户的电报信息
    telegram_username = db.Column(db.String(50), nullable=True)
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    avatar_url = db.Column(db.String(255), nullable=True)
    
    is_admin = db.Column(db.Boolean, default=False)
    is_banned = db.Column(db.Boolean, default=False)
    is_vip = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    bot_configs = db.relationship('BotConfig', backref='user', lazy=True)

# 机器人配置表
class BotConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    bot_token = db.Column(db.String(255), nullable=True)
    command = db.Column(db.String(50), nullable=True)
    response = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

# 邮箱验证码表
class EmailCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    code = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# 电报验证码表（增加防重复定义保护）
class TelegramCode(db.Model):
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.String(50), nullable=False)
    code = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ✨ 扫码登录临时凭证表
class QrLoginSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(32), unique=True, nullable=False)
    telegram_id = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(20), default='pending') # pending, success, expired
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
