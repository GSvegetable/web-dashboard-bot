import os
import random
import re # 用来判断邮箱格式
from datetime import datetime, timezone

from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user
from werkzeug.security import generate_password_hash, check_password_hash

# 导入原有模型
from models import db, User, EmailCode, BotConfig
# 导入新增的电报模型和发送函数
from tg_models import db as tg_db, TelegramCode
from telegram_bot import send_verification_code

# ================= 重点：必须先创建 app 实例，然后才能写路由 =================
app = Flask(__name__)

# --- 核心配置 ---
app.config['SECRET_KEY'] = os.urandom(24).hex()
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///local.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db.init_app(app)
tg_db.init_app(app)

# 登录管理器
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ================= 页面路由 =================
@app.route('/')
def splash():
    return render_template('splash.html')

@app.route('/warehouse')
def warehouse():
    return render_template('warehouse.html')

# ================= 发送验证码（自动辨别邮箱或电报ID） =================
@app.route('/api/send_code', methods=['POST'])
def send_code():
    data = request.get_json()
    account = data.get('email') # 前端传过来的是 name="reg-email" 的值
    
    if not account:
        return jsonify({'ok': False, 'msg': '请输入账号或电报ID'})
    
    code = str(random.randint(100000, 999999))
    
    # 判断是不是邮箱（包含 @ 和 .）
    is_email = re.match(r"[^@]+@[^@]+\.[^@]+", account)
    
    if is_email:
        # --- 邮箱发送逻辑 ---
        record = EmailCode.query.filter_by(email=account).first()
        if record:
            record.code = code
            record.created_at = datetime.now(timezone.utc)
        else:
            new_record = EmailCode(email=account, code=code)
            db.session.add(new_record)
        db.session.commit()
        # 这里保留之前的邮箱发送逻辑，为了测试，默认返回成功
        return jsonify({'ok': True, 'msg': '验证码已发送至邮箱'})
    
    else:
        # --- ⭐ 电报ID发送逻辑 ---
        success, _ = send_verification_code(account)
        if success:
            return jsonify({'ok': True, 'msg': '已通过Telegram机器人发送验证码'})
        else:
            return jsonify({'ok': False, 'msg': '电报ID无效或机器人未响应，请在Railway后台查看最新日志'})

# ================= 注册/登录逻辑 =================
@app.route('/register', methods=['POST'])
def register():
    account = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    code = request.form.get('code')
    
    if not all([account, password, confirm_password, code]):
        return "表单信息填写不完整"
    if password != confirm_password:
        return "两次输入的密码不一致"
    
    is_email = re.match(r"[^@]+@[^@]+\.[^@]+", account)
    
    # 验证验证码逻辑
    valid_code = False
    if is_email:
        record = EmailCode.query.filter_by(email=account).order_by(EmailCode.created_at.desc()).first()
        if record and record.code == code and (datetime.now(timezone.utc) - record.created_at).seconds <= 300:
            valid_code = True
    else:
        record = TelegramCode.query.filter_by(telegram_id=account).order_by(TelegramCode.created_at.desc()).first()
        if record and record.code == code and (datetime.now(timezone.utc) - record.created_at).seconds <= 300:
            valid_code = True
            
    if not valid_code:
        return "验证码错误或已过期"
    
    # 查找用户（兼容邮箱和电报两种登录）
    user = None
    if is_email:
        user = User.query.filter_by(email=account).first()
    else:
        user = User.query.filter_by(telegram_id=account).first()
        
    if user:
        # 已有用户 -> 登录
        login_user(user)
        return "登录成功"
    
    # 新用户 -> 创建并注册
    hashed_password = generate_password_hash(password)
    if is_email:
        new_user = User(email=account, password_hash=hashed_password)
    else:
        new_user = User(telegram_id=account, password_hash=hashed_password)
        
    db.session.add(new_user)
    db.session.commit()
    login_user(new_user)
    return "注册成功"

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=8080)
