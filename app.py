import os
from pathlib import Path
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
# 从此处引入单独剥离出来的 mail 和 oauth
from extensions import mail, oauth
from models import db, User
from routes import main_bp

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24).hex())

# ✅ 核心修复：自动定位到项目根目录，使用绝对路径创建 SQLite 数据库文件
BASE_DIR = Path(__file__).parent.resolve()       # 获取 /www/wwwroot/gsbot
DB_PATH = BASE_DIR / 'local.db'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', f'sqlite:///{DB_PATH}')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ================== 邮件配置 ==================
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
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

app.register_blueprint(main_bp)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=8080)
