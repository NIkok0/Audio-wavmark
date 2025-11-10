# Standard library imports
import hashlib
import mimetypes
import os
import random
import re
import shutil
from datetime import datetime, timedelta
from watermark.utils.time_provider import get_now_utc

# Third-party imports
from flask import (
    abort, current_app, flash as flask_flash, jsonify, redirect, render_template,
    request, send_file, session, url_for
)
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

# Local imports
from watermark import app, db
from watermark.forms.login_form import LoginForm
from watermark.forms.register_form import RegisterForm
from watermark.forms.watermark_form import WatermarkForm
from watermark.models import File, Group, User
from watermark.utils.algorithm_selector import AlgorithmSelector
from watermark.utils.file_config import (
    get_file_size_info, get_file_type_by_extension, validate_file_size,format_file_size
)

# 统一封装 flash，记录触发位置，便于排查登录后首页出现的错误提示
def flash(message, category='info'):
    try:
        user_id = getattr(current_user, 'id', None)
        username = getattr(current_user, 'username', None)
        current_app.logger.info(
            'FLASH category=%s message=%s endpoint=%s path=%s referrer=%s user_id=%s username=%s',
            category, str(message), request.endpoint, request.path, request.referrer, user_id, username
        )
    except Exception:
        # 日志记录失败不影响原有逻辑
        pass
    return flask_flash(message, category)

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

from watermark.utils.path_utils import (
    get_user_dated_upload_dir,
    get_user_dated_embed_dir,
    get_user_dated_extract_dir,
)

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

def handle_file_upload(file, media_type, save_to_temp=True):
    """
    处理文件上传的通用函数
    
    Args:
        file: 上传的文件对象
        media_type: 媒体类型 (image/video/audio/text)
        save_to_temp: 是否保存到临时目录（True）还是最终目录（False）
    
    Returns:
        tuple: (file_path, error_message, file_info)
        - file_path: 保存的文件路径
        - error_message: 错误消息（如果有），否则为None
        - file_info: 文件信息字典，包含 file_size, mime_type, file_hash, file_format, filename, unique_filename
    """
    if not file:
        return None, "没有选择文件", None
    
    filename = secure_filename_with_chinese(file.filename)
    extension = os.path.splitext(filename)[1][1:].lower()
    
    # 验证文件类型
    file_type = get_file_type_by_extension(extension)
    if not file_type or file_type != media_type:
        return None, f"不支持的文件类型: {extension}", None
    
    # 验证文件大小
    if not validate_file_size(file.content_length, extension):
        size_info = get_file_size_info(extension)
        max_size = size_info['max_size'] if size_info else "未知"
        return None, f"文件大小超过限制 (最大: {format_file_size(max_size)})", None
    
    # 生成唯一文件名
    timestamp = get_now_utc().strftime('%Y%m%d_%H%M%S')
    unique_filename = f"{timestamp}_{filename}"
    
    # 根据 save_to_temp 决定保存路径
    if save_to_temp:
        # 保存到临时目录
        file_path = os.path.join(temp_dir, unique_filename)
    else:
        # 保存到最终目录
        upload_path = get_user_dated_upload_dir(media_type)
        file_path = os.path.join(upload_path, unique_filename)
    
    try:
        file.save(file_path)
        # 获取文件信息
        file_size = os.path.getsize(file_path)
        mime_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
        file_hash = calculate_file_hash(file_path)
        return file_path, None, {
            'file_size': file_size,
            'mime_type': mime_type,
            'file_hash': file_hash,
            'file_format': extension,
            'filename': filename,
            'unique_filename': unique_filename
        }
    except Exception as e:
        return None, f"文件保存失败: {str(e)}", None

def move_file_to_final_location(temp_path, media_type, filename):
    """
    将临时文件移动到最终位置（upload目录）
    
    Args:
        temp_path: 临时文件路径
        media_type: 媒体类型
        filename: 文件名
    
    Returns:
        str: 最终文件路径，如果移动失败返回 None
    """
    try:
        upload_path = get_user_dated_upload_dir(media_type)
        final_path = os.path.join(upload_path, filename)
        
        # 确保目标目录存在
        os.makedirs(os.path.dirname(final_path), exist_ok=True)
        
        # 移动文件
        import shutil
        shutil.move(temp_path, final_path)
        return final_path
    except Exception as e:
        print(f"移动文件失败: {str(e)}")
        return None

def move_file_to_embed_location(temp_path, media_type, filename):
    """
    将临时文件移动到embed目录（用于已加水印的文件）
    
    Args:
        temp_path: 临时文件路径
        media_type: 媒体类型
        filename: 文件名
    
    Returns:
        str: 最终文件路径，如果移动失败返回 None
    """
    try:
        embed_path = get_user_dated_embed_dir(media_type)
        final_path = os.path.join(embed_path, filename)
        
        # 确保目标目录存在
        os.makedirs(os.path.dirname(final_path), exist_ok=True)
        
        # 移动文件
        import shutil
        shutil.move(temp_path, final_path)
        return final_path
    except Exception as e:
        print(f"移动文件到embed目录失败: {str(e)}")
        return None

def process_watermark(file_path, watermark_text, operation_type='embed', file_id=None,random_seed=None):
    """处理水印的通用函数"""
    try:
        selector = AlgorithmSelector()
        if operation_type == 'embed':
            if random_seed:
                result = selector.select_algorithm(file_path, watermark_text,random_seed)
                return result.get('result'), result.get('algorithm'), None,result.get('watermark_hash')
            else:
                result = selector.select_algorithm(file_path, watermark_text)
                return result.get('result'), result.get('algorithm'), None
        else:  # extract
            file_record = File.query.get(file_id)
            if random_seed:
                # 使用存储的算法提取水印
                print("use this")
                extracted_text = selector.extract_watermark(file_path, file_record.watermark_type,watermark_seed=random_seed,watermark_text=file_record.watermark_text,original_watermark_text=file_record.original_watermark_text)
            else:
                extracted_text = selector.extract_watermark(file_path, file_record.watermark_type)
            # 确保返回的是字符串类型
            if extracted_text is not None:
                # 如果是numpy数组，转换为字符串
                if hasattr(extracted_text, 'tolist'):
                    extracted_text = str(extracted_text.tolist())
                # 如果是bytes，解码为字符串
                elif isinstance(extracted_text, bytes):
                    try:
                        extracted_text = extracted_text.decode('utf-8')
                    except UnicodeDecodeError:
                        extracted_text = str(extracted_text)
                # 如果是其他类型，转换为字符串
                elif not isinstance(extracted_text, str):
                    extracted_text = str(extracted_text)
            return extracted_text, None, None
    except Exception as e:
        return None, None, str(e)

def process_watermark_try_all_algorithms(file_path):
    """尝试所有算法提取水印"""
    try:
        selector = AlgorithmSelector()
        extracted_text, algorithm, attempt_results = selector.extract_watermark_try_all(file_path)
        
        # 确保返回的是字符串类型
        if extracted_text is not None:
            # 如果是numpy数组，转换为字符串
            if hasattr(extracted_text, 'tolist'):
                extracted_text = str(extracted_text.tolist())
            # 如果是bytes，解码为字符串
            elif isinstance(extracted_text, bytes):
                try:
                    extracted_text = extracted_text.decode('utf-8')
                except UnicodeDecodeError:
                    extracted_text = str(extracted_text)
            # 如果是其他类型，转换为字符串
            elif not isinstance(extracted_text, str):
                extracted_text = str(extracted_text)
        
        return extracted_text, algorithm, None, attempt_results
    except Exception as e:
        # 如果异常包含 attempt_results，提取出来
        attempt_results = []
        if hasattr(e, 'args') and len(e.args) > 1:
            attempt_results = e.args[1]
        return None, None, str(e.args[0] if hasattr(e, 'args') and e.args else e), attempt_results

def get_user_files(user, file_type, has_watermark=None):
    """获取用户的文件列表"""
    # 获取用户所在的组
    user_group_ids = [group.id for group in user.groups]
    
    # 构建基本查询
    query = File.query.filter_by(file_type=file_type)
    
    # 如果指定了水印状态，添加过滤条件
    if has_watermark is not None:
        query = query.filter_by(has_watermark=has_watermark)
    
    # 根据用户组或用户ID过滤
    if user_group_ids:
        query = query.filter(
            (File.group_id.in_(user_group_ids)) |
            (File.uploader_id == user.id)
        )
    else:
        query = query.filter_by(uploader_id=user.id)
    
    # 按创建时间降序排序
    return query.order_by(File.created_at.desc()).all()

def get_user_files_pagination(user, file_type, has_watermark=None, page=1, per_page=5):
    """获取用户的文件列表（分页版本）"""
    # 获取用户所在的组
    user_group_ids = [group.id for group in user.groups]
    
    # 构建基本查询
    query = File.query.filter_by(file_type=file_type)
    
    # 如果指定了水印状态，添加过滤条件
    if has_watermark is not None:
        query = query.filter_by(has_watermark=has_watermark)
    
    # 根据用户组或用户ID过滤
    if user_group_ids:
        query = query.filter(
            (File.group_id.in_(user_group_ids)) |
            (File.uploader_id == user.id)
        )
    else:
        query = query.filter_by(uploader_id=user.id)
    
    # 按创建时间降序排序并分页
    return query.order_by(File.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

def get_user_all_files_pagination(user, has_watermark=None, page=1, per_page=5):
    """获取用户的文件列表（不区分类型，分页版本）

    - 可见范围：本人上传 + 所在组文件
    - 可按是否已添加水印过滤
    - 创建时间倒序
    """
    user_group_ids = [group.id for group in user.groups]

    query = File.query

    if has_watermark is not None:
        query = query.filter_by(has_watermark=has_watermark)

    if user_group_ids:
        query = query.filter(
            (File.group_id.in_(user_group_ids)) |
            (File.uploader_id == user.id)
        )
    else:
        query = query.filter_by(uploader_id=user.id)

    return query.order_by(File.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

#主页
@app.route('/', methods=['GET', 'POST'])
def index():
    # 全局统计
    total_files = File.query.count()
    total_size = db.session.query(db.func.coalesce(db.func.sum(File.file_size), 0)).scalar()
    total_size_value = int(total_size or 0)
    total_size_str = format_file_size(total_size_value)

    types = ['image', 'audio', 'video', 'text']
    type_counts = {t: File.query.filter_by(file_type=t).count() for t in types}
    type_labels = ['图片', '音频', '视频', '文档']
    type_values = [type_counts[t] for t in types]

    watermarked_count = File.query.filter_by(has_watermark=True).count()
    non_watermarked_count = total_files - watermarked_count

    recent_files = File.query.order_by(File.created_at.desc()).limit(5).all()

    # 最近14天按天统计
    days = 14
    start_date = get_now_utc() - timedelta(days=days - 1)
    grouped = (
        db.session.query(db.func.date(File.created_at).label('d'), db.func.count(File.id))
        .filter(File.created_at >= start_date)
        .group_by(db.func.date(File.created_at))
        .all()
    )
    count_map = {str(d): c for d, c in grouped}
    timeseries_labels = []
    timeseries_counts = []
    for i in range(days):
        day = (start_date + timedelta(days=i))
        key = str(day.date())
        timeseries_labels.append(day.strftime('%m-%d'))
        timeseries_counts.append(int(count_map.get(key, 0)))

    # 如果已登录，提供个人统计与个人可视化数据
    user_stats = None
    user_recent_files = []
    user_type_labels = []
    user_type_values = []
    user_timeseries_labels = []
    user_timeseries_counts = []
    if current_user.is_authenticated:
        user_total = File.query.filter_by(uploader_id=current_user.id).count()
        user_watermarked = File.query.filter_by(uploader_id=current_user.id, has_watermark=True).count()
        user_size = db.session.query(db.func.coalesce(db.func.sum(File.file_size), 0)).filter(File.uploader_id == current_user.id).scalar()
        user_size_value = int(user_size or 0)
        user_stats = {
            'total': user_total,
            'watermarked': user_watermarked,
            'non_watermarked': user_total - user_watermarked,
            'total_size_str': format_file_size(user_size_value)
        }

        # 最近文件（仅本人）
        user_recent_files = (
            File.query.filter_by(uploader_id=current_user.id)
            .order_by(File.created_at.desc())
            .limit(5)
            .all()
        )

        # 类型分布（仅本人）
        user_types = ['image', 'audio', 'video', 'text']
        user_type_labels = ['图片', '音频', '视频', '文档']
        user_type_values = [
            File.query.filter_by(uploader_id=current_user.id, file_type=t).count()
            for t in user_types
        ]

        # 最近14天上传趋势（仅本人）
        u_grouped = (
            db.session.query(db.func.date(File.created_at).label('d'), db.func.count(File.id))
            .filter(File.uploader_id == current_user.id, File.created_at >= start_date)
            .group_by(db.func.date(File.created_at))
            .all()
        )
        u_count_map = {str(d): c for d, c in u_grouped}
        for i in range(days):
            dday = (start_date + timedelta(days=i))
            ukey = str(dday.date())
            user_timeseries_labels.append(dday.strftime('%m-%d'))
            user_timeseries_counts.append(int(u_count_map.get(ukey, 0)))

        # 首页个人文件分页（不区分类型）
        unwatermarked_page = request.args.get('unwatermarked_page', 1, type=int)
        watermarked_page = request.args.get('watermarked_page', 1, type=int)
        all_uploaded_page = request.args.get('all_uploaded_page', 1, type=int)
        
        # 获取所有已上传的文件（不论是否加水印）
        user_all_uploaded_pagination = get_user_all_files_pagination(
            current_user, has_watermark=None, page=all_uploaded_page, per_page=5
        )
        user_watermarked_pagination = get_user_all_files_pagination(
            current_user, has_watermark=True, page=watermarked_page, per_page=5
        )
    else:
        user_all_uploaded_pagination = None
        user_watermarked_pagination = None

    return render_template(
        'index.html',
        total_files=total_files,
        total_size_str=total_size_str,
        watermarked_count=watermarked_count,
        non_watermarked_count=non_watermarked_count,
        type_counts=type_counts,
        recent_files=recent_files,
        user_stats=user_stats,
        format_file_size=format_file_size,
        timeseries_labels=timeseries_labels,
        timeseries_counts=timeseries_counts,
        user_recent_files=user_recent_files,
        user_type_labels=user_type_labels,
        user_type_values=user_type_values,
        user_timeseries_labels=user_timeseries_labels,
        user_timeseries_counts=user_timeseries_counts,
        user_all_uploaded_pagination=user_all_uploaded_pagination,
        user_watermarked_pagination=user_watermarked_pagination
        , type_labels=type_labels
        , type_values=type_values
    )

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
        # 优先下载已加水印文件；若不存在则回退为原始文件
        target_path = file.watermarked_path or file.original_path
        if not target_path:
            flash('未找到可下载的文件路径')
            return redirect(url_for('index'))

        # 如为相对路径则补齐为绝对路径
        if not os.path.isabs(target_path):
            root_dir = os.path.abspath(os.path.join(current_app.root_path, '..'))
            target_path = os.path.join(root_dir, target_path)

        if not os.path.exists(target_path):
            flash('文件不存在或已被移除')
            return redirect(url_for('index'))

        return send_file(
            target_path,
            download_name=file.filename,
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
    
    # 使用统一的session键名
    session_key = 'extracted_watermarks'
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
    
    # 使用统一的session键名
    session_key = 'extracted_watermarks'
    session[session_key] = {}
    
    return redirect(request.referrer)

# # 计算相似度
# def calculate_similarity(str1, str2):
#     """计算两个字符串的相似度"""
#     def levenshtein_distance(s1, s2):
#         if len(s1) < len(s2):
#             return levenshtein_distance(s2, s1)
#         if len(s2) == 0:
#             return len(s1)
#         previous_row = list(range(len(s2) + 1))
#         for i, c1 in enumerate(s1):
#             current_row = [i + 1]
#             for j, c2 in enumerate(s2):
#                 insertions = previous_row[j + 1] + 1
#                 deletions = current_row[j] + 1
#                 substitutions = previous_row[j] + (c1 != c2)
#                 current_row.append(min(insertions, deletions, substitutions))
#             previous_row = current_row
#         return previous_row[-1]
    
#     if not str1 or not str2:
#         return 0.0
    
#     distance = levenshtein_distance(str1, str2)
#     max_len = max(len(str1), len(str2))
#     similarity = 1 - (distance / max_len)
#     return similarity

# 图片处理相关路由
@app.route('/image/process')
@login_required
def image_process():
    return render_template('image/image_process.html')

@app.route('/image/upload', methods=['GET', 'POST'])
@login_required
def image_upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': '没有文件被上传'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'})
        
        # 先保存到临时目录进行检查
        temp_file_path, error, file_info = handle_file_upload(file, 'image', save_to_temp=True)
        if error:
            return jsonify({'error': error})

        final_file_path = move_file_to_final_location(
            temp_file_path, 'image', file_info['unique_filename']
        )

        if not final_file_path:
            try:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
            except Exception:
                pass
            return jsonify({'error': '文件移动失败'})

        try:
            file_record = File(
                filename=file_info['filename'],
                original_path=final_file_path,
                file_hash=file_info['file_hash'],
                file_type='image',
                file_format=file_info['file_format'],
                file_size=file_info['file_size'],
                mime_type=file_info['mime_type'],
                uploader_id=current_user.id,
                group_id=current_user.groups[0].id if current_user.groups else None,
                processing_status='pending',
                has_watermark=False
            )
            db.session.add(file_record)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            try:
                if os.path.exists(final_file_path):
                    os.remove(final_file_path)
            except Exception:
                pass
            return jsonify({'error': f'保存文件记录失败: {str(e)}'})

        return jsonify({
            'success': True,
            'message': '文件上传成功',
            'file_id': file_record.id,
            'file_type': 'image',
            'has_watermark': False,
            'filename': file_info['filename']
        })
    
    # 获取用户的图片文件列表（分页，分未加水印/已加水印）
    page = request.args.get('page', 1, type=int)
    watermarked_page = request.args.get('watermarked_page', 1, type=int)
    per_page = 5
    unwatermarked_pagination = get_user_files_pagination(
        current_user, 'image', has_watermark=False, page=page, per_page=per_page
    )
    watermarked_pagination = get_user_files_pagination(
        current_user, 'image', has_watermark=True, page=watermarked_page, per_page=per_page
    )
    return render_template(
        'image/upload.html',
        unwatermarked_pagination=unwatermarked_pagination,
        watermarked_pagination=watermarked_pagination
    )

@app.route('/image/add_watermark', methods=['GET', 'POST'])
@login_required
def image_add_watermark():
    form = WatermarkForm()
    if form.validate_on_submit():
        # 获取选中的文件ID
        selected_file_ids = request.form.get('selected_file_ids', '')
        
        if not selected_file_ids or not selected_file_ids.strip():
            flash('请先选择要添加水印的文件', 'error')
            return redirect(url_for('image_add_watermark'))
        
        # 处理选中的文件
        file_ids = [int(id.strip()) for id in selected_file_ids.split(',') if id.strip()]
        
        if not file_ids:
            flash('请先选择要添加水印的文件', 'error')
            return redirect(url_for('image_add_watermark'))
        
        files = File.query.filter(
            File.id.in_(file_ids),
            File.uploader_id == current_user.id,
            File.file_type == 'image',
            File.has_watermark == False
        ).all()
        
        if not files:
            flash('未找到可处理的文件', 'error')
            return redirect(url_for('image_add_watermark'))
        
        success_count = 0
        error_count = 0
        error_details = []  # 收集错误详情
        
        for file in files:
            try:
                file.processing_status = 'processing'
                db.session.commit()
                
                result, algorithm, error = process_watermark(
                    file.original_path,
                    form.watermark.data,
                    'embed'
                )
                
                if result and not error:
                    # 创建新的文件记录表示已添加水印的版本
                    watermarked_file = File(
                        filename=file.filename,
                        original_path=file.original_path,  # 保持相同的原始路径引用
                        watermarked_path=result,
                        file_hash=file.file_hash,  # 复制原文件的hash
                        file_watermark_hash=calculate_file_hash(result),
                        file_type=file.file_type,
                        file_format=file.file_format,
                        file_size=file.file_size,
                        mime_type=file.mime_type,  # 复制mime_type
                        uploader_id=current_user.id,
                        has_watermark=True,
                        watermark_type=algorithm,
                        watermark_text=form.watermark.data,
                        processing_status='completed',
                        error_message=None
                    )
                    db.session.add(watermarked_file)
                    
                    # 原文件保持 has_watermark=False，只更新处理状态
                    file.processing_status = 'completed'
                    file.error_message = None
                    success_count += 1
                else:
                    error_message = error or '水印处理失败'
                    file.processing_status = 'failed'
                    file.error_message = error_message
                    error_count += 1
                    error_details.append({
                        'filename': file.filename,
                        'error': error_message
                    })
                    
            except Exception as e:
                error_message = str(e)
                file.processing_status = 'failed'
                file.error_message = error_message
                error_count += 1
                error_details.append({
                    'filename': file.filename,
                    'error': error_message
                })
        
        db.session.commit()
        
        # 将结果存储到 session 中
        session['embed_result'] = {
            'success_count': success_count,
            'error_count': error_count,
            'error_details': error_details,
            'total_count': len(files)
        }
        
        return redirect(url_for('image_add_watermark'))
    
    # 获取分页参数
    page = request.args.get('page', 1, type=int)
    per_page = 5  # 每页5条数据
    
    # 获取未添加水印的文件
    unwatermarked_pagination = get_user_files_pagination(
        current_user, 'image', has_watermark=False, page=page, per_page=per_page
    )
    
    # 获取已添加水印的文件  
    watermarked_page = request.args.get('watermarked_page', 1, type=int)
    watermarked_pagination = get_user_files_pagination(
        current_user, 'image', has_watermark=True, page=watermarked_page, per_page=per_page
    )
    
    # 获取嵌入结果并清除
    embed_result = session.pop('embed_result', None)
    
    return render_template('image/add_watermark.html', 
                         form=form, 
                         unwatermarked_pagination=unwatermarked_pagination,
                         watermarked_pagination=watermarked_pagination,
                         embed_result=embed_result)

@app.route('/image/extract_watermark', methods=['GET', 'POST'])
@login_required
def image_extract_watermark():
    if request.method == 'POST':
        # 处理批量提取
        selected_file_ids = request.form.getlist('selected_files')
        if selected_file_ids:
            results = {}
            for file_id in selected_file_ids:
                try:
                    file_record = File.query.get(file_id)
                    if not file_record or file_record.uploader_id != current_user.id:
                        continue
                    
                    # 提取水印
                    extracted_text, _, error = process_watermark(
                        file_record.watermarked_path,
                        None,
                        'extract',
                        file_id # 传递文件ID
                    )
                    
                    if not error:
                        results[file_record.filename] = extracted_text
                    
                except Exception as e:
                    continue
            
            # 将结果存储到session中
            session['extracted_watermarks'] = results
            return redirect(url_for('image_extract_watermark'))
        
        # 处理单个文件上传提取
        if 'file' not in request.files:
            return jsonify({'error': '没有文件被上传'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'})
        
        # 使用通用文件上传处理函数
        file_path, error, _ = handle_file_upload(file, 'image')
        if error:
            return jsonify({'error': error})
        
        # 提取水印
        extracted_text, _, error = process_watermark(file_path, None, 'extract')
        
        if error:
            return jsonify({'error': f'水印提取失败: {error}'})
        
        return jsonify({
            'success': True,
            'extracted_text': extracted_text
        })
    
    # 获取未添加水印的文件列表（待处理的文件）
    page = request.args.get('page', 1, type=int)
    per_page = 5
    unwatermarked_pagination = get_user_files_pagination(
        current_user, 'image', has_watermark=False, page=page, per_page=per_page
    )
    
    # 获取已添加水印的文件列表（分页）
    watermarked_pagination = get_user_files_pagination(
        current_user, 'image', has_watermark=True, page=page, per_page=per_page
    )
    
    # 获取之前的提取结果
    extracted_watermarks = session.pop('extracted_watermarks', {})
    
    return render_template('image/extract_watermark.html',
                         unwatermarked_pagination=unwatermarked_pagination,
                         watermarked_pagination=watermarked_pagination,
                         extracted_watermarks=extracted_watermarks)

@app.route('/image/extract_from_file/<int:file_id>')
@login_required
def image_extract_from_file(file_id):
    # 获取文件记录
    file_record = File.query.get_or_404(file_id)
    if file_record.uploader_id != current_user.id:
        return jsonify({'error': '您没有权限处理该文件'})
    
    # 提取水印
    extracted_text, _, error = process_watermark(
        file_record.watermarked_path,
        None,
        'extract',
        file_id # 传递文件ID
    )
    
    if error:
        return jsonify({'error': f'水印提取失败: {error}'})
    
    return jsonify({
        'success': True,
        'extracted_text': extracted_text
    })

@app.route('/image/extract_from_unwatermarked_file/<int:file_id>')
@login_required
def image_extract_from_unwatermarked_file(file_id):
    # 获取文件记录
    file_record = File.query.get_or_404(file_id)
    if file_record.uploader_id != current_user.id:
        return jsonify({'error': '您没有权限处理该文件'})
    
    # 尝试所有算法从原始文件提取水印
    extracted_text, algorithm, error, attempt_results = process_watermark_try_all_algorithms(
        file_record.original_path
    )
    
    if error:
        return jsonify({
            'error': f'水印提取失败: {error}',
            'attempt_results': attempt_results
        })
    
    # 成功提取水印后，将文件复制到 embed 文件夹，并创建一个已添加水印的文件记录
    try:
        # 获取用户的 embed 目录
        user_embed_dir = get_user_dated_embed_dir(current_user.username, 'image')
        
        # 生成唯一的文件名（保持原始扩展名）
        file_ext = os.path.splitext(file_record.filename)[1]
        unique_filename = f"{file_record.file_hash}_embed{file_ext}"
        embed_file_path = os.path.join(user_embed_dir, unique_filename)
        
        # 复制文件到 embed 目录
        shutil.copy2(file_record.original_path, embed_file_path)
        
        watermarked_file = File(
            filename=file_record.filename,
            original_path=file_record.original_path,
            watermarked_path=embed_file_path,  # 使用 embed 目录下的路径
            file_hash=file_record.file_hash,
            file_watermark_hash=file_record.file_hash,
            file_type=file_record.file_type,
            file_format=file_record.file_format,
            file_size=file_record.file_size,
            mime_type=file_record.mime_type,
            uploader_id=current_user.id,
            has_watermark=True,
            watermark_type=algorithm or 'Unknown',
            watermark_text=extracted_text,
            processing_status='completed'
        )
        db.session.add(watermarked_file)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error creating watermarked file record: {e}")
    
    return jsonify({
        'success': True,
        'extracted_text': extracted_text,
        'algorithm': algorithm,
        'attempt_results': attempt_results
    })

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
        if file_ext not in ['mp3', 'wav', 'flac', 'aac', 'ogg']:
            return f'不支持的音频格式: {file_ext}', 400
            
        # 先保存到临时目录进行检查
        temp_file_path, error, file_info = handle_file_upload(f, 'audio', save_to_temp=True)
        if error:
            return jsonify({'error': error}), 400

        final_file_path = move_file_to_final_location(
            temp_file_path, 'audio', file_info['unique_filename']
        )

        if not final_file_path:
            try:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
            except Exception:
                pass
            return jsonify({'error': '文件移动失败'}), 500

        try:
            file_record = File(
                filename=file_info['filename'],
                original_path=final_file_path,
                file_hash=file_info['file_hash'],
                file_type='audio',
                file_format=file_info['file_format'],
                file_size=file_info['file_size'],
                mime_type=file_info['mime_type'],
                uploader_id=current_user.id,
                group_id=current_user.groups[0].id if current_user.groups else None,
                processing_status='pending',
                has_watermark=False
            )

            db.session.add(file_record)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            try:
                if os.path.exists(final_file_path):
                    os.remove(final_file_path)
            except Exception:
                pass
            return jsonify({'error': f'保存文件记录失败: {str(e)}'}), 500

        return jsonify({
            'success': True,
            'message': '文件上传成功',
            'file_id': file_record.id,
            'filename': file_info['filename'],
            'file_type': 'audio',
            'has_watermark': False
        })
        
    
    # 获取用户的音频文件列表（分页，分未加水印/已加水印）
    page = request.args.get('page', 1, type=int)
    watermarked_page = request.args.get('watermarked_page', 1, type=int)
    per_page = 5
    unwatermarked_pagination = get_user_files_pagination(
        current_user, 'audio', has_watermark=False, page=page, per_page=per_page
    )
    watermarked_pagination = get_user_files_pagination(
        current_user, 'audio', has_watermark=True, page=watermarked_page, per_page=per_page
    )
    return render_template(
        'audio/upload.html',
        unwatermarked_pagination=unwatermarked_pagination,
        watermarked_pagination=watermarked_pagination
    )

@app.route('/audio/add_watermark', methods=['GET', 'POST'])
@login_required
def audio_add_watermark():
    form = WatermarkForm()
    if form.validate_on_submit():
        # 获取选中的文件ID
        selected_file_ids = request.form.get('selected_file_ids', '')
        
        if not selected_file_ids or not selected_file_ids.strip():
            flash('请先选择要添加水印的文件', 'error')
            return redirect(url_for('audio_add_watermark'))
        
        # 处理选中的文件
        file_ids = [int(id.strip()) for id in selected_file_ids.split(',') if id.strip()]
        
        if not file_ids:
            flash('请先选择要添加水印的文件', 'error')
            return redirect(url_for('audio_add_watermark'))
        
        files = File.query.filter(
            File.id.in_(file_ids),
            File.uploader_id == current_user.id,
            File.file_type == 'audio',
            File.has_watermark == False
        ).all()
        
        if not files:
            flash('未找到可处理的文件', 'error')
            return redirect(url_for('audio_add_watermark'))
        
        success_count = 0
        error_count = 0
        error_details = []
        
        for file in files:
            try:
                file.processing_status = 'processing'
                db.session.commit()
                
                result, algorithm, error = process_watermark(
                    file.original_path,
                    form.watermark.data,
                    'embed'
                )
                
                if result and not error:
                    # 创建新的文件记录表示已添加水印的版本
                    watermarked_file = File(
                        filename=file.filename,
                        original_path=file.original_path,  # 保持相同的原始路径引用
                        watermarked_path=result,
                        file_hash=file.file_hash,  # 复制原文件的hash
                        file_watermark_hash=calculate_file_hash(result),
                        file_type=file.file_type,
                        file_format=file.file_format,
                        file_size=file.file_size,
                        mime_type=file.mime_type,  # 复制mime_type
                        uploader_id=current_user.id,
                        has_watermark=True,
                        watermark_type=algorithm,
                        watermark_text=form.watermark.data,
                        processing_status='completed',
                        error_message=None
                    )
                    db.session.add(watermarked_file)
                    
                    # 原文件保持 has_watermark=False，只更新处理状态
                    file.processing_status = 'completed'
                    file.error_message = None
                    success_count += 1
                else:
                    error_message = error or '水印处理失败'
                    file.processing_status = 'failed'
                    file.error_message = error_message
                    error_count += 1
                    error_details.append({
                        'filename': file.filename,
                        'error': error_message
                    })
                    
            except Exception as e:
                error_message = str(e)
                file.processing_status = 'failed'
                file.error_message = error_message
                error_count += 1
                error_details.append({
                    'filename': file.filename,
                    'error': error_message
                })
        
        db.session.commit()
        
        # 将结果存储到 session 中
        session['embed_result'] = {
            'success_count': success_count,
            'error_count': error_count,
            'error_details': error_details,
            'total_count': len(files)
        }
        
        return redirect(url_for('audio_add_watermark'))
    
    # 获取分页参数
    page = request.args.get('page', 1, type=int)
    per_page = 5  # 每页5条数据
    
    # 获取未添加水印的文件
    unwatermarked_pagination = get_user_files_pagination(
        current_user, 'audio', has_watermark=False, page=page, per_page=per_page
    )
    
    # 获取已添加水印的文件  
    watermarked_page = request.args.get('watermarked_page', 1, type=int)
    watermarked_pagination = get_user_files_pagination(
        current_user, 'audio', has_watermark=True, page=watermarked_page, per_page=per_page
    )
    
    # 获取嵌入结果并清除
    embed_result = session.pop('embed_result', None)
    
    return render_template('audio/add_watermark.html', 
                         form=form, 
                         unwatermarked_pagination=unwatermarked_pagination,
                         watermarked_pagination=watermarked_pagination,
                         embed_result=embed_result)

@app.route('/audio/extract_watermark', methods=['GET', 'POST'])
@login_required
def audio_extract_watermark():
    if request.method == 'POST':
        # 处理批量提取
        selected_file_ids = request.form.getlist('selected_files')
        if selected_file_ids:
            results = {}
            for file_id in selected_file_ids:
                try:
                    file_record = File.query.get(file_id)
                    if not file_record or file_record.uploader_id != current_user.id:
                        continue
                    
                    # 提取水印
                    extracted_text, _, error = process_watermark(
                        file_record.watermarked_path,
                        None,
                        'extract',
                        file_id # 传递文件ID
                    )
                    
                    if not error:
                        results[file_record.filename] = extracted_text
                    
                except Exception as e:
                    continue
            
            # 将结果存储到session中
            session['extracted_watermarks'] = results
            return redirect(url_for('audio_extract_watermark'))
        
        # 处理单个文件上传提取
        if 'file' not in request.files:
            return jsonify({'error': '没有文件被上传'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'})
        
        # 使用通用文件上传处理函数
        file_path, error, _ = handle_file_upload(file, 'audio')
        if error:
            return jsonify({'error': error})
        
        # 提取水印
        extracted_text, _, error = process_watermark(file_path, None, 'extract')
        
        if error:
            return jsonify({'error': f'水印提取失败: {error}'})
        
        return jsonify({
            'success': True,
            'extracted_text': extracted_text
        })
    
    # 获取未添加水印的文件列表（待处理的文件）
    page = request.args.get('page', 1, type=int)
    per_page = 5
    unwatermarked_pagination = get_user_files_pagination(
        current_user, 'audio', has_watermark=False, page=page, per_page=per_page
    )
    
    # 获取已添加水印的文件列表（分页）
    watermarked_pagination = get_user_files_pagination(
        current_user, 'audio', has_watermark=True, page=page, per_page=per_page
    )
    
    # 获取之前的提取结果
    extracted_watermarks = session.pop('extracted_watermarks', {})
    
    return render_template('audio/extract_watermark.html',
                         unwatermarked_pagination=unwatermarked_pagination,
                         watermarked_pagination=watermarked_pagination,
                         extracted_watermarks=extracted_watermarks)

@app.route('/audio/extract_from_file/<int:file_id>')
@login_required
def audio_extract_from_file(file_id):
    # 获取文件记录
    file_record = File.query.get_or_404(file_id)
    if file_record.uploader_id != current_user.id:
        return jsonify({'error': '您没有权限处理该文件'})
    
    # 提取水印
    extracted_text, _, error = process_watermark(
        file_record.watermarked_path,
        None,
        'extract',
        file_id # 传递文件ID
    )
    
    if error:
        return jsonify({'error': f'水印提取失败: {error}'})
    
    return jsonify({
        'success': True,
        'extracted_text': extracted_text
    })

@app.route('/audio/extract_from_unwatermarked_file/<int:file_id>')
@login_required
def audio_extract_from_unwatermarked_file(file_id):
    # 获取文件记录
    file_record = File.query.get_or_404(file_id)
    if file_record.uploader_id != current_user.id:
        return jsonify({'error': '您没有权限处理该文件'})
    
    # 尝试所有算法从原始文件提取水印
    extracted_text, algorithm, error, attempt_results = process_watermark_try_all_algorithms(
        file_record.original_path
    )
    
    if error:
        return jsonify({
            'error': f'水印提取失败: {error}',
            'attempt_results': attempt_results
        })
    
    # 成功提取水印后，将文件复制到 embed 文件夹，并创建一个已添加水印的文件记录
    try:
        # 获取用户的 embed 目录
        user_embed_dir = get_user_dated_embed_dir(current_user.username, 'audio')
        
        # 生成唯一的文件名（保持原始扩展名）
        file_ext = os.path.splitext(file_record.filename)[1]
        unique_filename = f"{file_record.file_hash}_embed{file_ext}"
        embed_file_path = os.path.join(user_embed_dir, unique_filename)
        
        # 复制文件到 embed 目录
        shutil.copy2(file_record.original_path, embed_file_path)
        
        watermarked_file = File(
            filename=file_record.filename,
            original_path=file_record.original_path,
            watermarked_path=embed_file_path,  # 使用 embed 目录下的路径
            file_hash=file_record.file_hash,
            file_watermark_hash=file_record.file_hash,
            file_type=file_record.file_type,
            file_format=file_record.file_format,
            file_size=file_record.file_size,
            mime_type=file_record.mime_type,
            uploader_id=current_user.id,
            has_watermark=True,
            watermark_type=algorithm or 'Unknown',
            watermark_text=extracted_text,
            processing_status='completed'
        )
        db.session.add(watermarked_file)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error creating watermarked file record: {e}")
    
    return jsonify({
        'success': True,
        'extracted_text': extracted_text,
        'algorithm': algorithm,
        'attempt_results': attempt_results
    })

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
            return jsonify({'error': '没有选择文件'}), 400
        
        # 先保存到临时目录进行检查
        temp_file_path, error, file_info = handle_file_upload(f, 'video', save_to_temp=True)
        if error:
            return jsonify({'error': error}), 400

        final_file_path = move_file_to_final_location(
            temp_file_path, 'video', file_info['unique_filename']
        )

        if not final_file_path:
            try:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
            except Exception:
                pass
            return jsonify({'error': '文件移动失败'}), 500

        try:
            file_record = File(
                filename=file_info['filename'],
                original_path=final_file_path,
                file_hash=file_info['file_hash'],
                file_type='video',
                file_format=file_info['file_format'],
                file_size=file_info['file_size'],
                mime_type=file_info['mime_type'],
                uploader_id=current_user.id,
                group_id=current_user.groups[0].id if current_user.groups else None,
                processing_status='pending',
                has_watermark=False
            )

            db.session.add(file_record)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            try:
                if os.path.exists(final_file_path):
                    os.remove(final_file_path)
            except Exception:
                pass
            return jsonify({'error': f'保存文件记录失败: {str(e)}'}), 500

        return jsonify({
            'success': True,
            'message': '文件上传成功',
            'file_id': file_record.id,
            'filename': file_info['filename'],
            'file_type': 'video',
            'has_watermark': False
        })
    
    # 获取用户的视频文件列表（分页，分未加水印/已加水印）
    page = request.args.get('page', 1, type=int)
    watermarked_page = request.args.get('watermarked_page', 1, type=int)
    per_page = 5
    unwatermarked_pagination = get_user_files_pagination(
        current_user, 'video', has_watermark=False, page=page, per_page=per_page
    )
    watermarked_pagination = get_user_files_pagination(
        current_user, 'video', has_watermark=True, page=watermarked_page, per_page=per_page
    )
    return render_template(
        'video/upload.html',
        unwatermarked_pagination=unwatermarked_pagination,
        watermarked_pagination=watermarked_pagination
    )

@app.route('/video/add_watermark', methods=['GET', 'POST'])
@login_required
def video_add_watermark():
    form = WatermarkForm()
    if form.validate_on_submit():
        # 获取选中的文件ID
        selected_file_ids = request.form.get('selected_file_ids', '')
        
        if not selected_file_ids or not selected_file_ids.strip():
            flash('请先选择要添加水印的文件', 'error')
            return redirect(url_for('video_add_watermark'))
        
        # 处理选中的文件
        file_ids = [int(id.strip()) for id in selected_file_ids.split(',') if id.strip()]
        
        if not file_ids:
            flash('请先选择要添加水印的文件', 'error')
            return redirect(url_for('video_add_watermark'))
        
        files = File.query.filter(
            File.id.in_(file_ids),
            File.uploader_id == current_user.id,
            File.file_type == 'video',
            File.has_watermark == False
        ).all()
        
        if not files:
            flash('未找到可处理的文件', 'error')
            return redirect(url_for('video_add_watermark'))
        
        success_count = 0
        error_count = 0
        error_details = []
        
        for file in files:
            try:
                file.processing_status = 'processing'
                db.session.commit()
                random_seed = str(random.randint(0, 10**8)).zfill(8)
                result, algorithm,error,watermark_hash = process_watermark(
                    file.original_path,
                    form.watermark.data,
                    'embed',
                    random_seed=random_seed
                )
                
                if result and not error:
                    # 创建新的文件记录表示已添加水印的版本
                    watermarked_file = File(
                        filename=file.filename,
                        original_path=file.original_path,  # 保持相同的原始路径引用
                        watermarked_path=result,
                        file_hash=file.file_hash,  # 复制原文件的hash
                        file_watermark_hash=calculate_file_hash(result),
                        file_type=file.file_type,
                        file_format=file.file_format,
                        file_size=file.file_size,
                        mime_type=file.mime_type,  # 复制mime_type
                        uploader_id=current_user.id,
                        has_watermark=True,
                        watermark_type=algorithm,
                        original_watermark_text=form.watermark.data,
                        watermark_text=watermark_hash,
                        processing_status='completed',
                        error_message=None,
                        watermark_seed=random_seed
                    )
                    db.session.add(watermarked_file)
                    
                    # 原文件保持 has_watermark=False，只更新处理状态
                    file.processing_status = 'completed'
                    file.error_message = None
                    success_count += 1
                else:
                    error_message = error or '水印处理失败'
                    file.processing_status = 'failed'
                    file.error_message = error_message
                    error_count += 1
                    error_details.append({
                        'filename': file.filename,
                        'error': error_message
                    })
                    
            except Exception as e:
                error_message = str(e)
                file.processing_status = 'failed'
                file.error_message = error_message
                error_count += 1
                error_details.append({
                    'filename': file.filename,
                    'error': error_message
                })
        
        db.session.commit()
        
        # 将结果存储到 session 中
        session['embed_result'] = {
            'success_count': success_count,
            'error_count': error_count,
            'error_details': error_details,
            'total_count': len(files)
        }
        
        return redirect(url_for('video_add_watermark'))
    
    # 获取分页参数
    page = request.args.get('page', 1, type=int)
    per_page = 5  # 每页5条数据
    
    # 获取未添加水印的文件
    unwatermarked_pagination = get_user_files_pagination(
        current_user, 'video', has_watermark=False, page=page, per_page=per_page
    )
    
    # 获取已添加水印的文件  
    watermarked_page = request.args.get('watermarked_page', 1, type=int)
    watermarked_pagination = get_user_files_pagination(
        current_user, 'video', has_watermark=True, page=watermarked_page, per_page=per_page
    )
    
    # 获取嵌入结果并清除
    embed_result = session.pop('embed_result', None)
    
    return render_template('video/add_watermark.html', 
                         form=form, 
                         unwatermarked_pagination=unwatermarked_pagination,
                         watermarked_pagination=watermarked_pagination,
                         embed_result=embed_result)

@app.route('/video/extract_watermark', methods=['GET', 'POST'])
@login_required
def video_extract_watermark():
    if request.method == 'POST':
        # 处理批量提取
        selected_file_ids = request.form.getlist('selected_files')
        if selected_file_ids:
            results = {}
            for file_id in selected_file_ids:
                try:
                    file_record = File.query.get(file_id)
                    if not file_record or file_record.uploader_id != current_user.id:
                        continue
                    
                    # 提取水印
                    extracted_text, _, error = process_watermark(
                        file_record.watermarked_path,
                        None,
                        'extract',
                        file_id, # 传递文件ID
                        random_seed=file_record.watermark_seed
                    )
                    
                    if not error:
                        results[file_record.filename] = extracted_text
                    
                except Exception as e:
                    continue
            
            # 将结果存储到session中
            session['extracted_watermarks'] = results
            return redirect(url_for('video_extract_watermark'))
        
        # 处理单个文件上传提取
        if 'file' not in request.files:
            return jsonify({'error': '没有文件被上传'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'})
        
        # 使用通用文件上传处理函数
        file_path, error, _ = handle_file_upload(file, 'video')
        if error:
            return jsonify({'error': error})
        
        # 提取水印
        extracted_text, _, error = process_watermark(file_path, None, 'extract')
        
        if error:
            return jsonify({'error': f'水印提取失败: {error}'})
        
        return jsonify({
            'success': True,
            'extracted_text': extracted_text
        })
    
    # 获取未添加水印的文件列表（待处理的文件）
    page = request.args.get('page', 1, type=int)
    per_page = 5
    unwatermarked_pagination = get_user_files_pagination(
        current_user, 'video', has_watermark=False, page=page, per_page=per_page
    )
    
    # 获取已添加水印的文件列表（分页）
    watermarked_pagination = get_user_files_pagination(
        current_user, 'video', has_watermark=True, page=page, per_page=per_page
    )
    
    # 获取之前的提取结果
    extracted_watermarks = session.pop('extracted_watermarks', {})
    
    return render_template('video/extract_watermark.html',
                         unwatermarked_pagination=unwatermarked_pagination,
                         watermarked_pagination=watermarked_pagination,
                         extracted_watermarks=extracted_watermarks)

@app.route('/video/extract_from_file/<int:file_id>')
@login_required
def video_extract_from_file(file_id):
    # 获取文件记录
    file_record = File.query.get_or_404(file_id)
    if file_record.uploader_id != current_user.id:
        return jsonify({'error': '您没有权限处理该文件'})
    
    # 提取水印
    random_seed = file_record.watermark_seed
    extracted_text, _, error = process_watermark(
        file_record.watermarked_path,
        None,
        'extract',
        file_id, # 传递文件ID
        random_seed=random_seed
    )
    
    if error:
        return jsonify({'error': f'水印提取失败: {error}'})
    
    return jsonify({
        'success': True,
        'extracted_text': extracted_text
    })

@app.route('/video/extract_from_unwatermarked_file/<int:file_id>')
@login_required
def video_extract_from_unwatermarked_file(file_id):
    # 获取文件记录
    file_record = File.query.get_or_404(file_id)
    if file_record.uploader_id != current_user.id:
        return jsonify({'error': '您没有权限处理该文件'})
    
    # 尝试所有算法从原始文件提取水印
    extracted_text, algorithm, error, attempt_results = process_watermark_try_all_algorithms(
        file_record.original_path
    )
    
    if error:
        return jsonify({
            'error': f'水印提取失败: {error}',
            'attempt_results': attempt_results
        })
    
    # 成功提取水印后，将文件复制到 embed 文件夹，并创建一个已添加水印的文件记录
    try:
        # 获取用户的 embed 目录
        user_embed_dir = get_user_dated_embed_dir(current_user.username, 'video')
        
        # 生成唯一的文件名（保持原始扩展名）
        file_ext = os.path.splitext(file_record.filename)[1]
        unique_filename = f"{file_record.file_hash}_embed{file_ext}"
        embed_file_path = os.path.join(user_embed_dir, unique_filename)
        
        # 复制文件到 embed 目录
        shutil.copy2(file_record.original_path, embed_file_path)
        
        watermarked_file = File(
            filename=file_record.filename,
            original_path=file_record.original_path,
            watermarked_path=embed_file_path,  # 使用 embed 目录下的路径
            file_hash=file_record.file_hash,
            file_watermark_hash=file_record.file_hash,
            file_type=file_record.file_type,
            file_format=file_record.file_format,
            file_size=file_record.file_size,
            mime_type=file_record.mime_type,
            uploader_id=current_user.id,
            has_watermark=True,
            watermark_type=algorithm or 'Unknown',
            watermark_text=extracted_text,
            processing_status='completed'
        )
        db.session.add(watermarked_file)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error creating watermarked file record: {e}")
    
    return jsonify({
        'success': True,
        'extracted_text': extracted_text,
        'algorithm': algorithm,
        'attempt_results': attempt_results
    })

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
            
        # 先保存到临时目录进行检查
        temp_file_path, error, file_info = handle_file_upload(f, 'text', save_to_temp=True)
        if error:
            return jsonify({'error': error}), 400

        final_file_path = move_file_to_final_location(
            temp_file_path, 'text', file_info['unique_filename']
        )

        if not final_file_path:
            try:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
            except Exception:
                pass
            return jsonify({'error': '文件移动失败'}), 500

        try:
            file_record = File(
                filename=file_info['filename'],
                original_path=final_file_path,
                file_hash=file_info['file_hash'],
                file_type='text',
                file_format=file_info['file_format'],
                file_size=file_info['file_size'],
                mime_type=file_info['mime_type'],
                uploader_id=current_user.id,
                group_id=current_user.groups[0].id if current_user.groups else None,
                processing_status='pending',
                has_watermark=False
            )

            db.session.add(file_record)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            try:
                if os.path.exists(final_file_path):
                    os.remove(final_file_path)
            except Exception:
                pass
            return jsonify({'error': f'保存文件记录失败: {str(e)}'}), 500

        return jsonify({
            'success': True,
            'message': '文件上传成功',
            'file_id': file_record.id,
            'filename': file_info['filename'],
            'file_type': 'text',
            'has_watermark': False
        })
    
    # 获取用户的文本文件列表（分页，分未加水印/已加水印）
    page = request.args.get('page', 1, type=int)
    watermarked_page = request.args.get('watermarked_page', 1, type=int)
    per_page = 5
    unwatermarked_pagination = get_user_files_pagination(
        current_user, 'text', has_watermark=False, page=page, per_page=per_page
    )
    watermarked_pagination = get_user_files_pagination(
        current_user, 'text', has_watermark=True, page=watermarked_page, per_page=per_page
    )
    return render_template(
        'text/upload.html',
        unwatermarked_pagination=unwatermarked_pagination,
        watermarked_pagination=watermarked_pagination
    )

@app.route('/text/add_watermark', methods=['GET', 'POST'])
@login_required
def text_add_watermark():
    form = WatermarkForm()
    if form.validate_on_submit():
        # 获取选中的文件ID
        selected_file_ids = request.form.get('selected_file_ids', '')
        
        if not selected_file_ids or not selected_file_ids.strip():
            flash('请先选择要添加水印的文件', 'error')
            return redirect(url_for('text_add_watermark'))
        
        # 处理选中的文件
        file_ids = [int(id.strip()) for id in selected_file_ids.split(',') if id.strip()]
        
        if not file_ids:
            flash('请先选择要添加水印的文件', 'error')
            return redirect(url_for('text_add_watermark'))
        
        files = File.query.filter(
            File.id.in_(file_ids),
            File.uploader_id == current_user.id,
            File.file_type == 'text',
            File.has_watermark == False
        ).all()
        
        if not files:
            flash('未找到可处理的文件', 'error')
            return redirect(url_for('text_add_watermark'))
        
        success_count = 0
        error_count = 0
        error_details = []
        
        for file in files:
            try:
                file.processing_status = 'processing'
                db.session.commit()
                result, algorithm, error = process_watermark(
                    file.original_path,
                    form.watermark.data,
                    'embed'
                )
                
                if result and not error:
                    # 创建新的文件记录表示已添加水印的版本
                    watermarked_file = File(
                        filename=file.filename,
                        original_path=file.original_path,  # 保持相同的原始路径引用
                        watermarked_path=result,
                        file_hash=file.file_hash,  # 复制原文件的hash
                        file_watermark_hash=calculate_file_hash(result),
                        file_type=file.file_type,
                        file_format=file.file_format,
                        file_size=file.file_size,
                        mime_type=file.mime_type,  # 复制mime_type
                        uploader_id=current_user.id,
                        has_watermark=True,
                        watermark_type=algorithm,
                        watermark_text=form.watermark.data,
                        processing_status='completed',
                        error_message=None
                    )
                    db.session.add(watermarked_file)
                    
                    # 原文件保持 has_watermark=False，只更新处理状态
                    file.processing_status = 'completed'
                    file.error_message = None
                    success_count += 1
                else:
                    error_message = error or '水印处理失败'
                    file.processing_status = 'failed'
                    file.error_message = error_message
                    error_count += 1
                    error_details.append({
                        'filename': file.filename,
                        'error': error_message
                    })
                    
            except Exception as e:
                error_message = str(e)
                file.processing_status = 'failed'
                file.error_message = error_message
                error_count += 1
                error_details.append({
                    'filename': file.filename,
                    'error': error_message
                })
        
        db.session.commit()
        
        # 将结果存储到 session 中
        session['embed_result'] = {
            'success_count': success_count,
            'error_count': error_count,
            'error_details': error_details,
            'total_count': len(files)
        }
        
        return redirect(url_for('text_add_watermark'))
    
    # 获取分页参数
    page = request.args.get('page', 1, type=int)
    per_page = 5  # 每页5条数据
    
    # 获取未添加水印的文件
    unwatermarked_pagination = get_user_files_pagination(
        current_user, 'text', has_watermark=False, page=page, per_page=per_page
    )
    
    # 获取已添加水印的文件  
    watermarked_page = request.args.get('watermarked_page', 1, type=int)
    watermarked_pagination = get_user_files_pagination(
        current_user, 'text', has_watermark=True, page=watermarked_page, per_page=per_page
    )
    
    # 获取嵌入结果并清除
    embed_result = session.pop('embed_result', None)
    
    return render_template('text/add_watermark.html', 
                         form=form, 
                         unwatermarked_pagination=unwatermarked_pagination,
                         watermarked_pagination=watermarked_pagination,
                         embed_result=embed_result)

@app.route('/text/extract_watermark', methods=['GET', 'POST'])
@login_required
def text_extract_watermark():
    if request.method == 'POST':
        # 处理批量提取
        selected_file_ids = request.form.getlist('selected_files')
        if selected_file_ids:
            results = {}
            for file_id in selected_file_ids:
                try:
                    file_record = File.query.get(file_id)
                    if not file_record or file_record.uploader_id != current_user.id:
                        continue
                    
                    # 提取水印
                    extracted_text, _, error = process_watermark(
                        file_record.watermarked_path,
                        None,
                        'extract',
                        file_id # 传递文件ID
                    )
                    
                    if not error:
                        results[file_record.filename] = extracted_text
                    
                except Exception as e:
                    continue
            
            # 将结果存储到session中
            session['extracted_watermarks'] = results
            return redirect(url_for('text_extract_watermark'))
        
        # 处理单个文件上传提取
        if 'file' not in request.files:
            return jsonify({'error': '没有文件被上传'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'})
        
        # 使用通用文件上传处理函数
        file_path, error, _ = handle_file_upload(file, 'text')
        if error:
            return jsonify({'error': error})
        
        # 提取水印
        extracted_text, _, error = process_watermark(file_path, None, 'extract')
        
        if error:
            return jsonify({'error': f'水印提取失败: {error}'})
        
        return jsonify({
            'success': True,
            'extracted_text': extracted_text
        })
    
    # 获取未添加水印的文件列表（待处理的文件）
    page = request.args.get('page', 1, type=int)
    per_page = 5
    unwatermarked_pagination = get_user_files_pagination(
        current_user, 'text', has_watermark=False, page=page, per_page=per_page
    )
    
    # 获取已添加水印的文件列表（分页）
    watermarked_pagination = get_user_files_pagination(
        current_user, 'text', has_watermark=True, page=page, per_page=per_page
    )
    
    # 获取之前的提取结果
    extracted_watermarks = session.pop('extracted_watermarks', {})
    
    return render_template('text/extract_watermark.html',
                         unwatermarked_pagination=unwatermarked_pagination,
                         watermarked_pagination=watermarked_pagination,
                         extracted_watermarks=extracted_watermarks)

@app.route('/text/extract_from_file/<int:file_id>')
@login_required
def text_extract_from_file(file_id):
    # 获取文件记录
    file_record = File.query.get_or_404(file_id)
    if file_record.uploader_id != current_user.id:
        return jsonify({'error': '您没有权限处理该文件'})
    
    # 提取水印
    extracted_text, _, error = process_watermark(
        file_record.watermarked_path,
        None,
        'extract',
        file_id # 传递文件ID
    )
    
    if error:
        return jsonify({'error': f'水印提取失败: {error}'})
    
    return jsonify({
        'success': True,
        'extracted_text': extracted_text
    })

@app.route('/text/extract_from_unwatermarked_file/<int:file_id>')
@login_required
def text_extract_from_unwatermarked_file(file_id):
    # 获取文件记录
    file_record = File.query.get_or_404(file_id)
    if file_record.uploader_id != current_user.id:
        return jsonify({'error': '您没有权限处理该文件'})
    
    # 尝试所有算法从原始文件提取水印
    extracted_text, algorithm, error, attempt_results = process_watermark_try_all_algorithms(
        file_record.original_path
    )
    
    if error:
        return jsonify({
            'error': f'水印提取失败: {error}',
            'attempt_results': attempt_results
        })
    
    # 成功提取水印后，将文件复制到 embed 文件夹，并创建一个已添加水印的文件记录
    try:
        # 获取用户的 embed 目录
        user_embed_dir = get_user_dated_embed_dir(current_user.username, 'text')
        
        # 生成唯一的文件名（保持原始扩展名）
        file_ext = os.path.splitext(file_record.filename)[1]
        unique_filename = f"{file_record.file_hash}_embed{file_ext}"
        embed_file_path = os.path.join(user_embed_dir, unique_filename)
        
        # 复制文件到 embed 目录
        shutil.copy2(file_record.original_path, embed_file_path)
        
        watermarked_file = File(
            filename=file_record.filename,
            original_path=file_record.original_path,
            watermarked_path=embed_file_path,  # 使用 embed 目录下的路径
            file_hash=file_record.file_hash,
            file_watermark_hash=file_record.file_hash,
            file_type=file_record.file_type,
            file_format=file_record.file_format,
            file_size=file_record.file_size,
            mime_type=file_record.mime_type,
            uploader_id=current_user.id,
            has_watermark=True,
            watermark_type=algorithm or 'Unknown',
            watermark_text=extracted_text,
            processing_status='completed'
        )
        db.session.add(watermarked_file)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error creating watermarked file record: {e}")
    
    return jsonify({
        'success': True,
        'extracted_text': extracted_text,
        'algorithm': algorithm,
        'attempt_results': attempt_results
    })

@app.route('/batch_delete', methods=['POST'])
@login_required
def batch_delete():
    """批量删除文件"""
    file_ids_str = request.form.get('file_ids', '')
    if not file_ids_str:
        flash("没有选择要删除的文件")
        return redirect(request.referrer or url_for('index'))
    
    try:
        file_ids = [int(id.strip()) for id in file_ids_str.split(',') if id.strip()]
        if not file_ids:
            flash("没有选择要删除的文件")
            return redirect(request.referrer or url_for('index'))
        
        # 查询用户有权限删除的文件
        files = File.query.filter(
            File.id.in_(file_ids),
            File.uploader_id == current_user.id
        ).all()
        
        if not files:
            flash("没有找到可删除的文件")
            return redirect(request.referrer or url_for('index'))
        
        success_count = 0
        error_count = 0
        
        for file in files:
            try:
                # 删除原始文件
                if file.original_path and os.path.exists(file.original_path):
                    os.remove(file.original_path)
                
                # 删除水印文件
                if file.watermarked_path and os.path.exists(file.watermarked_path):
                    os.remove(file.watermarked_path)
                
                # 从数据库删除记录
                db.session.delete(file)
                success_count += 1
                
            except Exception as e:
                error_count += 1
                print(f"删除文件 {file.filename} 时发生错误: {str(e)}")
        
        db.session.commit()
        
        if success_count > 0:
            flash(f"成功删除 {success_count} 个文件")
        if error_count > 0:
            flash(f"删除失败 {error_count} 个文件")
            
    except Exception as e:
        flash(f"批量删除操作失败: {str(e)}")
    
    return redirect(request.referrer or url_for('index'))

@app.route('/batch_download', methods=['POST'])
@login_required  
def batch_download():
    """批量下载文件"""
    import zipfile
    import tempfile
    from flask import make_response
    
    file_ids_str = request.form.get('file_ids', '')
    if not file_ids_str:
        flash("没有选择要下载的文件")
        return redirect(request.referrer or url_for('index'))
    
    try:
        file_ids = [int(id.strip()) for id in file_ids_str.split(',') if id.strip()]
        if not file_ids:
            flash("没有选择要下载的文件")
            return redirect(request.referrer or url_for('index'))
        
        # 查询用户有权限下载的文件
        files = File.query.filter(
            File.id.in_(file_ids),
            File.uploader_id == current_user.id,
            File.has_watermark == True  # 只下载已添加水印的文件
        ).all()
        
        if not files:
            flash("没有找到可下载的文件")
            return redirect(request.referrer or url_for('index'))
        
        # 创建临时ZIP文件
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        temp_zip.close()
        
        with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file in files:
                if file.watermarked_path and os.path.exists(file.watermarked_path):
                    # 使用原始文件名作为ZIP内的文件名
                    zip_file.write(file.watermarked_path, file.filename)
        
        # 读取ZIP文件内容
        with open(temp_zip.name, 'rb') as f:
            zip_data = f.read()
        
        # 删除临时文件
        os.unlink(temp_zip.name)
        
        # 创建响应
        response = make_response(zip_data)
        response.headers['Content-Type'] = 'application/zip'
        response.headers['Content-Disposition'] = f'attachment; filename=watermarked_files_{get_now_utc().strftime("%Y%m%d_%H%M%S")}.zip'
        
        return response
        
    except Exception as e:
        flash(f"批量下载操作失败: {str(e)}")
        return redirect(request.referrer or url_for('index'))

# -----------------------------
# 全局错误处理
# -----------------------------

@app.errorhandler(404)
def handle_404_error(error):
    """全局 404 错误处理：根据请求头返回 HTML 或 JSON。"""
    accepts_json = (
        request.is_json
        or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        or request.accept_mimetypes['application/json'] >= request.accept_mimetypes['text/html']
    )
    if accepts_json:
        return jsonify({
            'error': 'Not Found',
            'message': '您访问的资源不存在',
            'code': 404
        }), 404
    return render_template('404.html'), 404


@app.errorhandler(500)
def handle_500_error(error):
    """全局 500 错误处理：记录异常并根据需要返回 JSON 或 HTML。"""
    try:
        current_app.logger.exception('Unhandled Exception: %s', error)
    except Exception:
        pass

    accepts_json = (
        request.is_json
        or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        or request.accept_mimetypes['application/json'] >= request.accept_mimetypes['text/html']
    )
    if accepts_json:
        return jsonify({
            'error': 'Internal Server Error',
            'message': '服务器内部错误，请稍后重试',
            'code': 500
        }), 500
    return render_template('500.html'), 500

# -----------------------------
# 文件搜索
# -----------------------------

@app.route('/search', methods=['GET'])
@login_required
def search():
    """按文件名模糊搜索，显示用户有权限查看的文件（本人 + 组）。"""
    query_text = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    files_pagination = None
    if query_text:
        user_group_ids = [group.id for group in current_user.groups]
        base_query = File.query.filter(
            File.filename.like(f"%{query_text}%")
        )
        if user_group_ids:
            base_query = base_query.filter(
                (File.group_id.in_(user_group_ids)) | (File.uploader_id == current_user.id)
            )
        else:
            base_query = base_query.filter(File.uploader_id == current_user.id)

        files_pagination = base_query.order_by(File.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

    return render_template(
        'search_results.html',
        q=query_text,
        files_pagination=files_pagination,
        format_file_size=format_file_size
    )


# ============================================================================
# 问题反馈路由
# ============================================================================

@app.route('/feedback', methods=['GET'])
def feedback():
    """显示问题反馈页面"""
    return render_template('feedback.html')


@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    """处理问题反馈提交（暂不保存到数据库）"""
    # 获取表单数据
    name = request.form.get('name', '')
    contact = request.form.get('contact', '')
    issue_type = request.form.get('issue_type', '')
    title = request.form.get('title', '')
    description = request.form.get('description', '')
    
    # 记录到日志（可选）
    current_app.logger.info(
        f'收到反馈 - 姓名: {name}, 联系方式: {contact}, '
        f'类型: {issue_type}, 标题: {title}'
    )
    
    # 显示成功消息
    flash('感谢您的反馈！我们已收到您的问题，会尽快处理。', 'success')
    
    # 重定向回首页
    return redirect(url_for('index'))

# ============================================================================
# 清理文件：前端可配置清理天数
# ============================================================================

from typing import List
import threading
import time
import json
from typing import List

# 简单的分页对象类，用于模拟 Flask-SQLAlchemy 的 Pagination
class SimplePagination:
    def __init__(self, items, page, per_page, total):
        self.items = items
        self.page = page
        self.per_page = per_page
        self.total = total
        self.pages = (total + per_page - 1) // per_page if per_page > 0 else 0
        self.has_prev = page > 1
        self.has_next = page < self.pages
        self.prev_num = page - 1 if self.has_prev else None
        self.next_num = page + 1 if self.has_next else None
    
    def iter_pages(self, left_edge=2, left_current=2, right_current=3, right_edge=2):
        """生成页码列表，None 表示省略号"""
        last = 0
        for num in range(1, self.pages + 1):
            if (num <= left_edge or 
                (self.page - left_current - 1 < num < self.page + right_current) or 
                num > self.pages - right_edge):
                if last + 1 != num:
                    yield None
                yield num
                last = num

# ============================================================================
# 后台线程：按用户定期清理文件
# ============================================================================

_cleanup_thread_started = False

def _write_cleanup_log(username: str, deleted_files: list, days: int):
    """将清理记录写入JSON文件
    
    Args:
        username: 用户名
        deleted_files: 被删除的文件信息列表
        days: 保留天数（该用户设置的文件保留天数）
    """
    try:
        logs_dir = app.config.get('LOGS_FOLDER', 'instance/logs')
        os.makedirs(logs_dir, exist_ok=True)
        
        # 按日期创建JSON日志文件
        log_date = get_now_utc().strftime('%Y-%m-%d')
        log_file = os.path.join(logs_dir, f'cleanup_{log_date}.json')
        
        # 准备日志条目
        log_entry = {
            'timestamp': get_now_utc().strftime('%Y-%m-%d %H:%M:%S'),
            'username': username,
            'retention_days': days,
            'deleted_count': len(deleted_files),
            'files': deleted_files
        }
        
        # 读取现有日志
        existing_logs = []
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    existing_logs = json.load(f)
            except (json.JSONDecodeError, Exception):
                existing_logs = []
        
        # 追加新日志
        existing_logs.append(log_entry)
        
        # 写回文件
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(existing_logs, f, ensure_ascii=False, indent=2)
            
        current_app.logger.info('清理日志已写入: %s', log_file)
    except Exception as e:
        current_app.logger.error('写入清理日志失败: %s', e)

def _user_cleanup_worker(interval_seconds: int = 1800, default_days: int = 7):
    """后台循环：定期扫描所有用户，根据 retention_days 删除其过期文件。

    interval_seconds: 扫描间隔秒数
    default_days: 用户未设置 retention_days 时使用的默认保留天数
    """
    while True:
        try:
            with app.app_context():
                users = User.query.all()
                for user in users:
                    days = user.retention_days if user.retention_days and user.retention_days > 0 else default_days
                    cutoff = get_now_utc() - timedelta(days=days)
                    # 查询该用户的文件，超过天数的判定依据 created_at
                    old_files = File.query.filter(File.uploader_id == user.id, File.created_at < cutoff).all()
                    
                    if not old_files:
                        continue
                    
                    deleted_files = []
                    removed_count = 0
                    
                    for f in old_files:
                        # 记录文件信息
                        file_info = {
                            'filename': f.filename,
                            'file_type': f.file_type,
                            'file_size': f.file_size,
                            'created_at': f.created_at.strftime('%Y-%m-%d %H:%M:%S') if f.created_at else 'N/A',
                            'has_watermark': f.has_watermark,
                            'original_path': f.original_path,
                            'watermarked_path': f.watermarked_path
                        }
                        
                        # 删除物理文件
                        for path in [f.original_path, f.watermarked_path]:
                            if path and os.path.exists(path):
                                try:
                                    os.remove(path)
                                except Exception:
                                    pass
                        
                        try:
                            db.session.delete(f)
                            removed_count += 1
                            deleted_files.append(file_info)
                        except Exception:
                            db.session.rollback()
                    
                    if removed_count:
                        try:
                            db.session.commit()
                            current_app.logger.info('后台清理: user=%s days=%s removed=%s', user.username, days, removed_count)
                            # 写入日志文件
                            _write_cleanup_log(user.username, deleted_files, days)
                        except Exception as e:
                            db.session.rollback()
                            current_app.logger.error('后台清理提交失败: %s', e)
        except Exception as e:
            try:
                current_app.logger.exception('后台清理线程错误: %s', e)
            except Exception:
                pass
        time.sleep(interval_seconds)

def ensure_cleanup_thread():
    global _cleanup_thread_started
    if not _cleanup_thread_started:
        t = threading.Thread(target=_user_cleanup_worker, args=(1800, 7), daemon=True)
        t.start()
        _cleanup_thread_started = True
        current_app.logger.info('用户文件后台清理线程已启动')

# 在应用启动后尝试启动一次（被导入时可能无应用上下文，使用 after_request 保底）
@app.before_request
def _start_background_cleanup_if_needed():
    try:
        ensure_cleanup_thread()
    except Exception:
        pass

# ============================================================================
# 用户设置保留天数 UI + API
# ============================================================================

@app.route('/profile/retention', methods=['GET', 'POST'])
@login_required
def profile_retention():
    if request.method == 'POST':
        days = request.form.get('days', type=int)
        if not days or days < 1 or days > 365:
            flash('保留天数必须在 1-365 之间', 'warning')
            return redirect(url_for('profile_retention'))
        try:
            current_user.retention_days = days
            db.session.commit()
            flash(f'已更新保留天数为 {days} 天', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'更新失败: {e}', 'danger')
        return redirect(url_for('profile_retention'))
    
    # 获取分页参数
    page = request.args.get('page', 1, type=int)
    per_page = 2  # 每页显示2条清理记录（便于测试分页）
    
    # 读取当前用户的所有清理日志
    all_logs = _get_all_user_cleanup_logs(current_user.username)
    
    # 手动实现分页
    total = len(all_logs)
    start = (page - 1) * per_page
    end = start + per_page
    cleanup_logs = all_logs[start:end]
    
    # 创建分页对象
    pagination = SimplePagination(
        items=cleanup_logs,
        page=page,
        per_page=per_page,
        total=total
    )
    
    return render_template('profile/retention.html', 
                         current_days=current_user.retention_days or 7,
                         pagination=pagination)

def _get_all_user_cleanup_logs(username: str):
    """获取用户的所有清理日志
    
    Args:
        username: 用户名
    
    Returns:
        list: 清理日志列表，按时间倒序
    """
    try:
        logs_dir = app.config.get('LOGS_FOLDER', 'instance/logs')
        if not os.path.exists(logs_dir):
            return []
        
        # 获取所有JSON日志文件，按日期倒序
        log_files = sorted(
            [f for f in os.listdir(logs_dir) if f.startswith('cleanup_') and f.endswith('.json')],
            reverse=True
        )
        
        user_logs = []
        for log_file in log_files:
            log_path = os.path.join(logs_dir, log_file)
            try:
                with open(log_path, 'r', encoding='utf-8') as f:
                    daily_logs = json.load(f)
                    # 筛选当前用户的日志，按时间倒序
                    for log_entry in reversed(daily_logs):
                        if log_entry.get('username') == username:
                            user_logs.append(log_entry)
            except Exception as e:
                current_app.logger.error('读取日志文件失败 %s: %s', log_file, e)
                continue
        
        return user_logs
    except Exception as e:
        current_app.logger.error('获取清理日志失败: %s', e)
        return []

def _get_user_cleanup_logs(username: str, limit: int = 10):
    """获取用户的清理日志
    
    Args:
        username: 用户名
        limit: 返回最近N条记录
    
    Returns:
        list: 清理日志列表，按时间倒序
    """
    try:
        logs_dir = app.config.get('LOGS_FOLDER', 'instance/logs')
        if not os.path.exists(logs_dir):
            return []
        
        # 获取所有JSON日志文件，按日期倒序
        log_files = sorted(
            [f for f in os.listdir(logs_dir) if f.startswith('cleanup_') and f.endswith('.json')],
            reverse=True
        )
        
        user_logs = []
        for log_file in log_files:
            if len(user_logs) >= limit:
                break
                
            log_path = os.path.join(logs_dir, log_file)
            try:
                with open(log_path, 'r', encoding='utf-8') as f:
                    daily_logs = json.load(f)
                    # 筛选当前用户的日志，按时间倒序
                    for log_entry in reversed(daily_logs):
                        if len(user_logs) >= limit:
                            break
                        if log_entry.get('username') == username:
                            user_logs.append(log_entry)
            except Exception as e:
                current_app.logger.error('读取日志文件失败 %s: %s', log_file, e)
                continue
        
        return user_logs
    except Exception as e:
        current_app.logger.error('获取清理日志失败: %s', e)
        return []

@app.route('/api/profile/retention', methods=['POST'])
@login_required
def api_profile_retention():
    payload = request.get_json(silent=True) or request.form
    try:
        days = int(payload.get('days', 0))
        if days < 1 or days > 365:
            return jsonify({'success': False, 'message': 'days 需在 1-365 之间'}), 400
        current_user.retention_days = days
        db.session.commit()
        return jsonify({'success': True, 'days': days})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
