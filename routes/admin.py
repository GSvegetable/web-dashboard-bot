from flask import render_template, request, jsonify
from flask_login import current_user
from datetime import date
from models import db, User, VisitLog, Transaction, Post, Like
from . import main_bp

@main_bp.route('/admin/dashboard')
def admin_dashboard():
    if not current_user.is_authenticated or not current_user.is_admin:
        return "无权访问，请使用管理员密码登录", 403
    
    today = date.today()
    total_visits = VisitLog.query.count()
    today_visits = VisitLog.query.filter(db.func.date(VisitLog.visited_at) == today).count()
    total_uv = VisitLog.query.distinct(VisitLog.ip_address).count()
    today_uv = VisitLog.query.filter(db.func.date(VisitLog.visited_at) == today).distinct(VisitLog.ip_address).count()
    total_users = User.query.count()
    today_registered = User.query.filter(db.func.date(User.created_at) == today).count()
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
    if not user_id or amount is None:
        return jsonify({'ok': False, 'msg': '参数缺失'})
    try:
        amount = int(amount)
        if amount <= 0:
            return jsonify({'ok': False, 'msg': '赠送数量必须大于 0'})
    except:
        return jsonify({'ok': False, 'msg': '数量格式错误'})
    user = User.query.get(int(user_id))
    if not user:
        return jsonify({'ok': False, 'msg': '用户不存在'})
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
    if not post_id:
        return jsonify({'ok': False, 'msg': '参数缺失'})
    post = Post.query.get(int(post_id))
    if not post:
        return jsonify({'ok': False, 'msg': '帖子不存在'})
    post.is_hidden = True
    db.session.commit()
    return jsonify({'ok': True, 'msg': '已隐藏该帖子'})
