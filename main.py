# --- 🟢 发送验证码（自动辨别邮箱或电报ID） ---
@app.route('/api/send_code', methods=['POST'])
def send_code():
    data = request.get_json()
    account = data.get('email') # 前端传过来的是 name="reg-email" 的值
    
    if not account:
        return jsonify({'ok': False, 'msg': '请输入账号或电报ID'})
    
    code = str(random.randint(100000, 999999))
    
    # 判断是不是邮箱（包含 @ 和 .）
    is_email = re.match(r"[^@]+@[^@]+\.[^@]+", account)
    
    if is_email:
        # --- 邮箱发送逻辑 ---
        record = EmailCode.query.filter_by(email=account).first()
        if record:
            record.code = code
            record.created_at = datetime.now(timezone.utc)
        else:
            new_record = EmailCode(email=account, code=code)
            db.session.add(new_record)
        db.session.commit()
        return jsonify({'ok': True, 'msg': '验证码已发送至邮箱'})
    
    else:
        # --- ⭐ 电报ID发送逻辑 ---
        success, _ = send_verification_code(account)
        if success:
            return jsonify({'ok': True, 'msg': '已通过Telegram机器人发送验证码'})
        else:
            # 修改：把错误传递给前端，你就能看懂了
            return jsonify({'ok': False, 'msg': '电报ID无效或机器人未响应，请在Railway后台查看最新日志'})
