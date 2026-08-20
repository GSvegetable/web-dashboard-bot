from flask import request, jsonify
from flask_login import current_user
from datetime import datetime, timedelta
from models import db, Post, Comment, Like, Subscription, User
from . import main_bp

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
    post = Post(user_id=current_user.id, content=content, media_urls=media_urls, code_lang=code_lang, code_content=code_content)
    db.session.add(post)
    db.session.commit()
    return jsonify({'ok': True, 'msg': '发布成功', 'post_id': post.id})

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

@main_bp.route('/api/posts/<int:post_id>/comments', methods=['POST'])
def create_comment(post_id):
    if not current_user.is_authenticated:
        return jsonify({'ok': False, 'msg': '请先登录'}), 401
    data = request.get_json()
    content = data.get('content', '').strip()
    if not content:
        return jsonify({'ok': False, 'msg': '评论不能为空'})
    comment = Comment(post_id=post_id, user_id=current_user.id, content=content)
    db.session.add(comment)
    db.session.commit()
    return jsonify({'ok': True, 'msg': '评论成功'})

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
