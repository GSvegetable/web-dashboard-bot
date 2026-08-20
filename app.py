import os
import logging
from pathlib import Path
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from extensions import mail, oauth
from models import db, User, VisitLog
from routes import main_bp

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24).hex())

BASE_DIR = Path(__file__).parent.resolve()
DB_PATH = BASE_DIR / 'local.db'
db_url = os.getenv('DATABASE_URL')
if db_url:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:////{DB_PATH}'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.qq.com')
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

mail.init_app(app)
oauth.init_app(app)
db.init_app(app)

try:
    with app.app_context():
        db.create_all()
        app.logger.info("✅ 数据库表结构检查/创建成功！")
except Exception as e:
    app.logger.error(f"❌ 数据库初始化失败: {e}")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ==========================================
# ✅ 核心：全局访问记录器
# ==========================================
@app.before_request
def log_visit():
    # 排除静态资源请求和 favicon，只记录页面访问
    if request.path.startswith('/static') or request.path == '/favicon.ico':
        return
    
    try:
        ip = request.remote_addr
        user_agent = request.user_agent.string if request.user_agent else ''
        user_id = current_user.id if current_user.is_authenticated else None
        
        visit = VisitLog(ip_address=ip, user_agent=user_agent, user_id=user_id)
        db.session.add(visit)
        db.session.commit()
    except Exception as e:
        app.logger.error(f"记录访问失败: {e}")

app.register_blueprint(main_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
