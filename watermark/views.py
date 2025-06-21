from flask import render_template, Flask, redirect, url_for, request, flash, session, jsonify, abort
from flask_bootstrap import Bootstrap
from watermark.forms.login_form import LoginForm
from watermark.forms.watermark_form import WatermarkForm
from watermark.forms.register_form import RegisterForm
import os
import hashlib
from watermark.models import User, Group, File
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, current_user, logout_user
from flask_login import LoginManager
from werkzeug.utils import secure_filename
import re
# from watermark.watermarkSystem import watermarks_select  # 已替换为AlgorithmSelector
from watermark.utils.algorithm_selector import AlgorithmSelector
from watermark.utils.file_config import get_file_type_by_extension, validate_file_size
# from watermark.utils.logger import OperationLogger
from flask import send_file, current_app
import json
from watermark import app, db
import mimetypes
from datetime import datetime
from watermark.utils.file_config import get_file_size_info
# 使用配置中的文件路径

temp_dir = app.config['TEMP_FOLDER']
logs_dir = app.config['LOGS_FOLDER']
def get_upload_path(media_type):
    """获取指定媒体类型的上传路径"""
    return app.config['MEDIA_FOLDERS'][media_type]['upload']

def get_extract_path(media_type):
    """获取指定媒体类型的提取路径"""
    return app.config['MEDIA_FOLDERS'][media_type]['extract']

def get_embed_path(media_type):
    """获取指定媒体类型的嵌入路径"""
    return app.config['MEDIA_FOLDERS'][media_type]['embed']


def secure_filename_with_chinese(filename):
    """支持中文的安全文件名处理函数"""
    # 分离文件名和扩展名
    name, ext = os.path.splitext(filename)
    
    # 替换不安全的字符为下划线，保留中文字符
    # 只保留字母、数字、中文字符和下划线
    name = re.sub(r'[^\w\u4e00-\u9fff]+', '_', name)
    
    # 确保文件名不为空
    if not name:
        name = '_'
    
    return name + ext

def calculate_file_hash(file_path):
    """计算文件的SHA256哈希值"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

#主页
@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

#注册
@app.route('/register.html', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    error_message = None
    success_message = None
    
    if form.validate_on_submit():
        # 检查用户名和邮箱是否已存在
        if User.query.filter_by(username=form.username.data).first():
            error_message = "该用户名已存在！"
        elif User.query.filter_by(email=form.email.data).first():
            error_message = "该邮箱已注册！"
        else:
            # 创建新用户
            user = User(
                username=form.username.data,
                email=form.email.data,
                password=generate_password_hash(form.password.data)
            )
            db.session.add(user)
            db.session.commit()
            success_message = "注册成功，请登录！"
            # 注册成功后重定向到登录页面
            flash(success_message)
            return redirect(url_for('signin'))
    
    return render_template('register.html', form=form, error_message=error_message, success_message=success_message)

#登录
@app.route('/signin.html', methods=['GET', 'POST'])
def signin():
    form = LoginForm()
    error_message = None
    
    if request.method == 'POST':
        # 从普通HTML表单获取数据
        username_or_email = request.form.get('username_or_email')
        password = request.form.get('password')
        
        if username_or_email and password:
            # 尝试通过用户名或邮箱查找用户
            user = User.query.filter(
                (User.username == username_or_email) | 
                (User.email == username_or_email)
            ).first()
            
            if user and check_password_hash(user.password, password):
                login_user(user)
                flash(f"欢迎回来，{user.username}！")
                return redirect(url_for('index'))
            else:
                error_message = "用户名/邮箱或密码错误，请重新登录！"
        else:
            error_message = "请填写用户名和密码！"
    
    return render_template('signin.html', form=form, error_message=error_message)

#登出
@app.route('/signout.html', methods=['GET', 'POST'])
@login_required
def signout():
    logout_user()
    return redirect(url_for('index'))





#文件下载
@app.route('/download/<int:file_id>', methods=['GET'])
@login_required
def download(file_id):
    file = File.query.get_or_404(file_id)
    print(current_app.root_path)
    # 验证文件所有权
    if file.uploader_id != current_user.id:
        flash('您没有权限下载该文件')
        return redirect(url_for('index'))

    try:
        root_dir = os.path.abspath(os.path.join(current_app.root_path, '..'))
        abs_path = os.path.join(root_dir, file.watermarked_path)
        return send_file(
            abs_path,  # 直接使用相对目录路径
            file.filename,   # 文件名
            as_attachment=True
        )
    except Exception as e:
        flash(f'下载失败: {str(e)}')
        return redirect(url_for('index'))

#删除文件
@app.route('/delete_file/<int:file_id>', methods=['POST'])
@login_required
def delete_file(file_id):
    file = File.query.get_or_404(file_id)
    
    # 验证文件所有权
    if file.uploader_id != current_user.id:
        flash('您没有权限删除该文件')
        return redirect(url_for('index'))
    
    # 记录文件路径以便删除
    original_path = file.original_path
    watermarked_path = file.watermarked_path
    
    # 从数据库中删除记录
    db.session.delete(file)
    db.session.commit()
    
    # 尝试删除物理文件
    try:
        if original_path and os.path.exists(original_path):
            os.remove(original_path)
            
        if watermarked_path and os.path.exists(watermarked_path):
            os.remove(watermarked_path)
            
        # 记录删除日志
        # OperationLogger.log_delete(
        #     current_user.id,
        #     file.id,
        #     file.filename,
        #     success=True
        # )
        
        flash('文件已成功删除')
    except Exception as e:
        # 记录失败日志
        # OperationLogger.log_delete(
        #     current_user.id,
        #     file.id,
        #     file.filename,
        #     success=False,
        #     error_message=str(e)
        # )
        flash(f'删除文件时出错: {str(e)}')
    
    # 根据请求来源决定重定向位置
    referer = request.referrer
    if referer:
        if 'image' in referer:
            if 'upload' in referer:
                return redirect(url_for('image_upload'))
            elif 'add_watermark' in referer:
                return redirect(url_for('image_add_watermark'))
            elif 'extract_watermark' in referer:
                return redirect(url_for('image_extract_watermark'))
        elif 'audio' in referer:
            if 'upload' in referer:
                return redirect(url_for('audio_upload'))
            elif 'add_watermark' in referer:
                return redirect(url_for('audio_add_watermark'))
            elif 'extract_watermark' in referer:
                return redirect(url_for('audio_extract_watermark'))
        elif 'video' in referer:
            if 'upload' in referer:
                return redirect(url_for('video_upload'))
            elif 'add_watermark' in referer:
                return redirect(url_for('video_add_watermark'))
            elif 'extract_watermark' in referer:
                return redirect(url_for('video_extract_watermark'))
        elif 'text' in referer:
            if 'upload' in referer:
                return redirect(url_for('text_upload'))
            elif 'add_watermark' in referer:
                return redirect(url_for('text_add_watermark'))
            elif 'extract_watermark' in referer:
                return redirect(url_for('text_extract_watermark'))
    return redirect(url_for('index'))



# 清除提取结果
@app.route('/clear_extract_result', methods=['POST'])
@login_required
def clear_extract_result():
    filename = request.form.get('filename')
    file_type = request.form.get('file_type')  # 新增：从表单获取文件类型
    if not filename or not file_type:
        return redirect(request.referrer)
    
    session_key = f'{file_type}_extracted_files'
    extracted_files = session.get(session_key, {})
    if filename in extracted_files:
        del extracted_files[filename]
        session[session_key] = extracted_files
    
    return redirect(request.referrer)

# 清除所有提取结果
@app.route('/clear_all_extract_results', methods=['POST'])
@login_required
def clear_all_extract_results():
    file_type = request.form.get('file_type')  # 新增：从表单获取文件类型
    if not file_type:
        return redirect(request.referrer)
    
    session_key = f'{file_type}_extracted_files'
    session[session_key] = {}
    
    return redirect(request.referrer)

# 计算相似度
def calculate_similarity(str1, str2):
    """计算两个字符串的相似度"""
    def levenshtein_distance(s1, s2):
        if len(s1) < len(s2):
            return levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]
    
    if not str1 or not str2:
        return 0.0
    
    distance = levenshtein_distance(str1, str2)
    max_len = max(len(str1), len(str2))
    similarity = 1 - (distance / max_len)
    return similarity

# 图片处理相关路由
@app.route('/image/process')
@login_required
def image_process():
    return render_template('image/image_process.html')

@app.route('/image/upload', methods=['GET', 'POST'])
@login_required
def image_upload():
    if request.method == 'POST':
        f = request.files.get('file')
        if not f:
            return '没有选择文件', 400
            
        if '.' not in f.filename:
            return '文件名无效', 400
        file_ext = f.filename.rsplit('.', 1)[1].lower()
        if file_ext not in ['jpg', 'jpeg', 'png', 'bmp', 'gif']:
            return f'不支持的图片格式: {file_ext}', 400
            
        original_filename = secure_filename_with_chinese(f.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{current_user.id}_{timestamp}_{original_filename}"
        file_path = os.path.join(get_upload_path('image'), unique_filename)
        
        try:
            f.save(file_path)
            file_size = os.path.getsize(file_path)
            mime_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
            file_hash = calculate_file_hash(file_path)
            
            if not validate_file_size(file_size, 'image'):
                os.remove(file_path)
                return '文件大小超出限制', 400
            
            file_record = File(
                filename=original_filename,
                original_path=file_path,
                file_hash=file_hash,
                file_type='image',
                file_format=file_ext,
                file_size=file_size,
                mime_type=mime_type,
                uploader_id=current_user.id,
                group_id=current_user.groups[0].id if current_user.groups else None,
                processing_status='pending'
            )
            
            db.session.add(file_record)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'file_id': file_record.id,
                'filename': original_filename,
                'file_type': 'image'
            })
            
        except Exception as e:
            return jsonify({'error': f'上传失败: {str(e)}'}), 500
    
    # 获取当前用户的文件列表
    user_group_ids = [group.id for group in current_user.groups]
    if user_group_ids:
        files = File.query.filter(
            File.group_id.in_(user_group_ids),
            File.file_type == 'image'
        ).order_by(File.created_at.desc()).all()
    else:
        files = File.query.filter_by(
            uploader_id=current_user.id,
            file_type='image'
        ).order_by(File.created_at.desc()).all()
    
    return render_template('image/upload.html', files=files)

@app.route('/image/add_watermark', methods=['GET', 'POST'])
@login_required
def image_add_watermark():
    form = WatermarkForm()
    if form.validate_on_submit():
        # 获取选中的文件ID
        selected_file_ids = request.form.get('selected_file_ids', '')
        
        if selected_file_ids:
            # 处理选中的文件
            file_ids = [int(id.strip()) for id in selected_file_ids.split(',') if id.strip()]
            files = File.query.filter(
                File.id.in_(file_ids),
                File.uploader_id == current_user.id,
                File.file_type == 'image',
                File.has_watermark == False
            ).all()
        else:
            # 处理所有未添加水印的文件
            user_group_ids = [group.id for group in current_user.groups]
            
            if user_group_ids:
                files = File.query.filter(
                    File.group_id.in_(user_group_ids),
                    File.has_watermark == False,
                    File.file_type == 'image'
                ).all()
            else:
                files = File.query.filter_by(
                    uploader_id=current_user.id,
                    has_watermark=False,
                    file_type='image'
                ).all()
        
        success_count = 0
        error_count = 0
        selector = AlgorithmSelector()
        
        for file in files:
            try:
                file.processing_status = 'processing'
                db.session.commit()
                
                result = selector.select_algorithm(
                    'image', 
                    file.original_path, 
                    form.watermark.data
                )
                
                if result['success']:
                    file.watermarked_path = result['result']
                    file.has_watermark = True
                    file.watermark_type = result['algorithm']
                    file.watermark_text = form.watermark.data
                    file.processing_status = 'completed'
                    file.error_message = None
                    success_count += 1
                else:
                    file.processing_status = 'failed'
                    file.error_message = '水印处理失败'
                    error_count += 1
                    
            except Exception as e:
                file.processing_status = 'failed'
                file.error_message = str(e)
                error_count += 1
        
        db.session.commit()
        
        if success_count > 0:
            flash(f"成功处理 {success_count} 个文件")
        if error_count > 0:
            flash(f"处理失败 {error_count} 个文件")
        
        return redirect(url_for('image_add_watermark'))
    
    user_group_ids = [group.id for group in current_user.groups]
    if user_group_ids:
        files = File.query.filter(
            File.group_id.in_(user_group_ids),
            File.file_type == 'image'
        ).order_by(File.created_at.desc()).all()
    else:
        files = File.query.filter_by(
            uploader_id=current_user.id,
            file_type='image'
        ).order_by(File.created_at.desc()).all()
    
    return render_template('image/add_watermark.html', form=form, files=files)

@app.route('/image/extract_watermark', methods=['GET', 'POST'])
@login_required
def image_extract_watermark():
    extracted_files = session.get('image_extracted_files', {})
    files = File.query.filter_by(uploader_id=current_user.id, file_type='image', has_watermark=True).all()
    return render_template('image/extract_watermark.html', extracted_files=extracted_files, files=files)

@app.route('/image/extract_from_file/<int:file_id>')
@login_required
def image_extract_from_file(file_id):
    file = File.query.get_or_404(file_id)
    
    if file.uploader_id != current_user.id or file.file_type != 'image':
        flash('您没有权限提取该文件的水印')
        return redirect(url_for('image_extract_watermark'))
    
    if not file.has_watermark:
        flash('该文件尚未添加水印')
        return redirect(url_for('image_extract_watermark'))
    
    if not file.watermarked_path or not os.path.exists(file.watermarked_path):
        flash(f'无法找到水印文件: {file.filename}')
        return redirect(url_for('image_extract_watermark'))
    
    try:
        algorithm = file.watermark_type 
        selector = AlgorithmSelector()
        result = selector.extract_watermark(
            'image', 
            file.watermarked_path, 
            algorithm=algorithm
        )
        
        # 将结果存储到session中，使用类型前缀
        extracted_files = session.get('image_extracted_files', {})
        extracted_files[file.filename] = result
        session['image_extracted_files'] = extracted_files
        
        flash(f"水印提取成功")
        
    except Exception as e:
        flash(f"水印提取失败: {str(e)}")
    
    # 检查是否是批量操作
    if 'selected' in request.args:
        selected_ids = request.args.get('selected').split(',')
        # 如果还有其他文件需要处理
        remaining_ids = [id for id in selected_ids if int(id) != file_id]
        if remaining_ids:
            # 继续处理下一个文件
            next_id = remaining_ids[0]
            new_selected = ','.join(remaining_ids)
            return redirect(url_for('image_extract_from_file', file_id=next_id, selected=new_selected))
    
    return redirect(url_for('image_extract_watermark'))

# 音频处理相关路由
@app.route('/audio/process')
@login_required
def audio_process():
    return render_template('audio/audio_process.html')

@app.route('/audio/upload', methods=['GET', 'POST'])
@login_required
def audio_upload():
    if request.method == 'POST':
        f = request.files.get('file')
        if not f:
            return '没有选择文件', 400
            
        if '.' not in f.filename:
            return '文件名无效', 400
        file_ext = f.filename.rsplit('.', 1)[1].lower()
        if file_ext not in ['mp3', 'wav', 'flac', 'aac']:
            return f'不支持的音频格式: {file_ext}', 400
            
        original_filename = secure_filename_with_chinese(f.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{current_user.id}_{timestamp}_{original_filename}"
        file_path = os.path.join(get_upload_path('audio'), unique_filename)
        
        try:
            f.save(file_path)
            file_size = os.path.getsize(file_path)
            mime_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
            file_hash = calculate_file_hash(file_path)
            
            if not validate_file_size(file_size, 'audio'):
                os.remove(file_path)
                return '文件大小超出限制', 400
            
            file_record = File(
                filename=original_filename,
                original_path=file_path,
                file_hash=file_hash,
                file_type='audio',
                file_format=file_ext,
                file_size=file_size,
                mime_type=mime_type,
                uploader_id=current_user.id,
                group_id=current_user.groups[0].id if current_user.groups else None,
                processing_status='pending'
            )
            
            db.session.add(file_record)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'file_id': file_record.id,
                'filename': original_filename,
                'file_type': 'audio'
            })
            
        except Exception as e:
            return jsonify({'error': f'上传失败: {str(e)}'}), 500
    
    # 获取当前用户的文件列表
    user_group_ids = [group.id for group in current_user.groups]
    if user_group_ids:
        files = File.query.filter(
            File.group_id.in_(user_group_ids),
            File.file_type == 'audio'
        ).order_by(File.created_at.desc()).all()
    else:
        files = File.query.filter_by(
            uploader_id=current_user.id,
            file_type='audio'
        ).order_by(File.created_at.desc()).all()
    
    return render_template('audio/upload.html', files=files)

@app.route('/audio/add_watermark', methods=['GET', 'POST'])
@login_required
def audio_add_watermark():
    form = WatermarkForm()
    if form.validate_on_submit():
        # 获取选中的文件ID
        selected_file_ids = request.form.get('selected_file_ids', '')
        
        if selected_file_ids:
            # 处理选中的文件
            file_ids = [int(id.strip()) for id in selected_file_ids.split(',') if id.strip()]
            files = File.query.filter(
                File.id.in_(file_ids),
                File.uploader_id == current_user.id,
                File.file_type == 'audio',
                File.has_watermark == False
            ).all()
        else:
            # 处理所有未添加水印的文件
            user_group_ids = [group.id for group in current_user.groups]
            
            if user_group_ids:
                files = File.query.filter(
                    File.group_id.in_(user_group_ids),
                    File.has_watermark == False,
                    File.file_type == 'audio'
                ).all()
            else:
                files = File.query.filter_by(
                    uploader_id=current_user.id,
                    has_watermark=False,
                    file_type='audio'
                ).all()
        
        success_count = 0
        error_count = 0
        selector = AlgorithmSelector()
        
        for file in files:
            try:
                file.processing_status = 'processing'
                db.session.commit()
                
                result = selector.select_algorithm(
                    'audio', 
                    file.original_path, 
                    form.watermark.data
                )
                
                if result['success']:
                    file.watermarked_path = result['result']
                    file.has_watermark = True
                    file.watermark_type = result['algorithm']
                    file.watermark_text = form.watermark.data
                    file.processing_status = 'completed'
                    file.error_message = None
                    success_count += 1
                else:
                    file.processing_status = 'failed'
                    file.error_message = '水印处理失败'
                    error_count += 1
                    
            except Exception as e:
                file.processing_status = 'failed'
                file.error_message = str(e)
                error_count += 1
        
        db.session.commit()
        
        if success_count > 0:
            flash(f"成功处理 {success_count} 个文件")
        if error_count > 0:
            flash(f"处理失败 {error_count} 个文件")
        
        return redirect(url_for('audio_add_watermark'))
    
    user_group_ids = [group.id for group in current_user.groups]
    if user_group_ids:
        files = File.query.filter(
            File.group_id.in_(user_group_ids),
            File.file_type == 'audio'
        ).order_by(File.created_at.desc()).all()
    else:
        files = File.query.filter_by(
            uploader_id=current_user.id,
            file_type='audio'
        ).order_by(File.created_at.desc()).all()
    
    return render_template('audio/add_watermark.html', form=form, files=files)

@app.route('/audio/extract_watermark', methods=['GET', 'POST'])
@login_required
def audio_extract_watermark():
    extracted_files = session.get('audio_extracted_files', {})
    files = File.query.filter_by(uploader_id=current_user.id, file_type='audio', has_watermark=True).all()
    return render_template('audio/extract_watermark.html', extracted_files=extracted_files, files=files)

@app.route('/audio/extract_from_file/<int:file_id>')
@login_required
def audio_extract_from_file(file_id):
    file = File.query.get_or_404(file_id)
    
    if file.uploader_id != current_user.id or file.file_type != 'audio':
        flash('您没有权限提取该文件的水印')
        return redirect(url_for('audio_extract_watermark'))
    
    if not file.has_watermark:
        flash('该文件尚未添加水印')
        return redirect(url_for('audio_extract_watermark'))
    
    if not file.watermarked_path or not os.path.exists(file.watermarked_path):
        flash(f'无法找到水印文件: {file.filename}')
        return redirect(url_for('audio_extract_watermark'))
    
    try:
        algorithm = file.watermark_type 
        selector = AlgorithmSelector()
        result = selector.extract_watermark(
            'audio', 
            file.watermarked_path, 
            algorithm=algorithm
        )
        
        # 将结果存储到session中，使用类型前缀
        extracted_files = session.get('audio_extracted_files', {})
        extracted_files[file.filename] = result
        session['audio_extracted_files'] = extracted_files
        
        flash(f"水印提取成功")
        
    except Exception as e:
        flash(f"水印提取失败: {str(e)}")
    
    # 检查是否是批量操作
    if 'selected' in request.args:
        selected_ids = request.args.get('selected').split(',')
        # 如果还有其他文件需要处理
        remaining_ids = [id for id in selected_ids if int(id) != file_id]
        if remaining_ids:
            # 继续处理下一个文件
            next_id = remaining_ids[0]
            new_selected = ','.join(remaining_ids)
            return redirect(url_for('audio_extract_from_file', file_id=next_id, selected=new_selected))
    
    return redirect(url_for('audio_extract_watermark'))

# 视频处理相关路由
@app.route('/video/process')
@login_required
def video_process():
    return render_template('video/video_process.html')

@app.route('/video/upload', methods=['GET', 'POST'])
@login_required
def video_upload():
    if request.method == 'POST':
        f = request.files.get('file')
        if not f:
            return '没有选择文件', 400
            
        if '.' not in f.filename:
            return '文件名无效', 400
        file_ext = f.filename.rsplit('.', 1)[1].lower()
        if file_ext not in ['mp4', 'avi', 'mkv', 'mov']:
            return f'不支持的视频格式: {file_ext}', 400
            
        original_filename = secure_filename_with_chinese(f.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{current_user.id}_{timestamp}_{original_filename}"
        file_path = os.path.join(get_upload_path('video'), unique_filename)
        
        try:
            f.save(file_path)
            file_size = os.path.getsize(file_path)
            mime_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
            file_hash = calculate_file_hash(file_path)
            
            if not validate_file_size(file_size, 'video'):
                os.remove(file_path)
                return '文件大小超出限制', 400
            
            file_record = File(
                filename=original_filename,
                original_path=file_path,
                file_hash=file_hash,
                file_type='video',
                file_format=file_ext,
                file_size=file_size,
                mime_type=mime_type,
                uploader_id=current_user.id,
                group_id=current_user.groups[0].id if current_user.groups else None,
                processing_status='pending'
            )
            
            db.session.add(file_record)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'file_id': file_record.id,
                'filename': original_filename,
                'file_type': 'video'
            })
            
        except Exception as e:
            return jsonify({'error': f'上传失败: {str(e)}'}), 500
    
    # 获取当前用户的文件列表
    user_group_ids = [group.id for group in current_user.groups]
    if user_group_ids:
        files = File.query.filter(
            File.group_id.in_(user_group_ids),
            File.file_type == 'video'
        ).order_by(File.created_at.desc()).all()
    else:
        files = File.query.filter_by(
            uploader_id=current_user.id,
            file_type='video'
        ).order_by(File.created_at.desc()).all()
    
    return render_template('video/upload.html', files=files)

@app.route('/video/add_watermark', methods=['GET', 'POST'])
@login_required
def video_add_watermark():
    form = WatermarkForm()
    if form.validate_on_submit():
        # 获取选中的文件ID
        selected_file_ids = request.form.get('selected_file_ids', '')
        
        if selected_file_ids:
            # 处理选中的文件
            file_ids = [int(id.strip()) for id in selected_file_ids.split(',') if id.strip()]
            files = File.query.filter(
                File.id.in_(file_ids),
                File.uploader_id == current_user.id,
                File.file_type == 'video',
                File.has_watermark == False
            ).all()
        else:
            # 处理所有未添加水印的文件
            user_group_ids = [group.id for group in current_user.groups]
            
            if user_group_ids:
                files = File.query.filter(
                    File.group_id.in_(user_group_ids),
                    File.has_watermark == False,
                    File.file_type == 'video'
                ).all()
            else:
                files = File.query.filter_by(
                    uploader_id=current_user.id,
                    has_watermark=False,
                    file_type='video'
                ).all()
        
        success_count = 0
        error_count = 0
        selector = AlgorithmSelector()
        
        for file in files:
            try:
                file.processing_status = 'processing'
                db.session.commit()
                
                result = selector.select_algorithm(
                    'video', 
                    file.original_path, 
                    form.watermark.data
                )
                
                if result['success']:
                    file.watermarked_path = result['result']
                    file.has_watermark = True
                    file.watermark_type = result['algorithm']
                    file.watermark_text = form.watermark.data
                    file.processing_status = 'completed'
                    file.error_message = None
                    success_count += 1
                else:
                    file.processing_status = 'failed'
                    file.error_message = '水印处理失败'
                    error_count += 1
                    
            except Exception as e:
                file.processing_status = 'failed'
                file.error_message = str(e)
                error_count += 1
        
        db.session.commit()
        
        if success_count > 0:
            flash(f"成功处理 {success_count} 个文件")
        if error_count > 0:
            flash(f"处理失败 {error_count} 个文件")
        
        return redirect(url_for('video_add_watermark'))
    
    user_group_ids = [group.id for group in current_user.groups]
    if user_group_ids:
        files = File.query.filter(
            File.group_id.in_(user_group_ids),
            File.file_type == 'video'
        ).order_by(File.created_at.desc()).all()
    else:
        files = File.query.filter_by(
            uploader_id=current_user.id,
            file_type='video'
        ).order_by(File.created_at.desc()).all()
    
    return render_template('video/add_watermark.html', form=form, files=files)

@app.route('/video/extract_watermark', methods=['GET', 'POST'])
@login_required
def video_extract_watermark():
    extracted_files = session.get('video_extracted_files', {})
    files = File.query.filter_by(uploader_id=current_user.id, file_type='video', has_watermark=True).all()
    return render_template('video/extract_watermark.html', extracted_files=extracted_files, files=files)

@app.route('/video/extract_from_file/<int:file_id>')
@login_required
def video_extract_from_file(file_id):
    file = File.query.get_or_404(file_id)
    
    if file.uploader_id != current_user.id or file.file_type != 'video':
        flash('您没有权限提取该文件的水印')
        return redirect(url_for('video_extract_watermark'))
    
    if not file.has_watermark:
        flash('该文件尚未添加水印')
        return redirect(url_for('video_extract_watermark'))
    
    if not file.watermarked_path or not os.path.exists(file.watermarked_path):
        flash(f'无法找到水印文件: {file.filename}')
        return redirect(url_for('video_extract_watermark'))
    
    try:
        algorithm = file.watermark_type 
        selector = AlgorithmSelector()
        result = selector.extract_watermark(
            'video', 
            file.watermarked_path, 
            algorithm=algorithm
        )
        
        # 将结果存储到session中，使用类型前缀
        extracted_files = session.get('video_extracted_files', {})
        extracted_files[file.filename] = result
        session['video_extracted_files'] = extracted_files
        
        flash(f"水印提取成功")
        
    except Exception as e:
        flash(f"水印提取失败: {str(e)}")
    
    # 检查是否是批量操作
    if 'selected' in request.args:
        selected_ids = request.args.get('selected').split(',')
        # 如果还有其他文件需要处理
        remaining_ids = [id for id in selected_ids if int(id) != file_id]
        if remaining_ids:
            # 继续处理下一个文件
            next_id = remaining_ids[0]
            new_selected = ','.join(remaining_ids)
            return redirect(url_for('video_extract_from_file', file_id=next_id, selected=new_selected))
    
    return redirect(url_for('video_extract_watermark'))

# 文档处理相关路由
@app.route('/text/process')
@login_required
def text_process():
    return render_template('text/text_process.html')

@app.route('/text/upload', methods=['GET', 'POST'])
@login_required
def text_upload():
    if request.method == 'POST':
        f = request.files.get('file')
        if not f:
            return '没有选择文件', 400
            
        if '.' not in f.filename:
            return '文件名无效', 400
        file_ext = f.filename.rsplit('.', 1)[1].lower()
        if file_ext not in ['txt', 'doc', 'docx', 'pdf']:
            return f'不支持的文档格式: {file_ext}', 400
            
        original_filename = secure_filename_with_chinese(f.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{current_user.id}_{timestamp}_{original_filename}"
        file_path = os.path.join(get_upload_path('text'), unique_filename)
        
        try:
            f.save(file_path)
            file_size = os.path.getsize(file_path)
            mime_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
            file_hash = calculate_file_hash(file_path)
            
            if not validate_file_size(file_size, 'text'):
                os.remove(file_path)
                return '文件大小超出限制', 400
            
            file_record = File(
                filename=original_filename,
                original_path=file_path,
                file_hash=file_hash,
                file_type='text',
                file_format=file_ext,
                file_size=file_size,
                mime_type=mime_type,
                uploader_id=current_user.id,
                group_id=current_user.groups[0].id if current_user.groups else None,
                processing_status='pending'
            )
            
            db.session.add(file_record)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'file_id': file_record.id,
                'filename': original_filename,
                'file_type': 'text'
            })
            
        except Exception as e:
            return jsonify({'error': f'上传失败: {str(e)}'}), 500
    
    # 获取当前用户的文件列表
    user_group_ids = [group.id for group in current_user.groups]
    if user_group_ids:
        files = File.query.filter(
            File.group_id.in_(user_group_ids),
            File.file_type == 'text'
        ).order_by(File.created_at.desc()).all()
    else:
        files = File.query.filter_by(
            uploader_id=current_user.id,
            file_type='text'
        ).order_by(File.created_at.desc()).all()
    
    return render_template('text/upload.html', files=files)

@app.route('/text/add_watermark', methods=['GET', 'POST'])
@login_required
def text_add_watermark():
    form = WatermarkForm()
    if form.validate_on_submit():
        # 获取选中的文件ID
        selected_file_ids = request.form.get('selected_file_ids', '')
        
        if selected_file_ids:
            # 处理选中的文件
            file_ids = [int(id.strip()) for id in selected_file_ids.split(',') if id.strip()]
            files = File.query.filter(
                File.id.in_(file_ids),
                File.uploader_id == current_user.id,
                File.file_type == 'text',
                File.has_watermark == False
            ).all()
        else:
            # 处理所有未添加水印的文件
            user_group_ids = [group.id for group in current_user.groups]
            
            if user_group_ids:
                files = File.query.filter(
                    File.group_id.in_(user_group_ids),
                    File.has_watermark == False,
                    File.file_type == 'text'
                ).all()
            else:
                files = File.query.filter_by(
                    uploader_id=current_user.id,
                    has_watermark=False,
                    file_type='text'
                ).all()
        
        success_count = 0
        error_count = 0
        selector = AlgorithmSelector()
        
        for file in files:
            try:
                file.processing_status = 'processing'
                db.session.commit()
                
                result = selector.select_algorithm(
                    'text', 
                    file.original_path, 
                    form.watermark.data
                )
                
                if result['success']:
                    file.watermarked_path = result['result']
                    file.has_watermark = True
                    file.watermark_type = result['algorithm']
                    file.watermark_text = form.watermark.data
                    file.processing_status = 'completed'
                    file.error_message = None
                    success_count += 1
                else:
                    file.processing_status = 'failed'
                    file.error_message = '水印处理失败'
                    error_count += 1
                    
            except Exception as e:
                file.processing_status = 'failed'
                file.error_message = str(e)
                error_count += 1
        
        db.session.commit()
        
        if success_count > 0:
            flash(f"成功处理 {success_count} 个文件")
        if error_count > 0:
            flash(f"处理失败 {error_count} 个文件")
        
        return redirect(url_for('text_add_watermark'))
    
    user_group_ids = [group.id for group in current_user.groups]
    if user_group_ids:
        files = File.query.filter(
            File.group_id.in_(user_group_ids),
            File.file_type == 'text'
        ).order_by(File.created_at.desc()).all()
    else:
        files = File.query.filter_by(
            uploader_id=current_user.id,
            file_type='text'
        ).order_by(File.created_at.desc()).all()
    
    return render_template('text/add_watermark.html', form=form, files=files)

@app.route('/text/extract_watermark', methods=['GET', 'POST'])
@login_required
def text_extract_watermark():
    extracted_files = session.get('text_extracted_files', {})
    files = File.query.filter_by(uploader_id=current_user.id, file_type='text', has_watermark=True).all()
    return render_template('text/extract_watermark.html', extracted_files=extracted_files, files=files)

@app.route('/text/extract_from_file/<int:file_id>')
@login_required
def text_extract_from_file(file_id):
    file = File.query.get_or_404(file_id)
    
    if file.uploader_id != current_user.id or file.file_type != 'text':
        flash('您没有权限提取该文件的水印')
        return redirect(url_for('text_extract_watermark'))
    
    if not file.has_watermark:
        flash('该文件尚未添加水印')
        return redirect(url_for('text_extract_watermark'))
    
    if not file.watermarked_path or not os.path.exists(file.watermarked_path):
        flash(f'无法找到水印文件: {file.filename}')
        return redirect(url_for('text_extract_watermark'))
    
    try:
        algorithm = file.watermark_type 
        selector = AlgorithmSelector()
        result = selector.extract_watermark(
            'text', 
            file.watermarked_path, 
            algorithm=algorithm
        )
        
        # 将结果存储到session中，使用类型前缀
        extracted_files = session.get('text_extracted_files', {})
        extracted_files[file.filename] = result
        session['text_extracted_files'] = extracted_files
        
        flash(f"水印提取成功")
        
    except Exception as e:
        flash(f"水印提取失败: {str(e)}")
    
    # 检查是否是批量操作
    if 'selected' in request.args:
        selected_ids = request.args.get('selected').split(',')
        # 如果还有其他文件需要处理
        remaining_ids = [id for id in selected_ids if int(id) != file_id]
        if remaining_ids:
            # 继续处理下一个文件
            next_id = remaining_ids[0]
            new_selected = ','.join(remaining_ids)
            return redirect(url_for('text_extract_from_file', file_id=next_id, selected=new_selected))
    
    return redirect(url_for('text_extract_watermark'))