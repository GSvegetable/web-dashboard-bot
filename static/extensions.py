from flask_mail import Mail
from authlib.integrations.flask_client import OAuth

# 单独声明，不依赖 app 实例
mail = Mail()
oauth = OAuth()
