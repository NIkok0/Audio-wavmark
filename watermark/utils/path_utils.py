import os
from flask import current_app
from flask_login import current_user

from watermark.utils.time_provider import get_now_utc

import shutil
import uuid
from typing import Optional


def _secure_filename_with_chinese(filename: str) -> str:
    """保留中文与常见字符的安全文件名转换。"""
    import re
    # 允许中文、字母、数字、下划线、横杠、点号
    return re.sub(r"[^\u4e00-\u9fa5A-Za-z0-9_.\-]", "_", filename or "anonymous").strip("._") or "anonymous"


def _build_user_dated_dir(base_dir: str) -> str:
    username = getattr(current_user, 'username', 'anonymous') or 'anonymous'
    user_dir_name = _secure_filename_with_chinese(username)
    date_dir_name = get_now_utc().strftime('%Y%m%d')
    target_dir = os.path.join(base_dir, user_dir_name, date_dir_name)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)
    return target_dir


def get_user_dated_upload_dir(media_type: str) -> str:
    base_dir = current_app.config['MEDIA_FOLDERS'][media_type]['upload']
    return _build_user_dated_dir(base_dir)


def get_user_dated_embed_dir(media_type: str) -> str:
    base_dir = current_app.config['MEDIA_FOLDERS'][media_type]['embed']
    return _build_user_dated_dir(base_dir)


def get_user_dated_extract_dir(media_type: str) -> str:
    base_dir = current_app.config['MEDIA_FOLDERS'][media_type]['extract']
    return _build_user_dated_dir(base_dir)

def ensure_ascii_local_copy(input_path: str, preferred_ext: Optional[str] = None) -> str:
    """如果路径包含非ASCII字符，则复制到临时目录中的ASCII文件名并返回新路径。
    否则直接返回原路径（转换为绝对路径以确保兼容性）。
    preferred_ext: 可选，强制使用的目标扩展名（不带点）。
    """
    try:
        # 转换为绝对路径，确保路径格式统一
        input_path_str = os.path.abspath(str(input_path))
        
        # 检查文件是否存在
        if not os.path.exists(input_path_str):
            # 如果文件不存在，尝试使用原始路径
            input_path_str = str(input_path)
        
        # 更严格的ASCII判断：检查路径中是否包含非ASCII字符
        # 使用try-except确保编码兼容性
        try:
            # 尝试将路径编码为系统默认编码，如果失败说明可能有编码问题
            input_path_str.encode('ascii')
            # 如果编码成功，说明是ASCII路径，但为了兼容性，仍需要转换为绝对路径
            return input_path_str
        except (UnicodeEncodeError, UnicodeDecodeError):
            # 包含非ASCII字符，需要复制到ASCII路径
            pass
    except Exception as e:
        # 如果判断失败，为了安全起见，走复制流程
        input_path_str = str(input_path)
    
    # 确保源文件存在
    if not os.path.exists(input_path_str):
        raise FileNotFoundError(f"源文件不存在: {input_path_str}")

    temp_root = current_app.config.get('TEMP_FOLDER')
    if not temp_root:
        temp_root = os.path.join(current_app.instance_path, 'temp')
    os.makedirs(temp_root, exist_ok=True)

    src_ext = os.path.splitext(input_path_str)[1]
    if preferred_ext:
        dst_ext = '.' + preferred_ext.lstrip('.').lower()
    else:
        dst_ext = src_ext if src_ext else ''

    ascii_name = f"tmp_{uuid.uuid4().hex}{dst_ext}"
    dst_path = os.path.join(temp_root, ascii_name)
    
    # 使用copy2保留文件元数据，并添加错误处理
    try:
        shutil.copy2(input_path_str, dst_path)
        # 验证复制是否成功
        if not os.path.exists(dst_path):
            raise IOError(f"文件复制失败: {dst_path}")
        return dst_path
    except Exception as e:
        # 如果复制失败，尝试使用原始路径（某些情况下可能仍然有效）
        raise IOError(f"无法复制文件到临时目录: {str(e)}") from e


def prepare_ascii_output_path(target_path: str) -> tuple[str, str]:
    """为输出准备安全路径。
    如果目标路径含非ASCII字符，则返回 (ascii临时路径, 最终路径)，调用方应先写入ascii临时路径，随后移动到最终路径。
    如果是ASCII路径，则返回 (目标路径, 目标路径)。
    """
    try:
        target_str = str(target_path)
        if all(ord(ch) < 128 for ch in target_str):
            return target_str, target_str
    except Exception:
        pass

    temp_root = current_app.config.get('TEMP_FOLDER')
    if not temp_root:
        temp_root = os.path.join(current_app.instance_path, 'temp')
    os.makedirs(temp_root, exist_ok=True)

    _, ext = os.path.splitext(target_path)
    ascii_name = f"out_{uuid.uuid4().hex}{ext}"
    ascii_temp = os.path.join(temp_root, ascii_name)
    return ascii_temp, target_path


def maybe_delete_temp(file_path: str) -> None:
    """如果文件位于应用的 TEMP_FOLDER 中则尝试删除。静默失败。"""
    try:
        if not file_path:
            return
        temp_root = current_app.config.get('TEMP_FOLDER')
        if not temp_root:
            temp_root = os.path.join(current_app.instance_path, 'temp')
        # 归一化比较
        fp = os.path.abspath(file_path)
        tr = os.path.abspath(temp_root)
        if fp.startswith(tr) and os.path.exists(fp) and os.path.isfile(fp):
            try:
                os.remove(fp)
            except Exception:
                pass
    except Exception:
        pass


