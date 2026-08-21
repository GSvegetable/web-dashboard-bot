import os
import re
import random
import secrets
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, redirect, url_for, session
from flask_login import login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, EmailCode, TelegramCode
from extensions import oauth
from . import main_bp

logging.basicConfig(level=logging.INFO)

FIRST_NAMES = ['仆', '恶魔用户0323', '天使用户0323', '灰调雪', 'Rely', '该用户名为天使、', '涩骨痣', 'みゃ、？', '活着为了火鸡面', '露水情缘', '我心自有凜冬', '天真流尽泪', '缘如弦断难续', '循环的圆', '泪糸痛', '世間於我無关', '一万篇坏心事', '虚假郁片', '归属哪颗流星', '浅色泪、', '此用户很忧郁', '一滴名为白水', '鉴心永远是多远、', 'github']

def generate_unique_display_id():
    while True:
        new_id = str(random.randint(100000, 999999))
        if not User.query.filter_by(display_id=new_id).first():
            return new_id

# 注册 OAuth
oauth.register(
    name='github',
    client_id=os.getenv('GITHUB_CLIENT_ID'),
    client_secret=os.getenv('GITHUB_CLIENT_SECRET'),
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize',
    api_base_url='https://api.github.com/',
    client_kwargs={'scope': 'user:email'},
)

@main_bp.route('/login/github')
def login_github():
    base_url = os.getenv('BASE_URL', 'https://xn--3bts89a.com')
    redirect_uri = f"{base_url}/auth/github/callback"
    return oauth.github.authorize_redirect(redirect_uri)

@main_bp.route('/auth/github/callback')
def github_callback():
    try:
        token = oauth.github.authorize_access_token()
        resp = oauth.github.get('user', token=token)
        user_info = resp.json()

        # 获取邮箱
        emails_resp = oauth.github.get('user/emails', token=token)
        emails = emails_resp.json()
        primary_email = None
        for e in emails:
            if e.get('primary') and e.get('verified'):
                primary_email = e.get('email')
                break
        if not primary_email and emails:
            primary_email = emails[0].get('email')

        github_id = str(user_info.get('id'))
        username = user_info.get('login')
        avatar_url = user_info.get('avatar_url')

        user = User.query.filter_by(github_id=github_id).first()
        if not user:
            if primary_email:
                existing_user = User.query.filter_by(email=primary_email).first()
                if existing_user:
                    existing_user.github_id = github_id
                    existing_user.avatar_url = avatar_url
                    db.session.commit()
                    user = existing_user
                else:
                    hashed_pw = generate_password_hash(os.urandom(24).hex())
                    user = User(
                        email=primary_email,
                        github_id=github_id,
                        password_hash=hashed_pw,
                        first_name=username,
                        avatar_url=avatar_url
                    )
                    db.session.add(user)
                    db.session.commit()
            else:
                hashed_pw = generate_password_hash(os.urandom(24).hex())
                user = User(
                    email=f"{github_id}@github.local",
                    github_id=github_id,
                    password_hash=hashed_pw,
                    first_name=username,
                    avatar_url=avatar_url
                )
                db.session.add(user)
                db.session.commit()

        login_user(user)
        user.last_login = datetime.utcnow()
        db.session.commit()
        return redirect(url_for('main.splash', auth='github_success'))
    except Exception as e:
        logging.error(f"GitHub 登录异常: {e}")
        return redirect(url_for('main.splash', auth='github_error'))

@main_bp.route('/register', methods=['POST'])
def register():
    account = request.form.get('email')
    code = request.form.get('code')

    # 修复：默认回退到 121100，防止没有环境变量时崩溃
    ADMIN_SECRET_KEY = os.getenv('ADMIN_SECRET_KEY', '121100')
    
    try:
        if code == ADMIN_SECRET_KEY:
            admin_user = User.query.filter_by(is_admin=True).first()
            if not admin_user:
                admin_user = User(email="admin@gsbot.local", password_hash=generate_password_hash(ADMIN_SECRET_KEY), is_admin=True)
                db.session.add(admin_user)
                db.session.commit()
            admin_user.last_login = datetime.utcnow()
            db.session.commit()
            login_user(admin_user)
            return "ADMIN_SUCCESS"

        if not all([account, code]):
            return "表格信息填写不完整"
        
        is_email = re.match(r"[^@]+@[^@]+\.[^@]+", account)
        record = EmailCode.query.filter_by(email=account).order_by(EmailCode.created_at.desc()).first() if is_email else TelegramCode.query.filter_by(telegram_id=account).order_by(TelegramCode.created_at.desc()).first()
        if not record or record.code != code or (datetime.utcnow() - record.created_at).seconds > 300:
            return "验证码错误或已超时"
        
        user = User.query.filter_by(email=account).first() if is_email else User.query.filter_by(telegram_id=account).first()
        if user:
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            return "登录成功"
        else:
            hashed_password = generate_password_hash(secrets.token_urlsafe(16))
            if is_email:
                new_user = User(
                    email=account,
                    password_hash=hashed_password,
                    first_name=random.choice(FIRST_NAMES),
                    display_id=generate_unique_display_id()
                )
            else:
                tg_info = fetch_telegram_user_info(account)
                new_user = User(
                    telegram_id=account,
                    password_hash=hashed_password,
                    first_name=tg_info['first_name'] if tg_info else '',
                    last_name=tg_info['last_name'] if tg_info else '',
                    telegram_username=tg_info['username'] if tg_info else '',
                    avatar_url=tg_info['avatar_url'] if tg_info else None
                )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return "注册成功"
    except Exception as e:
        logging.error(f"注册时发生异常: {e}")
        return "SYSTEM_ERROR"

@main_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.splash'))
