# Standard library imports
import os
import datetime

# Third-party imports
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_dropzone import Dropzone
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

# Initialize Flask app
app = Flask(__name__)

# 配置文件路径
app.config['INSTANCE_PATH'] = os.getenv('INSTANCE_PATH', 'instance')
app.config['TEMP_FOLDER'] = os.path.join(app.config['INSTANCE_PATH'], 'temp')
app.config['LOGS_FOLDER'] = os.path.join(app.config['INSTANCE_PATH'], 'logs')

# 按媒体类型分类的文件存储路径配置
app.config['MEDIA_FOLDERS'] = {
    'image': {
        'upload':  os.path.join(app.config['INSTANCE_PATH'], 'uploads', 'images'),
        'extract': os.path.join(app.config['INSTANCE_PATH'], 'extracts', 'images'),
        'embed': os.path.join(app.config['INSTANCE_PATH'], 'embeds', 'images')
    },
    'audio': {
        'upload': os.path.join(app.config['INSTANCE_PATH'], 'uploads', 'audio'),
        'extract': os.path.join(app.config['INSTANCE_PATH'], 'extracts', 'audio'),
        'embed': os.path.join(app.config['INSTANCE_PATH'], 'embeds', 'audio')
    },
    'video': {
        'upload': os.path.join(app.config['INSTANCE_PATH'], 'uploads', 'video'),
        'extract': os.path.join(app.config['INSTANCE_PATH'], 'extracts', 'video'),
        'embed': os.path.join(app.config['INSTANCE_PATH'], 'embeds', 'video')
    },
    'text': {
        'upload': os.path.join(app.config['INSTANCE_PATH'], 'uploads', 'documents'),
        'extract': os.path.join(app.config['INSTANCE_PATH'], 'extracts', 'documents'),
        'embed': os.path.join(app.config['INSTANCE_PATH'], 'embeds', 'documents')
    }
}

def ensure_directories():
    """确保所有必要的目录存在"""
    # 基础目录
    base_directories = [
        app.config['INSTANCE_PATH'],
        app.config['TEMP_FOLDER'],
        app.config['LOGS_FOLDER']
    ]
    
    # 媒体类型目录
    media_directories = []
    for _, folders in app.config['MEDIA_FOLDERS'].items():
        for _, folder_path in folders.items():
            media_directories.append(folder_path)
    all_directories = base_directories + media_directories
    
    for directory in all_directories:
        if not os.path.exists(directory):
            os.makedirs(directory, mode=0o755, exist_ok=True)

ensure_directories()

def get_media_folder(media_type, folder_type):
    """获取指定媒体类型和操作类型的文件夹路径"""
    media_folders = app.config.get('MEDIA_FOLDERS', {})
    if media_type in media_folders and folder_type in media_folders[media_type]:
        return media_folders[media_type][folder_type]
    # 如果没有找到，返回默认路径
    return None

# 将函数添加到应用上下文，以方便前端页面直接调用使用url
app.jinja_env.globals.update(get_media_folder=get_media_folder)

# 配置数据库
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', 'mysql+pymysql://root:88888888@localhost:3306/watermark_test')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS', 'False').lower() in ('true', '1', 't')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')
app.config['DEBUG'] = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')
app.config['ENV'] = os.getenv('ENV', 'production')

# 初始化扩展
Bootstrap(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# 配置登录管理
login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'signin'
login_manager.init_app(app=app)

# 配置文件上传
dropzone = Dropzone()
dropzone.init_app(app)

# 添加自定义过滤器
@app.template_filter('path_exists')
def path_exists_filter(path):
    """检查文件路径是否存在"""
    return path and os.path.exists(path)

@app.context_processor
def inject_user():
    return dict(user=current_user)

@app.context_processor
def inject_now():
    return {'now': datetime.datetime.now}

@login_manager.user_loader
def load_user(user_id):  # 创建用户加载回调函数，接受用户 ID 作为参数
    from watermark.models import User
    user = User.query.get(int(user_id))  # 用 ID 作为 User 模型的主键查询对应的用户
    return user  # 返回用户对象

# Local imports
from watermark import views, commands