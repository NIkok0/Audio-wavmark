from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_wtf.file import FileField, FileRequired


class WatermarkForm(FlaskForm):
    watermark = StringField('水印内容', validators=[DataRequired()])
    submit = SubmitField('提交')

