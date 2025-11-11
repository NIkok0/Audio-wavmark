# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, ValidationError
from watermark.models import User, Group


class UserPermissionForm(FlaskForm):
    """用户权限管理表单"""
    username = StringField('用户名', validators=[DataRequired(), Length(1, 64)])
    email = StringField('邮箱', validators=[DataRequired(), Email(), Length(1, 64)])
    role = SelectField('角色', choices=[
        ('member', '成员'),
        ('admin', '管理员'),
        ('super_admin', '超级管理员')
    ], validators=[DataRequired()])
    is_active = BooleanField('激活状态', default=True)
    submit = SubmitField('保存')

    def __init__(self, user=None, *args, **kwargs):
        super(UserPermissionForm, self).__init__(*args, **kwargs)
        self.user = user

    def validate_username(self, field):
        if self.user and self.user.username == field.data:
            return
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('该用户名已存在')

    def validate_email(self, field):
        if self.user and self.user.email == field.data:
            return
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('该邮箱已被注册')


class GroupManagementForm(FlaskForm):
    """组管理表单"""
    name = StringField('组名', validators=[DataRequired(), Length(1, 64)])
    description = TextAreaField('描述', validators=[Length(0, 500)])
    submit = SubmitField('保存')

    def __init__(self, group=None, *args, **kwargs):
        super(GroupManagementForm, self).__init__(*args, **kwargs)
        self.group = group

    def validate_name(self, field):
        if self.group and self.group.name == field.data:
            return
        if Group.query.filter_by(name=field.data).first():
            raise ValidationError('该组名已存在')


class UserGroupAssignmentForm(FlaskForm):
    """用户组分配表单"""
    user_id = SelectField('用户', coerce=int, validators=[DataRequired()])
    group_ids = SelectField('组别', coerce=int, validators=[DataRequired()])
    submit = SubmitField('分配')

    def __init__(self, *args, **kwargs):
        super(UserGroupAssignmentForm, self).__init__(*args, **kwargs)
        # 动态加载用户和组选项
        self.user_id.choices = [(u.id, f"{u.username} ({u.email})") for u in User.query.filter_by(is_active=True).all()]
        self.group_ids.choices = [(g.id, g.name) for g in Group.query.all()]

