import os
import random
from datetime import datetime, timezone
from email.mime.text import MIMEText

from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
from werkzeug.security import generate_password_hash

from models import db, User, EmailCode, BotConfig

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

# --- 🟢 测试版：无邮件发送，强制固定为 123456 ---
@app.route('/api/send_code', methods=['POST'])
def send_code():
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({'ok': False, 'msg': '邮箱不能为空'})
    
    # 我们固定一个测试验证码，并且将其打印在 Railway 的实时日志里
    code = "123456"
    
    record = EmailCode.query.filter_by(email=email).first()
    if record:
        record.code = code
        record.created_at = datetime.now(timezone.utc)
    else:
        new_record = EmailCode(email=email, code=code)
        db.session.add(new_record)
    db.session.commit()
    
    # 打印到 Railway 日志，等下你要去后台看这个
    print(f"\n\n============== 测试验证码已生成 ==============")
    print(f"   用户邮箱：{email}")
    print(f"   验证码是：【 {code} 】")
    print(f"============================================\n\n")
    
    return jsonify({'ok': True, 'msg': '验证码已生成（请在 Railway 实时日志查看）'})

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
    
    record = EmailCode.query.filter_by(email=email).order_by(EmailCode.created_at.desc()).first()
    if not record:
        return "请先获取验证码"
    if record.code != code:
        return "验证码错误"
    if (datetime.now(timezone.utc) - record.created_at).seconds > 300:
        return "验证码已过期，请重新获取"
    if User.query.filter_by(email=email).first():
        return "该邮箱已注册，请直接登录"
    
    hashed_password = generate_password_hash(password)
    new_user = User(email=email, password_hash=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    
    return "注册成功"

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=8080)
