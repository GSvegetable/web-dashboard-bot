import os, requests
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, BotConfig

app = Flask(__name__)

# 环境配置
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化扩展
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 用户加载器
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 在应用启动前创建所有表（保证 Railway 部署时第一次跑起来）
with app.app_context():
    db.create_all()
    # 如果没有管理员，自动创建一个管理员账号（邮箱 admin@gsbot.com，密码 admin123）
    if not User.query.filter_by(email='admin@gsbot.com').first():
        admin = User(email='admin@gsbot.com', password_hash=generate_password_hash('admin123'), is_admin=True)
        db.session.add(admin)
        db.session.commit()

# ================= 登录 / 注册 页面 =================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            if user.is_banned:
                flash('此账号已被封禁，无法登录。', 'error')
                return redirect(url_for('login'))
            login_user(user)
            return redirect(url_for('index'))
        flash('邮箱或密码错误', 'error')
    return render_template('login.html') # 需要新建登录模板

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        if password != confirm:
            flash('两次输入的密码不一致', 'error')
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash('该邮箱已被注册', 'error')
            return redirect(url_for('register'))
        new_user = User(email=email, password_hash=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()
        flash('注册成功，请登录', 'success')
        return redirect(url_for('login'))
    return render_template('register.html') # 需要新建注册模板

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
    return render_template('admin.html', users=users) # 需要新建管理员模板

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

# ================= 网页主入口 =================
@app.route('/')
@login_required
def index():
    return render_template('index.html')

# ================= 机器人配置 API（配合网站下拉卡片） =================
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
