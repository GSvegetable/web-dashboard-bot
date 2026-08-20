from flask import render_template, redirect, url_for
from flask_login import current_user
from . import main_bp

@main_bp.route('/')
def splash():
    return render_template('splash.html')

@main_bp.route('/warehouse')
def warehouse():
    return render_template('warehouse.html')

@main_bp.route('/workspace')
def workspace():
    return render_template('workspace/workspace.html')

@main_bp.route('/community')
def community():
    return render_template('community.html')

@main_bp.route('/settings')
def settings_redirect():
    return redirect(url_for('main.settings_page', page='profile'))

@main_bp.route('/settings/<string:page>')
def settings_page(page):
    ALLOWED_SETTINGS = ['profile', 'stars', 'appearance', 'accessibility', 'notifications', 'billing', 'email', 'password', 'sessions', 'keys', 'credentials', 'organizations', 'enterprises', 'moderation', 'repositories', 'codespaces', 'packages']
    if page not in ALLOWED_SETTINGS:
        abort(404)
    return render_template('settings.html', active_page=page)

@main_bp.route('/workspace/add_bot')
def add_bot():
    return render_template('workspace/add_bot.html')
