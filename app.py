import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from extensions import mail, oauth
from models import db, User, VisitLog
from routes import main_bp

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# ✅ 强制硬编码 Secret Key
app.config['SECRET_KEY'] = 'gsbot-production-secret-key-2026'

# ✅ 强制硬编码 PostgreSQL 连接地址（绝不读环境变量，绝对稳！）
# 说明：gsbot_user / zhang121100 是你之前填的数据库账号密码
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://gsbot_user:zhang121100@127.0.0.1:5432/gsbot'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ================== 邮件配置（从环境变量读取，保持原样） ==================
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.qq.com')
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

# ================== 初始化扩展 ==================
mail.init_app(app)
oauth.init_app(app)
db.init_app(app)

# ================== 强制创建所有数据库表 ==================
try:
    with app.app_context():
        db.create_all()
        app.logger.info("✅ 数据库表结构检查/创建成功！")
except Exception as e:
    try:
        db.session.rollback()
    except:
        pass
    app.logger.error(f"❌ 数据库初始化失败 (已回滚事务): {e}")

# ================== 登录管理器 ==================
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ================== 访问记录器 ==================
@app.before_request
def log_visit():
    if request.path.startswith('/static') or request.path == '/favicon.ico':
        return
    try:
        ip = request.remote_addr
        five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
        recent_visit = VisitLog.query.filter(
            VisitLog.ip_address == ip,
            VisitLog.visited_at > five_minutes_ago
        ).first()
        if not recent_visit:
            user_agent = request.user_agent.string if request.user_agent else ''
            user_id = current_user.id if current_user.is_authenticated else None
            visit = VisitLog(ip_address=ip, user_agent=user_agent, user_id=user_id)
            db.session.add(visit)
            db.session.commit()
    except Exception as e:
        app.logger.error(f"记录访问失败: {e}")

# ================== 注册路由蓝图 ==================
app.register_blueprint(main_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
