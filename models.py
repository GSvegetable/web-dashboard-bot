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
    github_id = db.Column(db.String(50), unique=True, nullable=True)  # ✅ 新增：GitHub 唯一标识
    password_hash = db.Column(db.String(512), nullable=False)
    telegram_username = db.Column(db.String(50), nullable=True)
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    avatar_url = db.Column(db.String(255), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_banned = db.Column(db.Boolean, default=False)
    is_vip = db.Column(db.Boolean, default=False)
    vip_level = db.Column(db.Integer, default=0)      # ✅ 新增：会员等级
    stars = db.Column(db.Integer, default=0)          # ✅ 新增：星星货币余额
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # 关联关系
    bot_configs = db.relationship('BotConfig', backref='user', lazy=True)
    transactions = db.relationship('Transaction', backref='user', lazy=True)

# 机器人配置表（你的原有表，不变）
class BotConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    bot_token = db.Column(db.String(255), nullable=True)
    command = db.Column(db.String(50), nullable=True)
    response = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

# 邮箱验证码表（你的原有表，不变）
class EmailCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    code = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Telegram 验证码表（你的原有表，不变）
class TelegramCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.String(50), nullable=False)
    code = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# 扫码登录临时凭证表（你的原有表，不变）
class QrLoginSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(32), unique=True, nullable=False)
    telegram_id = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ==========================================
# ✨ 新增 1：星星流水账表（极其重要，防乱账）
# ==========================================
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)      # 变动数量（正数增加，负数消耗）
    before_balance = db.Column(db.Integer, nullable=False) # 变动前余额
    after_balance = db.Column(db.Integer, nullable=False)  # 变动后余额
    reason = db.Column(db.String(255), nullable=True)   # 变动原因（如：卡密兑换、购买高级模型）
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ==========================================
# ✨ 新增 2：卡密兑换表（用于你售卖卡密）
# ==========================================
class CardKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(32), unique=True, nullable=False) # 卡密字符串
    value = db.Column(db.Integer, nullable=False)                # 卡密面值（对应多少星星）
    is_used = db.Column(db.Boolean, default=False)               # 是否已被兑换
    used_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # 谁兑换的
    used_at = db.Column(db.DateTime, nullable=True)              # 兑换时间
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
