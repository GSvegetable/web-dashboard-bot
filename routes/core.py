from flask import render_template, redirect, url_for, abort, request, jsonify
from flask_login import current_user
from models import db, MyBot
from . import main_bp

# 前面的路由保持原样...

# 新增：获取当前登录用户的机器人列表
@main_bp.route('/api/my_bots', methods=['GET'])
def my_bots():
    if not current_user.is_authenticated:
        return jsonify({'ok': False, 'bots': []})
    bots = MyBot.query.filter_by(user_id=current_user.id).order_by(MyBot.created_at.desc()).all()
    data = []
    for bot in bots:
        data.append({
            'token': bot.token,
            'name': bot.bot_name or '未命名',
            'id': bot.bot_id or '',
            'username': bot.bot_username or ''
        })
    return jsonify({'ok': True, 'bots': data})
