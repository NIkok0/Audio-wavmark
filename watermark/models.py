# Standard library imports
from datetime import datetime

# Third-party imports
from flask_login import UserMixin

# Local imports
from watermark import db
from watermark.utils.time_provider import get_now_utc

# 1. 用户-组 多对多关联表
user_group_rel = db.Table('user_group_rel',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('group_id', db.Integer, db.ForeignKey('groups.id'), primary_key=True)
)

# 2. 用户表
class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)  # 用户名
    email = db.Column(db.String(64), unique=True, nullable=False)     # 邮箱
    password = db.Column(db.String(512), nullable=False)              # 密码
    is_admin = db.Column(db.Boolean, default=False)                  # 是否管理员

    # 关系
    groups = db.relationship("Group", secondary=user_group_rel, back_populates="users")
    uploaded_files = db.relationship("File", back_populates="uploader")
    # operation_logs = db.relationship("OperationLog", back_populates="user")

    def get_id(self):
        return str(self.id)

# 3. 用户组表
class Group(db.Model):
    __tablename__ = 'groups'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=get_now_utc)

    # 关系
    users = db.relationship("User", secondary=user_group_rel, back_populates="groups")
    files = db.relationship("File", back_populates="group")

# 4. 文件表
class File(db.Model):
    __tablename__ = 'files'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_path = db.Column(db.String(512), nullable=False)
    watermarked_path = db.Column(db.String(512), nullable=True)
    file_hash = db.Column(db.String(128), nullable=False)
    has_watermark = db.Column(db.Boolean, default=False)
    file_type = db.Column(db.String(20), nullable=False)  # image/video/audio/text
    file_format = db.Column(db.String(20), nullable=False)  # jpg/png/mp4/wav/txt等
    file_size = db.Column(db.BigInteger, nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    watermark_type = db.Column(db.String(50), nullable=True)
    watermark_text = db.Column(db.Text, nullable=True)  
    original_watermark_text = db.Column(db.Text, nullable=True)  # 存储原始水印文本
    watermark_seed = db.Column(db.String(20), nullable=True)  # 存储随机种子
    processing_status = db.Column(db.String(20), default='pending')  # pending/completed/failed
    error_message = db.Column(db.Text, nullable=True)

    uploader_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=True)

    created_at = db.Column(db.DateTime, default=get_now_utc)
    updated_at = db.Column(db.DateTime, default=get_now_utc, onupdate=get_now_utc)

    # 关系
    uploader = db.relationship("User", back_populates="uploaded_files")
    group = db.relationship("Group", back_populates="files")

# class OperationLog(db.Model):
#     __tablename__ = 'operation_logs'
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
#     file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=True)
#     operation_type = db.Column(db.String(50), nullable=False)  # upload/embed/extract/download/delete
#     operation_details = db.Column(db.Text, nullable=True)
#     ip_address = db.Column(db.String(45), nullable=True)
#     user_agent = db.Column(db.Text, nullable=True)
#     success = db.Column(db.Boolean, default=True)
#     error_message = db.Column(db.Text, nullable=True)
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
#     user = db.relationship("User", back_populates="operation_logs")
#     file = db.relationship("File", backref="operation_logs")
