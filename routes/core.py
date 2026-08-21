from flask import render_template, redirect, url_for, abort
from . import main_bp

@main_bp.route('/')
def splash():
    return render_template('splash.html')

@main_bp.route('/warehouse')
def warehouse():
    return redirect(url_for('main.workspace'))

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
    ALLOWED = ['profile', 'stars', 'appearance', 'accessibility', 'notifications', 'billing', 'email', 'password', 'sessions', 'keys', 'credentials', 'organizations', 'enterprises', 'moderation', 'repositories', 'codespaces', 'packages']
    if page not in ALLOWED:
        abort(404)
    return render_template('settings.html', active_page=page)
