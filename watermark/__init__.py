
import os
import sys

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_login import current_user
from flask_bootstrap import Bootstrap
from flask_dropzone import Dropzone
app = Flask(__name__)
 # 初始化扩展，传入程序实例 app

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
print(os.getenv('SQLALCHEMY_DATABASE_URI'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS')  # 关闭对模型修改的监控
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['DEBUG'] = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')
app.config['ENV'] = os.getenv('ENV', 'production')
Bootstrap(app)
db = SQLAlchemy()
db.init_app(app)
 
login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'signin'
login_manager.init_app(app=app)
dropzone = Dropzone()
dropzone.init_app(app)
@app.context_processor
def inject_user():
    return dict(user=current_user)
# 这个函数自动注册这里面的资源到每个页面的上下文环境中，所以可以在模板中直接使用user变量。

@login_manager.user_loader
def load_user(user_id):  # 创建用户加载回调函数，接受用户 ID 作为参数
    from watermark.models import Users
    user = Users.query.get(int(user_id))  # 用 ID 作为 User 模型的主键查询对应的用户
    return user  # 返回用户对象

from watermark import views, commands