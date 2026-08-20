import os
import random
import re
import requests
import uuid
from datetime import datetime, date, timedelta
import io
import base64
import json
import secrets

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session, Response, stream_with_context
from flask_login import login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Message

import qrcode
from PIL import Image, ImageDraw, ImageFont

from models import db, User, EmailCode, QrLoginSession, TelegramCode, Transaction, CardKey, VisitLog, Post, Comment, Like, Subscription
from telegram_bot import send_verification_code, handle_message
from tg_config import BOT_TOKEN
from agent_prompts import DEFAULT_PROMPT, SANDBOX_PROMPT, AGENT_PROMPT, SUMMARY_PROMPT
from agent_tools import TOOLS, read_webpage, web_search

from extensions import mail, oauth

main_bp = Blueprint('main', __name__)

DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')

FIRST_NAMES = [
    '仆', '恶魔用户0323', '天使用户0323', '灰调雪', 'Rely', 
    '该用户名为天使、', '涩骨痣', 'みゃ、？', '活着为了火鸡面', '露水情缘', 
    '我心自有凜冬', '天真流尽泪', '缘如弦断难续', '循环的圆', '泪糸痛', 
    '世間於我無关', '一万篇坏心事', '虚假郁片', '归属哪颗流星', '浅色泪、', 
    '此用户很忧郁', '一滴名为白水', '鉴心永远是多远、', 'github'
]

def generate_unique_display_id():
    while True:
        new_id = str(random.randint(100000, 999999))
        if not User.query.filter_by(display_id=new_id).first():
            return new_id

@main_bp.route('/settings')
def settings():
    return render_template('settings.html')

# ==========================================
# GitHub OAuth 登录
# ==========================================
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
                existing_email_user = User.query.filter_by(email=primary_email).first()
                if existing_email_user:
                    existing_email_user.github_id = github_id
                    existing_email_user.avatar_url = avatar_url
                    db.session.commit()
                    user = existing_email_user
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
        print(f"GitHub 登录失败: {e}")
        return redirect(url_for('main.splash'))

# ==========================================
# 基础路由
# ==========================================
@main_bp.route('/')
def splash():
    return render_template('splash.html')

@main_bp.route('/warehouse')
def warehouse():
    return render_template('warehouse.html')

@main_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.splash'))

@main_bp.route('/admin/dashboard')
def admin_dashboard():
    if not current_user.is_authenticated or not current_user.is_admin:
        return "无权访问，请使用管理员密码登录", 403
    
    today = date.today()
    
    total_visits = VisitLog.query.count()
    today_visits = VisitLog.query.filter(func.date(VisitLog.visited_at) == today).count()
    total_uv = VisitLog.query.distinct(VisitLog.ip_address).count()
    today_uv = VisitLog.query.filter(func.date(VisitLog.visited_at) == today).distinct(VisitLog.ip_address).count()
    total_users = User.query.count()
    today_registered = User.query.filter(func.date(User.created_at) == today).count()
    recent_active_users = User.query.filter(User.last_login != None).order_by(User.last_login.desc()).limit(8).all()
    users = User.query.order_by(User.created_at.desc()).all()
    
    all_posts = Post.query.order_by(Post.created_at.desc()).all()
    
    return render_template('admin/dashboard.html', 
                           users=users,
                           total_visits=total_visits,
                           today_visits=today_visits,
                           total_uv=total_uv,
                           today_uv=today_uv,
                           total_users=total_users,
                           today_registered=today_registered,
                           recent_active_users=recent_active_users,
                           all_posts=all_posts)

@main_bp.route('/api/admin/add_stars', methods=['POST'])
def admin_add_stars():
    if not current_user.is_authenticated or not current_user.is_admin:
        return jsonify({'ok': False, 'msg': '权限不足'}), 403
    data = request.get_json()
    user_id = data.get('user_id')
    amount = data.get('amount')
    if not user_id or amount is None: return jsonify({'ok': False, 'msg': '参数缺失'})
    try:
        amount = int(amount)
        if amount <= 0: return jsonify({'ok': False, 'msg': '赠送数量必须大于 0'})
    except: return jsonify({'ok': False, 'msg': '数量格式错误'})
    user = User.query.get(int(user_id))
    if not user: return jsonify({'ok': False, 'msg': '用户不存在'})
    before_balance = user.stars
    user.stars += amount
    db.session.commit()
    tx = Transaction(user_id=user.id, amount=amount, before_balance=before_balance, after_balance=user.stars, reason="管理员后台赠送")
    db.session.add(tx)
    db.session.commit()
    return jsonify({'ok': True, 'new_balance': user.stars})

@main_bp.route('/api/admin/hide_post', methods=['POST'])
def admin_hide_post():
    if not current_user.is_authenticated or not current_user.is_admin:
        return jsonify({'ok': False, 'msg': '权限不足'}), 403
    data = request.get_json()
    post_id = data.get('post_id')
    if not post_id: return jsonify({'ok': False, 'msg': '参数缺失'})
    post = Post.query.get(int(post_id))
    if not post: return jsonify({'ok': False, 'msg': '帖子不存在'})
    post.is_hidden = True
    db.session.commit()
    return jsonify({'ok': True, 'msg': '已隐藏该帖子'})

@main_bp.route('/workspace')
def workspace():
    return render_template('workspace/workspace.html')

@main_bp.route('/community')
def community():
    return render_template('community.html')

# ==========================================
# ✅ 社区动态 API 接口
# ==========================================

# 1. 获取帖子列表（支持关键词和时段搜索）
@main_bp.route('/api/posts', methods=['GET'])
def get_posts():
    keyword = request.args.get('keyword', '').strip()
    time_filter = request.args.get('time', 'all')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    query = Post.query.filter_by(is_hidden=False).order_by(Post.created_at.desc())
    
    if keyword:
        query = query.filter(Post.content.contains(keyword))
    
    now = datetime.utcnow()
    if time_filter == 'today':
        query = query.filter(Post.created_at >= now - timedelta(days=1))
    elif time_filter == 'week':
        query = query.filter(Post.created_at >= now - timedelta(days=7))
    elif time_filter == 'month':
        query = query.filter(Post.created_at >= now - timedelta(days=30))
    
    posts = query.paginate(page=page, per_page=per_page)
    
    data = []
    for post in posts.items:
        author = User.query.get(post.user_id)
        data.append({
            'id': post.id,
            'user_id': post.user_id,
            'author_name': author.first_name or '匿名',
            'author_display_id': author.display_id or '000000',
            'author_avatar': author.avatar_url or '',
            'content': post.content,
            'media_urls': post.media_urls.split(',') if post.media_urls else [],
            'code_lang': post.code_lang,
            'code_content': post.code_content,
            'created_at': post.created_at.strftime('%Y-%m-%d %H:%M'),
            'likes': Like.query.filter_by(post_id=post.id).count(),
            'comments': Comment.query.filter_by(post_id=post.id).count(),
            'is_liked': current_user.is_authenticated and Like.query.filter_by(post_id=post.id, user_id=current_user.id).first() is not None,
            'is_subscribed': current_user.is_authenticated and Subscription.query.filter_by(follower_id=current_user.id, following_id=post.user_id).first() is not None
        })
    
    return jsonify({
        'ok': True,
        'posts': data,
        'has_next': posts.has_next,
        'total': posts.total
    })

# 2. 发布新帖子（✅ 修复：已取消 @login_required，改为手动 JSON 拦截）
@main_bp.route('/api/posts', methods=['POST'])
def create_post():
    if not current_user.is_authenticated:
        return jsonify({'ok': False, 'msg': '请先登录后再发布动态'}), 401
    
    data = request.get_json()
    content = data.get('content', '').strip()
    media_urls = data.get('media_urls', '')
    code_lang = data.get('code_lang', '')
    code_content = data.get('code_content', '')
    
    if not content and not code_content:
        return jsonify({'ok': False, 'msg': '内容不能为空'})
    
    post = Post(
        user_id=current_user.id,
        content=content,
        media_urls=media_urls,
        code_lang=code_lang,
        code_content=code_content
    )
    db.session.add(post)
    db.session.commit()
    
    return jsonify({'ok': True, 'msg': '发布成功', 'post_id': post.id})

# 3. 点赞/取消点赞
@main_bp.route('/api/posts/<int:post_id>/like', methods=['POST'])
def toggle_like(post_id):
    if not current_user.is_authenticated:
        return jsonify({'ok': False, 'msg': '请先登录'}), 401
    post = Post.query.get_or_404(post_id)
    like = Like.query.filter_by(post_id=post_id, user_id=current_user.id).first()
    if like:
        db.session.delete(like)
        db.session.commit()
        return jsonify({'ok': True, 'action': 'unliked', 'count': Like.query.filter_by(post_id=post_id).count()})
    else:
        new_like = Like(post_id=post_id, user_id=current_user.id)
        db.session.add(new_like)
        db.session.commit()
        return jsonify({'ok': True, 'action': 'liked', 'count': Like.query.filter_by(post_id=post_id).count()})

# 4. 获取评论
@main_bp.route('/api/posts/<int:post_id>/comments', methods=['GET'])
def get_comments(post_id):
    comments = Comment.query.filter_by(post_id=post_id).order_by(Comment.created_at.asc()).all()
    data = []
    for c in comments:
        author = User.query.get(c.user_id)
        data.append({
            'id': c.id,
            'user_id': c.user_id,
            'author_name': author.first_name or '匿名',
            'author_display_id': author.display_id or '000000',
            'content': c.content,
            'created_at': c.created_at.strftime('%Y-%m-%d %H:%M')
        })
    return jsonify({'ok': True, 'comments': data})

# 5. 发布评论
@main_bp.route('/api/posts/<int:post_id>/comments', methods=['POST'])
def create_comment(post_id):
    if not current_user.is_authenticated:
        return jsonify({'ok': False, 'msg': '请先登录'}), 401
    data = request.get_json()
    content = data.get('content', '').strip()
    if not content: return jsonify({'ok': False, 'msg': '评论不能为空'})
    comment = Comment(post_id=post_id, user_id=current_user.id, content=content)
    db.session.add(comment)
    db.session.commit()
    return jsonify({'ok': True, 'msg': '评论成功'})

# 6. 订阅/取消订阅
@main_bp.route('/api/users/<int:user_id>/subscribe', methods=['POST'])
def toggle_subscribe(user_id):
    if not current_user.is_authenticated:
        return jsonify({'ok': False, 'msg': '请先登录'}), 401
    if user_id == current_user.id:
        return jsonify({'ok': False, 'msg': '不能订阅自己'})
    sub = Subscription.query.filter_by(follower_id=current_user.id, following_id=user_id).first()
    if sub:
        db.session.delete(sub)
        db.session.commit()
        return jsonify({'ok': True, 'action': 'unsubscribed'})
    else:
        new_sub = Subscription(follower_id=current_user.id, following_id=user_id)
        db.session.add(new_sub)
        db.session.commit()
        return jsonify({'ok': True, 'action': 'subscribed'})

# ==========================================
# 辅助路由 (AI对话、机器人绑定等保持不变)
# ==========================================
def fetch_telegram_user_info(tg_id):
    try:
        resp = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getChat?chat_id={tg_id}", timeout=5)
        if resp.status_code == 200 and resp.json().get('ok'):
            chat = resp.json().get('result', {})
            return { 'first_name': chat.get('first_name', ''), 'last_name': chat.get('last_name', ''), 'username': chat.get('username', ''), 'avatar_url': None }
    except: pass
    return None

@main_bp.route('/api/bind_bot', methods=['POST'])
def bind_bot():
    data = request.get_json()
    token, chat_id, bot_name = data.get('token'), data.get('telegram_id'), data.get('name', '宫水编辑器')
    if not token or not chat_id: return jsonify({'ok': False, 'msg': '缺少参数'})
    result = execute_bind_bot(token, chat_id, bot_name)
    if result['ok']: return jsonify({'ok': True, 'msg': result['msg'], 'bot_name': result['bot_name'], 'bot_avatar_url': result.get('avatar')})
    return jsonify({'ok': False, 'msg': result['msg']})

def execute_bind_bot(token, chat_id, name='宫水编辑器'):
    try:
        test_resp = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
        if test_resp.status_code != 200: return {"ok": False, "msg": "Token 无效或网络错误"}
        getme_data = test_resp.json()
        real_bot_name = name; bot_avatar_url = None
        if getme_data.get('ok'):
            result = getme_data.get('result', {})
            real_bot_name = result.get('first_name') or result.get('username') or name
            bot_id = result.get('id')
            if bot_id:
                try:
                    photos_resp = requests.get(f"https://api.telegram.org/bot{token}/getUserProfilePhotos?user_id={bot_id}&limit=1", timeout=10)
                    if photos_resp.status_code == 200 and photos_resp.json().get('result', {}).get('total_count', 0) > 0:
                        file_id = photos_resp.json()['result']['photos'][0][-1]['file_id']
                        file_resp = requests.get(f"https://api.telegram.org/bot{token}/getFile?file_id={file_id}", timeout=10)
                        if file_resp.status_code == 200: 
                            file_path = file_resp.json()['result']['file_path']
                            bot_avatar_url = f"https://api.telegram.org/file/bot{token}/{file_path}"
                except: pass
        send_resp = requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id": chat_id, "text": f"机器人已绑定{real_bot_name}"}, timeout=10)
        if send_resp.status_code == 200: return {"ok": True, "msg": "绑定成功", "bot_name": real_bot_name, "avatar": bot_avatar_url}
        return {"ok": False, "msg": "Token有效，但向该ID发送消息失败"}
    except Exception as e: return {"ok": False, "msg": f"执行异常: {str(e)}"}

# ==========================================
# AI 接口
# ==========================================
DS_MODEL_MAP = {'discussion': 'deepseek-chat', 'agent': 'deepseek-chat'}
DS_API_BASE = "https://xh.v1api.cc/v1/chat/completions"

@main_bp.route('/api/agent/chat', methods=['POST'])
def agent_chat():
    data = request.get_json()
    user_message = data.get('message', '')
    mode = data.get('mode', 'discussion')
    if not user_message: return jsonify({'reply': '请先输入消息。'})
    user_config = data.get('config', {})
    mode_config = user_config.get(mode, {})
    if mode == 'discussion':
        system_prompt = SANDBOX_PROMPT if mode_config.get('jailbreak') else DEFAULT_PROMPT
    else:
        system_prompt = AGENT_PROMPT
    chat_summary = session.get('chat_summary', '')
    chat_history = session.get('chat_history', [])
    if len(chat_history) >= 15:
        summary_messages = [{"role": "system", "content": SUMMARY_PROMPT}, {"role": "user", "content": f"历史概要：{chat_summary}\n新对话内容：{chat_history}"}]
        summary_res, err = call_deepseek_core(summary_messages, 'deepseek-chat')
        if summary_res:
            chat_summary = summary_res['choices'][0]['message']['content']
            chat_history = []
            session['chat_summary'] = chat_summary
            session['chat_history'] = chat_history
    messages = [{"role": "system", "content": system_prompt}]
    if chat_summary: messages.append({"role": "system", "content": f"对话历史摘要：{chat_summary}"})
    for msg in chat_history: messages.append(msg)
    messages.append({"role": "user", "content": user_message})
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
    if not DEEPSEEK_API_KEY: return jsonify({'reply': '未配置 DeepSeek API Key。'})
    model_name = DS_MODEL_MAP.get(mode, 'deepseek-chat')
    raw_strength = mode_config.get('strength', 'low')
    reasoning_effort = 'high' if (model_name == "deepseek-v4-pro" and raw_strength == 'low') else raw_strength
    search_enabled = mode_config.get('search', False)
    tools = None
    if search_enabled: tools = TOOLS
    else: tools = [t for t in TOOLS if t['function']['name'] != 'web_search']
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {DEEPSEEK_API_KEY}"}
    initial_payload = {"model": model_name, "messages": messages, "temperature": 0.3, "stream": False, "extra_body": {"thinking": {"type": "enabled", "reasoning_effort": reasoning_effort}}}
    if tools: initial_payload['tools'] = tools; initial_payload['tool_choice'] = 'auto'
    try:
        initial_resp = requests.post(DS_API_BASE, headers=headers, json=initial_payload, timeout=60)
        if initial_resp.status_code != 200: return jsonify({'reply': f'DeepSeek 初始请求失败 (状态码: {initial_resp.status_code})'})
        initial_result = initial_resp.json()
        ai_message = initial_result['choices'][0]['message']
        reasoning_content = ai_message.get('reasoning_content')
        if ai_message.get('tool_calls'):
            for tool_call in ai_message['tool_calls']:
                func_name = tool_call['function']['name']
                args = json.loads(tool_call['function']['arguments'])
                result_content = {}
                if func_name == 'bind_bot': result_content = execute_bind_bot(args['token'], args['telegram_id'], args.get('name'))
                elif func_name == 'add_bot_node': result_content = {"status": "success", "action": "add_bot_node", "params": args}
                elif func_name == 'read_webpage': result_content = read_webpage(args['url'])
                elif func_name == 'web_search': result_content = web_search(args['query'])
                messages.append(ai_message)
                messages.append({"role": "tool", "tool_call_id": tool_call['id'], "content": json.dumps(result_content)})
            final_payload = {"model": model_name, "messages": messages, "temperature": 0.3, "stream": True, "extra_body": {"thinking": {"type": "enabled", "reasoning_effort": reasoning_effort}}}
            if tools: final_payload['tools'] = tools; final_payload['tool_choice'] = 'auto'
            def generate_final():
                try:
                    final_resp = requests.post(DS_API_BASE, headers=headers, json=final_payload, stream=True, timeout=90)
                    for line in final_resp.iter_lines():
                        if line:
                            line = line.decode('utf-8')
                            if line.startswith('data: '):
                                data_str = line[6:]
                                if data_str == '[DONE]': break
                                try:
                                    chunk = json.loads(data_str)
                                    delta = chunk['choices'][0]['delta']
                                    if delta.get('reasoning_content'): yield f"data: {json.dumps({'type': 'reasoning', 'content': delta['reasoning_content']})}\n\n"
                                    if delta.get('content'): yield f"data: {json.dumps({'type': 'content', 'content': delta['content']})}\n\n"
                                    if chunk['choices'][0].get('finish_reason'): yield f"data: {json.dumps({'type': 'done'})}\n\n"
                                except: pass
                except Exception as e: yield f"data: {json.dumps({'type': 'error', 'content': '流式输出异常'})}\n\n"
                finally: yield "data: [DONE]\n\n"
            session['chat_history'] = messages
            return Response(stream_with_context(generate_final()), mimetype='text/event-stream')
        else:
            final_reply = ai_message['content']
            def generate_normal():
                if reasoning_content: yield f"data: {json.dumps({'type': 'reasoning', 'content': reasoning_content})}\n\n"
                if final_reply: yield f"data: {json.dumps({'type': 'content', 'content': final_reply})}\n\n"
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                yield "data: [DONE]\n\n"
            session['chat_history'] = messages
            return Response(stream_with_context(generate_normal()), mimetype='text/event-stream')
    except Exception as e: print(f"Agent Error: {e}"); return jsonify({'reply': '请求异常，请稍后重试。'})

def call_deepseek_core(messages, model='deepseek-chat'):
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
    if not DEEPSEEK_API_KEY: return None, "未配置 Key"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {DEEPSEEK_API_KEY}"}
    payload = {"model": model, "messages": messages, "stream": False}
    try:
        resp = requests.post(DS_API_BASE, headers=headers, json=payload, timeout=30)
        if resp.status_code == 200: return resp.json(), None
        return None, f"错误: {resp.status_code}"
    except Exception as e: return None, str(e)

@main_bp.route('/api/agent/clear', methods=['POST'])
def clear_agent_history():
    session.pop('chat_history', None); session.pop('chat_summary', None)
    return jsonify({'status': 'ok', 'msg': '记忆已清空。'})

@main_bp.route('/api/send_code', methods=['POST'])
def send_code():
    data = request.get_json()
    account = data.get('email')
    if not account: return jsonify({'ok': False, 'msg': '请输入邮箱或电报ID'})
    code = str(random.randint(100000, 999999))
    if re.match(r"[^@]+@[^@]+\.[^@]+", account):
        record = EmailCode.query.filter_by(email=account).first()
        if record: record.code = code; record.created_at = datetime.utcnow()
        else: db.session.add(EmailCode(email=account, code=code))
        db.session.commit()
        try:
            msg = Message('【宫水编辑器】登录/注册验证码', recipients=[account])
            msg.body = f'您的验证码是：{code}，有效期为5分钟。请勿泄露给他人。'
            mail.send(msg)
            return jsonify({'ok': True, 'msg': '验证码已发送至邮箱，请查收。'})
        except Exception as e:
            print(f"邮件发送失败: {e}")
            return jsonify({'ok': False, 'msg': '邮件发送失败，请检查QQ邮箱授权码配置是否正确。'})
    else:
        success, _ = send_verification_code(account, code)
        return jsonify({'ok': True, 'msg': '已通过机器人发送验证码'}) if success else jsonify({'ok': False, 'msg': 'Telegram ID无效'})

@main_bp.route('/api/get_qr_login', methods=['GET'])
def get_qr_login():
    token = uuid.uuid4().hex[:16]
    deep_link = f"tg://resolve?domain=gsdsjbot&start=qr_{token}" if 'telegram' in request.headers.get('User-Agent', '').lower() else f"https://t.me/gsdsjbot?start=qr_{token}"
    db.session.add(QrLoginSession(token=token, status='pending')); db.session.commit()
    try:
        qr = qrcode.QRCode(box_size=10, border=2); qr.add_data(deep_link)
        img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
        d = ImageDraw.Draw(img)
        try: font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 55)
        except: font = ImageFont.load_default()
        bbox = d.textbbox((0, 0), "GS", font=font)
        d.text(((img.width - (bbox[2]-bbox[0]))/2, (img.height - (bbox[3]-bbox[1]))/2), "GS", fill=(0,0,0), font=font)
        buffered = io.BytesIO(); img.save(buffered, format="PNG")
        return jsonify({'success': True, 'token': token, 'url': deep_link, 'img_base64': f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode()}"})
    except: return jsonify({'success': True, 'token': token, 'url': deep_link, 'img_base64': f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={deep_link}&margin=10"})

@main_bp.route('/api/check_qr_login/<token>', methods=['GET'])
def check_qr_login(token):
    session_obj = QrLoginSession.query.filter_by(token=token).first()
    if not session_obj: return jsonify({'status': 'expired'})
    if session_obj.status == 'success' and session_obj.telegram_id:
        user = User.query.filter_by(telegram_id=session_obj.telegram_id).first()
        if user: login_user(user); user.last_login = datetime.utcnow(); db.session.commit(); return jsonify({'status': 'success'})
        return jsonify({'status': 'unregistered'})
    if (datetime.utcnow() - session_obj.created_at).seconds > 180:
        session_obj.status = 'expired'; db.session.commit(); return jsonify({'status': 'expired'})
    return jsonify({'status': session_obj.status})

@main_bp.route('/api/process_qr_token', methods=['POST'])
def process_qr_token():
    data = request.get_json()
    s = QrLoginSession.query.filter_by(token=data.get('token')).first()
    if s and s.status == 'pending': s.status = 'success'; s.telegram_id = data.get('chat_id'); db.session.commit(); return jsonify({'ok': True})
    return jsonify({'ok': False})

@main_bp.route('/register', methods=['POST'])
def register():
    account = request.form.get('email')
    code = request.form.get('code')
    
    ADMIN_SECRET_KEY = os.getenv('ADMIN_SECRET_KEY')
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

    if not all([account, code]): return "表格信息填写不完整"
    is_email = re.match(r"[^@]+@[^@]+\.[^@]+", account)
    record = EmailCode.query.filter_by(email=account).order_by(EmailCode.created_at.desc()).first() if is_email else TelegramCode.query.filter_by(telegram_id=account).order_by(TelegramCode.created_at.desc()).first()
    if not record or record.code != code or (datetime.utcnow() - record.created_at).seconds > 300: return "验证码错误或已超时"
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
        db.session.add(new_user); db.session.commit(); login_user(new_user)
        return "注册成功"

@main_bp.route('/tg_webhook', methods=['POST'])
def tg_webhook():
    data = request.get_json()
    if not data: return "Bad Request", 400
    if 'message' in data:
        msg = data['message']; chat_id = str(msg['chat']['id']); text = msg.get('text', '')
        if text.startswith('/start qr_'):
            token = text.replace('/start qr_', '').strip()
            session_obj = QrLoginSession.query.filter_by(token=token).first()
            if session_obj:
                if session_obj.status == 'pending':
                    session_obj.status = 'success'; session_obj.telegram_id = chat_id; db.session.commit()
                    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": chat_id, "text": "登录成功"})
                elif session_obj.status == 'expired':
                    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": chat_id, "text": "二维码已过期，请刷新"})
            return "OK"
        handle_message(data)
    return "OK"

@main_bp.route('/setup_webhook', methods=['GET'])
def setup_webhook():
    try:
        resp = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url=https://{request.host}/tg_webhook", timeout=10)
        return jsonify(resp.json())
    except Exception as e: return jsonify({'ok': False, 'error': str(e)})
