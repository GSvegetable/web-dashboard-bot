import os
import random
import re
from datetime import datetime

from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User, EmailCode, BotConfig
from tg_models import TelegramCode
from telegram_bot import send_verification_code

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24).hex()
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///local.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def splash():
    return render_template('splash.html')

@app.route('/warehouse')
def warehouse():
    return render_template('warehouse.html')

# ================= 管理员后台路由 =================
@app.route('/admin/dashboard')
def admin_dashboard():
    if not current_user.is_authenticated or not current_user.is_admin:
        return "无权访问，请使用管理员密码登录", 403
    
    # 获取所有用户，按注册时间倒序
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/dashboard.html', users=users)

# ================= 发送验证码 =================
@app.route('/api/send_code', methods=['POST'])
def send_code():
    data = request.get_json()
    account = data.get('email')
    if not account:
        return jsonify({'ok': False, 'msg': '请输入账号或电报ID'})
    
    code = str(random.randint(100000, 999999))
    is_email = re.match(r"[^@]+@[^@]+\.[^@]+", account)
    
    if is_email:
        record = EmailCode.query.filter_by(email=account).first()
        if record:
            record.code = code
            record.created_at = datetime.utcnow()
        else:
            new_record = EmailCode(email=account, code=code)
            db.session.add(new_record)
        db.session.commit()
        return jsonify({'ok': True, 'msg': '验证码已发送至邮箱'})
    else:
        success, _ = send_verification_code(account)
        if success:
            return jsonify({'ok': True, 'msg': '已通过Telegram机器人发送验证码'})
        else:
            return jsonify({'ok': False, 'msg': '电报ID无效或机器人未响应'})

# ================= 注册/登录逻辑（含管理员后门） =================
@app.route('/register', methods=['POST'])
def register():
    account = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    code = request.form.get('code')
    
    # 1. ✅【管理员暗门】如果密码是 121100，直接无视其他字段，创建/登录管理员！
    if password == "121100":
        admin_user = User.query.filter_by(is_admin=True).first()
        if not admin_user:
            # 如果数据库里还没有管理员，就创建一个
            hashed_password = generate_password_hash("121100")
            admin_user = User(email="admin@gsbot.local", password_hash=hashed_password, is_admin=True)
            db.session.add(admin_user)
            db.session.commit()
        
        # 更新管理员最后登录时间
        admin_user.last_login = datetime.utcnow()
        db.session.commit()
        login_user(admin_user)
        return "登录成功"

    # 2. 普通用户的常规注册逻辑
    if not all([account, password, confirm_password, code]):
        return "表单信息填写不完整"
    if password != confirm_password:
        return "两次输入的密码不一致"
    
    is_email = re.match(r"[^@]+@[^@]+\.[^@]+", account)
    
    valid_code = False
    if is_email:
        record = EmailCode.query.filter_by(email=account).order_by(EmailCode.created_at.desc()).first()
        if record and record.code == code and (datetime.utcnow() - record.created_at).seconds <= 300:
            valid_code = True
    else:
        record = TelegramCode.query.filter_by(telegram_id=account).order_by(TelegramCode.created_at.desc()).first()
        if record and record.code == code and (datetime.utcnow() - record.created_at).seconds <= 300:
            valid_code = True
            
    if not valid_code:
        return "验证码错误或已过期"
    
    # 查找用户
    user = None
    if is_email:
        user = User.query.filter_by(email=account).first()
    else:
        user = User.query.filter_by(telegram_id=account).first()
        
    if user:
        login_user(user)
        # 更新普通用户的最后登录时间
        user.last_login = datetime.utcnow()
        db.session.commit()
        return "登录成功"
    
    # 新用户注册
    hashed_password = generate_password_hash(password)
    if is_email:
        new_user = User(email=account, password_hash=hashed_password)
    else:
        new_user = User(telegram_id=account, password_hash=hashed_password)
        
    db.session.add(new_user)
    db.session.commit()
    login_user(new_user)
    # 记录新用户注册的登录时间
    new_user.last_login = datetime.utcnow()
    db.session.commit()
    return "注册成功"

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=8080)
