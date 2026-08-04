import os
import smtplib
import random
from datetime import datetime
from email.mime.text import MIMEText

from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User, EmailCode, BotConfig

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24).hex()
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///local.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --- 环境变量读取 ---
MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.qq.com')
MAIL_USERNAME = os.getenv('MAIL_USERNAME')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD') # 必须为QQ邮箱的独立授权码

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def splash():
    return render_template('splash.html')

@app.route('/warehouse')
def warehouse():
    return render_template('warehouse.html')

# --- 真正的邮件发送函数 ---
def send_email(to_email, code):
    if not MAIL_USERNAME or not MAIL_PASSWORD:
        raise ValueError("邮箱账号或授权码未在 Railway 环境变量中配置。")
    
    msg = MIMEText(f'您的 GsBot 注册验证码是：{code}，有效期为 5 分钟。', 'plain', 'utf-8')
    msg['Subject'] = 'GsBot 邮箱验证码'
    msg['From'] = MAIL_USERNAME
    msg['To'] = to_email
    
    try:
        # 使用 SSL 465 端口连接 QQ 邮箱
        with smtplib.SMTP_SSL(MAIL_SERVER, 465) as server:
            server.login(MAIL_USERNAME, MAIL_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"后端日志 - 邮件发送失败详情: {str(e)}")
        raise e

# --- 验证码发送接口 ---
@app.route('/api/send_code', methods=['POST'])
def send_code():
    data = request.get_json()
    email = data.get('email')
    if not email:
        return jsonify({'ok': False, 'msg': '邮箱不能为空'})
    
    # 生成6位真正的随机验证码
    code = str(random.randint(100000, 999999))
    
    try:
        # 写入数据库
        record = EmailCode.query.filter_by(email=email).first()
        if record:
            record.code = code
            record.created_at = datetime.utcnow()
        else:
            new_record = EmailCode(email=email, code=code)
            db.session.add(new_record)
        db.session.commit()
        
        # 发送真实邮件
        send_email(email, code)
        return jsonify({'ok': True, 'msg': '验证码已发送至您的邮箱，请查收'})
    except Exception as e:
        return jsonify({'ok': False, 'msg': f'邮件发送失败: {str(e)}'})

# --- 注册/登录处理 ---
@app.route('/register', methods=['POST'])
def register():
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    code = request.form.get('code')
    
    if not all([email, password, confirm_password, code]):
        return "表单信息填写不完整"
    if password != confirm_password:
        return "两次输入的密码不一致"
    
    # 查询验证码
    record = EmailCode.query.filter_by(email=email).order_by(EmailCode.created_at.desc()).first()
    if not record:
        return "请先获取验证码"
    
    if record.code != code:
        return "验证码错误"
    
    # 修复了之前的 TypeError：使用 datetime.utcnow() 匹配 naive 时间
    if (datetime.utcnow() - record.created_at).seconds > 300:
        return "验证码已过期，请重新获取"
    
    # 检查用户是否存在，存在则直接登录
    user = User.query.filter_by(email=email).first()
    if user:
        login_user(user)
        return "登录成功"
    
    # 不存在则新建用户并登录
    hashed_password = generate_password_hash(password)
    new_user = User(email=email, password_hash=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    
    login_user(new_user)
    return "注册成功"

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=8080)
