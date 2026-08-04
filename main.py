import os
import random
import smtplib
from datetime import datetime
from email.mime.text import MIMEText

from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
from werkzeug.security import generate_password_hash

# 引入数据库模型（从 models.py 导入）
from models import db, User, EmailCode, BotConfig

app = Flask(__name__)

# --- 核心配置 ---
app.config['SECRET_KEY'] = os.urandom(24).hex() # 用于 Session 加密，重要
# 读取 Railway 自动提供的 Postgres 环境变量
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///local.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db.init_app(app)

# 初始化登录管理器（可选项，为后面做后台做准备）
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --- 邮件配置 (读取你 Railway 设置的环境变量) ---
MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.qq.com')
MAIL_USERNAME = os.getenv('MAIL_USERNAME') # 你的QQ邮箱
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD') # 你的QQ邮箱SMTP授权码，不是QQ密码！

# --- 发送邮件辅助函数 ---
def send_email(to_email, code):
    if not MAIL_USERNAME or not MAIL_PASSWORD:
        raise Exception("邮箱账号或授权码未配置，请检查 Railway 环境变量")
    
    msg = MIMEText(f'您的 GsBot 验证码是：{code}，请在 5 分钟内完成验证。', 'plain', 'utf-8')
    msg['Subject'] = 'GsBot 邮箱验证码'
    msg['From'] = MAIL_USERNAME
    msg['To'] = to_email
    
    try:
        # QQ邮箱使用 SSL 465 端口
        with smtplib.SMTP_SSL(MAIL_SERVER, 465) as server:
            server.login(MAIL_USERNAME, MAIL_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"邮件发送失败: {str(e)}")
        raise e

# --- 路由：页面 ---
@app.route('/')
def splash():
    return render_template('splash.html')

@app.route('/warehouse')
def warehouse():
    return render_template('warehouse.html')

# --- 路由：API 发送验证码 ---
@app.route('/api/send_code', methods=['POST'])
def send_code():
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({'ok': False, 'msg': '邮箱不能为空'})
    
    # 生成6位随机验证码
    code = str(random.randint(100000, 999999))
    
    # 写入或更新数据库记录
    record = EmailCode.query.filter_by(email=email).first()
    if record:
        record.code = code
        record.created_at = datetime.utcnow()
    else:
        new_record = EmailCode(email=email, code=code)
        db.session.add(new_record)
    db.session.commit()
    
    # 尝试发送邮件
    try:
        send_email(email, code)
        return jsonify({'ok': True, 'msg': '验证码发送成功，请查看邮箱'})
    except Exception as e:
        return jsonify({'ok': False, 'msg': f'邮件发送失败: {str(e)}'})

# --- 路由：注册/登录（对应前端表单） ---
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
    
    # 验证验证码是否正确及是否过期 (5分钟)
    record = EmailCode.query.filter_by(email=email).order_by(EmailCode.created_at.desc()).first()
    if not record:
        return "请先获取验证码"
    
    if record.code != code:
        return "验证码错误"
    
    if (datetime.utcnow() - record.created_at).seconds > 300:
        return "验证码已过期，请重新获取"
    
    # 检查用户是否存在
    if User.query.filter_by(email=email).first():
        return "该邮箱已注册，请直接登录"
    
    # 创建新用户
    hashed_password = generate_password_hash(password)
    new_user = User(email=email, password_hash=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    
    return "注册成功"

# 用户加载器（给 LoginManager 用）
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

if __name__ == '__main__':
    # 自动在数据库中建立表结构（前提是你必须连接上 PostgreSQL）
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=8080)
