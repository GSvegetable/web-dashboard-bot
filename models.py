from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# 用户表
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_banned = db.Column(db.Boolean, default=False)
    is_vip = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    bot_configs = db.relationship('BotConfig', backref='user', lazy=True)

# 机器人配置表
class BotConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    bot_token = db.Column(db.String(255), nullable=True)
    command = db.Column(db.String(50), nullable=True)
    response = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

# 邮箱验证码表（用于注册验证）
class EmailCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    code = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
