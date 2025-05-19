from watermark import db
from datetime import datetime
from flask_login import UserMixin

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

    def get_id(self):
        return str(self.id)

# 3. 用户组表
class Group(db.Model):
    __tablename__ = 'groups'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    note = db.Column(db.Text)

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

    uploader_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    uploader = db.relationship("User", back_populates="uploaded_files")
    group = db.relationship("Group", back_populates="files")
