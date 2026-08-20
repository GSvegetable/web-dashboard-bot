from flask import Blueprint

# 定义主蓝图
main_bp = Blueprint('main', __name__)

# 导入各个子模块，让它们把路由注册到 main_bp 上
from . import auth
from . import core
from . import admin
from . import api
from . import bot
from . import ai
