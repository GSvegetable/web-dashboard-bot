import os, requests, smtplib, random, socket
from email.mime.text import MIMEText
from email.header import Header
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, BotConfig, EmailCode
from datetime import datetime, timedelta

app = Flask(__name__)

# 环境配置
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['MAIL_SERVER'] = 'smtp.qq.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = '3301296046@qq.com'
app.config['MAIL_DEFAULT_SENDER'] = '3301296046@qq.com'
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

# 初始化扩展
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 自动建表
with app.app_context():
    db.create_all()
    if not User.query.filter_by(email='admin@gsbot.com').first():
        admin = User(email='admin@gsbot.com', password_hash=generate_password_hash('admin123'), is_admin=True)
        db.session.add(admin)
        db.session.commit()

# ================= 发邮件工具函数 =================
def send_email_code(to_email):
    code = str(random.randint(100000, 999999))
    db.session.add(EmailCode(email=to_email, code=code))
    db.session.commit()
    
    msg = MIMEText(f'您的验证码是：{code}，请勿泄露给他人。', 'plain', 'utf-8')
    msg['Subject'] = Header('gsbot 验证码', 'utf-8')
    msg['From'] = app.config['MAIL_DEFAULT_SENDER']
    msg['To'] = to_email
    
    server = None
    try:
        socket.setdefaulttimeout(10)
        server = smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT'], timeout=10)
        server.starttls()
        server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        server.sendmail(app.config['MAIL_DEFAULT_SENDER'], [to_email], msg.as_string())
        return True
    except Exception as e:
        print(f"❗ 发送邮件失败具体原因: {e}")
        return False
    finally:
        if server:
            try: server.quit()
            except: pass

# ================= 人机验证 =================
def verify_turnstile(token):
    secret = os.getenv('CF_TURNSTILE_SECRET_KEY')
    if not secret: return True
    try:
        resp = requests.post('https://challenges.cloudflare.com/turnstile/v0/siteverify', 
                             data={'secret': secret, 'response': token}, timeout=5)
        return resp.json().get('success', False)
    except Exception:
        return False

# ================= 路由与逻辑 =================

# 🚀【打开首页，直接展示纯图启动页】
@app.route('/')
def splash():
    return render_template('splash.html')

# 注册
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        code = request.form.get('code')
        turnstile_token = request.form.get('cf-turnstile-response')
        
        if not verify_turnstile(turnstile_token):
            flash('人机验证失败，请重试！', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('邮箱已被注册', 'error')
            return redirect(url_for('register'))
        
        record = EmailCode.query.filter_by(email=email, code=code).order_by(EmailCode.created_at.desc()).first()
        if not record or (datetime.utcnow() - record.created_at) > timedelta(minutes=5):
            flash('验证码错误或已过期', 'error')
            return redirect(url_for('register'))
            
        new_user = User(email=email, password_hash=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()
        flash('注册成功，请登录', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# 发送邮件验证码接口
@app.route('/api/send_code', methods=['POST'])
def api_send_code():
    email = request.json.get('email')
    if not email: return jsonify({'ok': False, 'msg': '邮箱不能为空'})
    if send_email_code(email):
        return jsonify({'ok': True, 'msg': '验证码已发送到您的邮箱'})
    return jsonify({'ok': False, 'msg': '连接邮箱服务器超时或失败，请稍后重试！'})

# 登录
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_type = request.form.get('login_type')
        email = request.form.get('email')
        turnstile_token = request.form.get('cf-turnstile-response')
        
        if not verify_turnstile(turnstile_token):
            flash('人机验证失败！', 'error')
            return redirect(url_for('login'))
            
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('该邮箱不存在', 'error')
            return redirect(url_for('login'))
            
        if login_type == 'password':
            password = request.form.get('password')
            if check_password_hash(user.password_hash, password):
                login_user(user)
                return redirect(url_for('index'))
            flash('密码错误', 'error')
            
        elif login_type == 'code':
            code = request.form.get('code')
            record = EmailCode.query.filter_by(email=email, code=code).order_by(EmailCode.created_at.desc()).first()
            if record and (datetime.utcnow() - record.created_at) <= timedelta(minutes=5):
                login_user(user)
                return redirect(url_for('index'))
            flash('验证码错误或已过期', 'error')
            
    return render_template('login.html')

# 游客登录
@app.route('/guest_login')
def guest_login():
    guest_id = random.randint(100000, 999999)
    guest_email = f"guest_{guest_id}@gsbot.local"
    user = User.query.filter_by(email=guest_email).first()
    if not user:
        user = User(email=guest_email, password_hash=generate_password_hash('guest'))
        db.session.add(user)
        db.session.commit()
    login_user(user)
    return redirect(url_for('index'))

# 登出
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ================= 管理员后台 =================
@app.route('/admin')
@login_required
def admin_panel():
    if not current_user.is_admin:
        flash('您没有访问权限', 'error')
        return redirect(url_for('index'))
    users = User.query.all()
    return render_template('admin.html', users=users)

@app.route('/admin/toggle_ban/<int:user_id>', methods=['POST'])
@login_required
def toggle_ban(user_id):
    if not current_user.is_admin: return jsonify({'error': '无权操作'}), 403
    user = User.query.get(user_id)
    if user:
        user.is_banned = not user.is_banned
        db.session.commit()
        return jsonify({'success': True, 'banned': user.is_banned})
    return jsonify({'error': '用户不存在'}), 404

@app.route('/admin/toggle_vip/<int:user_id>', methods=['POST'])
@login_required
def toggle_vip(user_id):
    if not current_user.is_admin: return jsonify({'error': '无权操作'}), 403
    user = User.query.get(user_id)
    if user:
        user.is_vip = not user.is_vip
        db.session.commit()
        return jsonify({'success': True, 'vip': user.is_vip})
    return jsonify({'error': '用户不存在'}), 404

@app.route('/admin/clear_all_data', methods=['POST'])
@login_required
def admin_clear_all_data():
    if not current_user.is_admin: return jsonify({'ok': False, 'msg': '无权限'})
    try:
        db.drop_all()
        db.create_all()
        admin = User(email='admin@gsbot.com', password_hash=generate_password_hash('admin123'), is_admin=True)
        db.session.add(admin)
        db.session.commit()
        return jsonify({'ok': True, 'msg': '已清空所有用户与数据，并重建了管理员账号！'})
    except Exception as e:
        return jsonify({'ok': False, 'msg': str(e)})

# ================= 内部核心工作台 =================
@app.route('/dashboard')
@login_required
def index():
    return render_template('index.html')

# 机器人配置 API
@app.route('/api/set_custom_command', methods=['POST'])
@login_required
def set_custom_command():
    data = request.get_json()
    token = data.get('bot_token')
    command = data.get('command')
    response = data.get('response')
    if not token:
        return {"ok": False, "desc": "缺少 API"}

    try:
        config = BotConfig.query.filter_by(user_id=current_user.id).first()
        if not config:
            config = BotConfig(user_id=current_user.id)
            db.session.add(config)
        config.bot_token = token
        config.command = command
        config.response = response
        db.session.commit()
        return {"ok": True, "desc": "机器人配置保存成功"}
    except Exception as e:
        return {"ok": False, "desc": f"保存失败: {str(e)}"}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
