import os, io, base64, uuid, random, re, requests, logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_login import login_user, current_user
from flask_mail import Message
from models import db, EmailCode, QrLoginSession, User
from extensions import mail
from telegram_bot import send_verification_code
from . import main_bp

logging.basicConfig(level=logging.INFO)

@main_bp.route('/api/get_qr_login', methods=['GET'])
def get_qr_login():
    try:
        token = uuid.uuid4().hex[:16]
        deep_link = f"tg://resolve?domain=gsdsjbot&start=qr_{token}" if 'telegram' in request.headers.get('User-Agent', '').lower() else f"https://t.me/gsdsjbot?start=qr_{token}"
        
        # 写入数据库
        db.session.add(QrLoginSession(token=token, status='pending'))
        db.session.commit()
        
        import qrcode
        from PIL import Image, ImageDraw, ImageFont

        qr = qrcode.QRCode(box_size=10, border=2)
        qr.add_data(deep_link)
        img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
        d = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 55)
        except:
            font = ImageFont.load_default()
        bbox = d.textbbox((0, 0), "GS", font=font)
        d.text(((img.width - (bbox[2]-bbox[0]))/2, (img.height - (bbox[3]-bbox[1]))/2), "GS", fill=(0,0,0), font=font)
        
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        return jsonify({'success': True, 'token': token, 'url': deep_link, 'img_base64': f"data:image/png;base64,{img_base64}"})
    except Exception as e:
        logging.error(f"生成二维码异常: {e}")
        # 兜底：不写数据库，直接使用外部API生成
        token = uuid.uuid4().hex[:16]
        deep_link = f"https://t.me/gsdsjbot?start=qr_{token}"
        return jsonify({'success': True, 'token': token, 'url': deep_link, 'img_base64': f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={deep_link}&margin=10"})

@main_bp.route('/api/send_code', methods=['POST'])
def send_code():
    data = request.get_json()
    account = data.get('email')
    if not account:
        return jsonify({'ok': False, 'msg': '请输入邮箱或电报ID'})
    
    code = str(random.randint(100000, 999999))
    try:
        if re.match(r"[^@]+@[^@]+\.[^@]+", account):
            record = EmailCode.query.filter_by(email=account).first()
            if record:
                record.code = code
                record.created_at = datetime.utcnow()
            else:
                db.session.add(EmailCode(email=account, code=code))
            db.session.commit()
            try:
                msg = Message('【宫水编辑器】登录/注册验证码', recipients=[account])
                msg.body = f'您的验证码是：{code}，有效期为5分钟。请勿泄露给他人。'
                mail.send(msg)
                return jsonify({'ok': True, 'msg': '验证码已发送至邮箱，请查收。'})
            except Exception as e:
                logging.error(f"邮件发送失败: {e}")
                return jsonify({'ok': False, 'msg': '邮件发送失败，请检查QQ邮箱授权码配置是否正确。'})
        else:
            send_verification_code(account, code)
            return jsonify({'ok': True, 'msg': '已通过机器人发送验证码'})
    except Exception as e:
        logging.error(f"发送验证码异常: {e}")
        return jsonify({'ok': False, 'msg': '发送验证码异常，请稍后重试。'})
