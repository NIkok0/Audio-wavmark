from flask import render_template, Flask, redirect, url_for, request, flash, session, jsonify
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

from watermark.watermarkSystem import watermarks_select
from flask import send_from_directory
import json
from watermark import app, db

# 确保上传目录存在
upload_dir = os.path.join(os.getcwd(), 'upload')
upload_for_extract_dir = os.path.join(os.getcwd(), 'extract_file')
embed_dir = os.path.join(os.getcwd(), 'embed_file')

for directory in [upload_dir, upload_for_extract_dir, embed_dir]:
    if not os.path.exists(directory):
        os.makedirs(directory, mode=0o755)

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
    if form.validate_on_submit():
        # 检查用户名和邮箱是否已存在
        if User.query.filter_by(username=form.username.data).first():
            flash("该用户名已存在！")
            return redirect(url_for('register'))
        if User.query.filter_by(email=form.email.data).first():
            flash("该邮箱已注册！")
            return redirect(url_for('register'))
        
        # 创建新用户
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=generate_password_hash(form.password.data)
        )
        db.session.add(user)
        db.session.commit()
        flash("注册成功，请登录！")
        return redirect(url_for('signin'))
    return render_template('register.html', form=form)

#登录
@app.route('/signin.html', methods=['GET', 'POST'])
def signin():
    form = LoginForm()
    if form.validate_on_submit():
        # 尝试通过用户名或邮箱查找用户
        user = User.query.filter(
            (User.username == form.username_or_email.data) | 
            (User.email == form.username_or_email.data)
        ).first()
        
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash(f"欢迎回来，{user.username}！")
            return redirect(url_for('index'))
            
        flash("用户名/邮箱或密码错误，请重新登录！")
        return redirect(url_for('signin'))
    return render_template('signin.html', form=form)

#登出
@app.route('/signout.html', methods=['GET', 'POST'])
@login_required
def signout():
    logout_user()
    return redirect(url_for('index'))

#添加水印——上传文件
@app.route('/upload', methods=['GET','POST'])
@login_required
def upload():
    if request.method == 'POST':
        f = request.files.get('file')
        if not f:
            return '没有选择文件', 400
            
        # 检查文件类型
        allowed_extensions = ['png', 'jpg', 'jpeg', 'bmp', 'mp3', 'mp4', 'wav', 'mxf', 'avi', 'mov', 'wmv', 'flv', 'mkv']
        if '.' not in f.filename:
            return '文件名无效', 400
        file_ext = f.filename.rsplit('.', 1)[1].lower()
        if file_ext not in allowed_extensions:
            return '上传格式仅限图片、音频、视频!', 400
            
        # 生成安全的文件名并保存文件
        original_filename = secure_filename(f.filename)
        file_path = os.path.join(upload_dir, original_filename)
        f.save(file_path)
        
        # 计算文件哈希值
        file_hash = calculate_file_hash(file_path)
        
        # 保存文件信息到数据库
        file_record = File(
            filename=original_filename,
            original_path=file_path,
            file_hash=file_hash,
            uploader_id=current_user.id
        )
        db.session.add(file_record)
        db.session.commit()
        
        return redirect(url_for('add_watermark'))
    # 显示上传页面
    return render_template('upload.html')

#添加水印
@app.route('/add_watermark.html', methods=['GET', 'POST'])
@login_required
def add_watermark():
    form = WatermarkForm()
    if form.validate_on_submit():
        # 获取当前用户上传的未加水印的文件
        files = File.query.filter_by(
            uploader_id=current_user.id,
            has_watermark=False
        ).all()
        
        for file in files:
            # 检查文件名是否有效
            if not file.filename or '.' not in file.filename:
                flash(f"文件名无效: {file.filename}")
                continue
                
            try:
                file_ext = file.filename.rsplit('.', 1)[1].lower()
            except IndexError:
                flash(f"文件名格式错误: {file.filename}")
                continue
            
            # 根据文件类型处理水印
            try:
                if file_ext in ['png', 'jpg', 'jpeg', 'bmp']:
                    watermarks_select("image", "embed", file.original_path, form.watermark.data)
                    # 图像处理后的文件命名格式可能为 original_filename_embed.bmp
                    watermarked_filename = f"{os.path.basename(file.original_path)}_embed.bmp"
                elif file_ext in ['wav', 'mp3']:
                    # 音频水印处理特殊处理，直接返回水印文件路径
                    result_path = watermarks_select("audio", "embed", file.original_path, form.watermark.data)
                    if result_path and os.path.exists(result_path):
                        file.watermarked_path = result_path
                        file.has_watermark = True
                        flash(f"音频水印添加成功: {file.filename}")
                        continue
                    else:
                        flash(f"音频水印添加失败: {file.filename}")
                        continue
                elif file_ext in ['mxf', 'mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv']:  # 添加更多视频格式支持
                    # 视频水印处理特殊处理，直接返回水印文件路径
                    try:
                        result_path = watermarks_select("video", "embed", file.original_path, form.watermark.data)
                        # 确保文件实际已被创建且存在
                        if result_path and os.path.exists(result_path) and os.path.getsize(result_path) > 0:
                            file.watermarked_path = result_path
                            file.has_watermark = True
                            flash(f"视频水印添加成功: {file.filename}")
                        else:
                            flash(f"视频水印生成失败，未能创建有效的输出文件: {file.filename}")
                        continue
                    except Exception as e:
                        flash(f"处理视频文件 {file.filename} 时出错: {str(e)}")
                        continue
                else:
                    flash(f"不支持的文件格式: {file_ext}")
                    continue  # 跳过不支持的文件类型
            except Exception as e:
                flash(f"处理文件 {file.filename} 时出错: {str(e)}")
                continue
            
            # 检查水印文件是否存在 - 图像可能在embed_dir中或当前目录
            watermarked_path = os.path.join(embed_dir, watermarked_filename)
            
            if os.path.exists(watermarked_path):
                # 水印文件直接保存在embed_dir中
                file.watermarked_path = watermarked_path
                file.has_watermark = True
            else:
                # 检查当前工作目录
                current_dir_path = os.path.join(os.getcwd(), watermarked_filename)
                if os.path.exists(current_dir_path):
                    # 确保embed_dir存在
                    if not os.path.exists(embed_dir):
                        os.makedirs(embed_dir)
                    # 移动文件到embed_dir
                    dest_path = os.path.join(embed_dir, watermarked_filename)
                    try:
                        os.rename(current_dir_path, dest_path)
                        file.watermarked_path = dest_path
                        file.has_watermark = True
                    except Exception as e:
                        flash(f"文件移动失败: {file.filename} - {str(e)}")
                else:
                    flash(f"水印文件生成失败: {file.filename}")
            
        db.session.commit()
        flash("水印添加完成，请在文件列表中下载！")
        return redirect(url_for('add_watermark'))
    
    # 获取当前用户的所有文件并分类
    original_files = File.query.filter_by(
        uploader_id=current_user.id,
        has_watermark=False
    ).order_by(File.created_at.desc()).all()
    
    watermarked_files = File.query.filter_by(
        uploader_id=current_user.id,
        has_watermark=True
    ).order_by(File.created_at.desc()).all()
        
    return render_template('add_watermark.html', 
                          form=form, 
                          original_files=original_files, 
                          watermarked_files=watermarked_files)

#含水印文件列表
@app.route('/filelist')
@login_required
def filelist():
    watermarked_files = File.query.filter_by(
        uploader_id=current_user.id,
        has_watermark=True
    ).all()
    return render_template('add_watermark.html', 
                          watermarked_files=watermarked_files)

#文件下载
@app.route('/download/<int:file_id>', methods=['GET'])
@login_required
def download(file_id):
    file = File.query.get_or_404(file_id)
    
    # 验证文件所有权
    if file.uploader_id != current_user.id:
        flash('您没有权限下载该文件')
        return redirect(url_for('filelist'))
    
    if not file.has_watermark:
        flash('该文件尚未添加水印')
        return redirect(url_for('filelist'))
        
    return send_from_directory(
        os.path.dirname(file.watermarked_path),
        os.path.basename(file.watermarked_path),
        mimetype='application/octet-stream'
    )

#删除文件
@app.route('/delete_file/<int:file_id>', methods=['POST'])
@login_required
def delete_file(file_id):
    file = File.query.get_or_404(file_id)
    
    # 验证文件所有权
    if file.uploader_id != current_user.id:
        flash('您没有权限删除该文件')
        return redirect(url_for('add_watermark'))
    
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
            
        flash('文件已成功删除')
    except Exception as e:
        flash(f'删除文件时出错: {str(e)}')
    
    # 根据请求来源决定重定向位置
    referer = request.referrer
    if referer and 'extract_watermark' in referer:
        return redirect(url_for('extract_watermark'))
    else:
        return redirect(url_for('add_watermark'))

#提取水印——上传文件
@app.route('/upload_for_extract', methods=['GET','POST'])
@login_required
def upload_for_extract():
    if request.method == 'POST':
        f = request.files.get('file')
        if not f:
            return '没有选择文件', 400
            
        # 检查文件类型
        allowed_extensions = ['png', 'jpg', 'jpeg', 'bmp', 'mp3', 'mp4', 'wav', 'mxf', 'avi', 'mov', 'wmv', 'flv', 'mkv']
        if '.' not in f.filename:
            return '文件名无效', 400
        file_ext = f.filename.rsplit('.', 1)[1].lower()
        if file_ext not in allowed_extensions:
            return '上传格式仅限图片、音频、视频!', 400
            
        # 生成安全的文件名并保存文件
        original_filename = secure_filename(f.filename)
        file_path = os.path.join(upload_for_extract_dir, original_filename)
        f.save(file_path)
        
        # 计算文件哈希值
        file_hash = calculate_file_hash(file_path)
        
        # 检查是否存在相同哈希值的文件
        existing_file = File.query.filter_by(file_hash=file_hash).first()
        
        extracted_files = session.get('extracted_files', {})
        
        try:
            # 根据文件扩展名判断媒体类型
            if file_ext in ['png', 'jpg', 'jpeg', 'bmp']:
                file_type = "image"
            elif file_ext in ['wav', 'mp3']:
                file_type = "audio"
            elif file_ext in ['mxf', 'mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv']:
                file_type = "video"
            else:
                flash('不支持的文件类型!')
                return redirect(url_for('extract_watermark'))
                
            # 提取水印
            result = watermarks_select(file_type, "extract", file_path)
            
            # 检查结果是否包含错误信息
            if result and isinstance(result, str) and result.startswith("水印提取失败"):
                flash(f"提取水印失败: {result}")
            else:
                extracted_files[original_filename] = result
                session['extracted_files'] = extracted_files
                flash(f"水印提取结果：{result}")
                
        except Exception as e:
            flash(f"提取水印时出错: {str(e)}")
            
        # 清理临时文件
        try:
            os.remove(file_path)
        except:
            pass
            
        return redirect(url_for('extract_watermark'))
    return render_template('extract_watermark.html')

# 直接从已有文件中提取水印
@app.route('/extract_from_file/<int:file_id>', methods=['GET'])
@login_required
def extract_from_file(file_id):
    # 获取文件信息
    file = File.query.get_or_404(file_id)
    
    # 验证文件所有权
    if file.uploader_id != current_user.id:
        flash('您没有权限提取该文件的水印')
        return redirect(url_for('extract_watermark'))
    
    if not file.has_watermark:
        flash('该文件尚未添加水印')
        return redirect(url_for('extract_watermark'))
    
    # 检查文件是否存在
    if not file.watermarked_path or not os.path.exists(file.watermarked_path):
        flash(f'无法找到水印文件: {file.filename}')
        return redirect(url_for('extract_watermark'))
    
    # 提取水印
    file_ext = file.filename.rsplit('.', 1)[1].lower()
    # 根据文件扩展名判断媒体类型
    if file_ext in ['png', 'jpg', 'jpeg', 'bmp']:
        file_type = "image"
    elif file_ext in ['wav', 'mp3']:
        file_type = "audio"
    elif file_ext in ['mxf', 'mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv']:
        file_type = "video"
    else:
        flash(f'不支持的文件类型: {file_ext}')
        return redirect(url_for('extract_watermark'))
    
    try:
        # 从带水印的文件路径中提取水印
        result = watermarks_select(file_type, "extract", file.watermarked_path)
        
        # 检查结果是否包含错误信息
        if result and isinstance(result, str) and result.startswith("水印提取失败"):
            flash(f"提取水印失败: {result}")
            return redirect(url_for('extract_watermark'))
        
        # 保存提取结果到会话
        extracted_files = session.get('extracted_files', {})
        extracted_files[file.filename] = result
        session['extracted_files'] = extracted_files
        
        flash(f"从文件 {file.filename} 提取水印成功: {result}")
    except Exception as e:
        flash(f"提取水印失败: {str(e)}")
    
    return redirect(url_for('extract_watermark'))

#提取水印
@app.route('/extract_watermark.html', methods=['GET','POST'])
@login_required
def extract_watermark():
    form = WatermarkForm()
    if form.validate_on_submit():
        # 获取当前用户上传的文件
        extracted_files = session.get('extracted_files', {})
        if extracted_files:
            expected_watermark = form.watermark.data
            comparison_results = {}
            
            # 遍历每个提取结果进行比对
            for filename, extracted_text in extracted_files.items():
                # 计算相似度和比对结果
                if expected_watermark == extracted_text:
                    match_status = "完全匹配"
                    similarity = 100
                else:
                    match_status = "不匹配"
                    # 计算简单的相似度
                    similarity = calculate_similarity(expected_watermark, extracted_text)
                
                comparison_results[filename] = {
                    "extracted": extracted_text,
                    "expected": expected_watermark,
                    "match_status": match_status,
                    "similarity": similarity
                }
            
            # 保存比对结果到会话
            session['comparison_results'] = comparison_results
            flash(f"水印比对完成。预期水印：{expected_watermark}")
        else:
            flash("请先上传需要提取水印的文件或从您的文件列表中选择文件")
    
    # 获取用户的所有含水印文件
    watermarked_files = File.query.filter_by(
        uploader_id=current_user.id,
        has_watermark=True
    ).order_by(File.created_at.desc()).all()
    
    # 获取提取结果
    extracted_files = session.get('extracted_files', {})
    
    # 获取比对结果
    comparison_results = session.get('comparison_results', {})
    
    return render_template('extract_watermark.html', 
                          form=form, 
                          watermarked_files=watermarked_files, 
                          extract_results=extracted_files,
                          comparison_results=comparison_results)

#提取水印信息列表
@app.route('/filelist2')
@login_required
def filelist2():
    # 从会话中获取提取结果
    files_info = session.get('extracted_files', {})
    if not files_info:
        # 如果没有提取结果，则从数据库获取用户的水印文件
        watermarked_files = File.query.filter_by(
            uploader_id=current_user.id,
            has_watermark=True
        ).all()
        
        # 构建文件信息字典
        for file in watermarked_files:
            files_info[file.filename] = {
                'original_name': file.filename,
                'watermarked_name': os.path.basename(file.watermarked_path) if file.watermarked_path else None,
                'upload_time': file.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
    
    return render_template('extract_watermark.html', files=files_info)

# 清除提取结果
@app.route('/clear_extract_result', methods=['POST'])
@login_required
def clear_extract_result():
    data = request.get_json()
    filename = data.get('filename')
    
    if filename:
        extracted_files = session.get('extracted_files', {})
        comparison_results = session.get('comparison_results', {})
        
        if filename in extracted_files:
            del extracted_files[filename]
            session['extracted_files'] = extracted_files
            
        if filename in comparison_results:
            del comparison_results[filename]
            session['comparison_results'] = comparison_results
            
        return jsonify({'status': 'success', 'message': '已清除提取结果'})
    
    return jsonify({'status': 'error', 'message': '清除失败，未找到结果'}), 400

# 清除所有提取结果
@app.route('/clear_all_extract_results', methods=['POST'])
@login_required
def clear_all_extract_results():
    session['extracted_files'] = {}
    session['comparison_results'] = {}  # 同时清除比对结果
    return jsonify({'status': 'success', 'message': '已清除所有提取结果'})

# 计算两个字符串的相似度
def calculate_similarity(str1, str2):
    if not str1 or not str2:
        return 0
    
    # Levenshtein距离计算
    def levenshtein_distance(s1, s2):
        if len(s1) < len(s2):
            return levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    # 计算距离
    distance = levenshtein_distance(str1, str2)
    max_len = max(len(str1), len(str2))
    
    # 计算相似度百分比
    if max_len == 0:
        return 100  # 两个空字符串视为完全匹配
    
    similarity = (1 - distance / max_len) * 100
    return round(similarity, 1)  # 保留一位小数