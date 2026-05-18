import os
import re
import shutil
import uuid
from typing import Optional

from watermark.runtime_paths import (
    get_fs_username_for_paths,
    get_media_folders,
    get_temp_folder,
)
from watermark.utils.time_provider import get_now_utc


def _secure_filename_with_chinese(filename: str) -> str:
    """保留中文与常见字符的安全文件名转换。"""
    return re.sub(r"[^\u4e00-\u9fa5A-Za-z0-9_.\-]", "_", filename or "anonymous").strip("._") or "anonymous"


def _build_user_dated_dir(base_dir: str) -> str:
    username = get_fs_username_for_paths()
    user_dir_name = _secure_filename_with_chinese(username)
    date_dir_name = get_now_utc().strftime("%Y%m%d")
    target_dir = os.path.join(base_dir, user_dir_name, date_dir_name)
    os.makedirs(target_dir, mode=0o755, exist_ok=True)
    return target_dir


def get_user_dated_upload_dir(media_type: str) -> str:
    base_dir = get_media_folders()[media_type]["upload"]
    return _build_user_dated_dir(base_dir)


def get_user_dated_embed_dir(media_type: str) -> str:
    base_dir = get_media_folders()[media_type]["embed"]
    return _build_user_dated_dir(base_dir)


def get_user_dated_extract_dir(media_type: str) -> str:
    base_dir = get_media_folders()[media_type]["extract"]
    return _build_user_dated_dir(base_dir)


def ensure_ascii_local_copy(input_path: str, preferred_ext: Optional[str] = None) -> str:
    """如果路径包含非ASCII字符，则复制到临时目录中的ASCII文件名并返回新路径。"""
    try:
        input_path_str = os.path.abspath(str(input_path))
        if not os.path.exists(input_path_str):
            input_path_str = str(input_path)
        try:
            input_path_str.encode("ascii")
            return input_path_str
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    except Exception:
        input_path_str = str(input_path)

    if not os.path.exists(input_path_str):
        raise FileNotFoundError(f"源文件不存在: {input_path_str}")

    temp_root = get_temp_folder()
    os.makedirs(temp_root, exist_ok=True)

    src_ext = os.path.splitext(input_path_str)[1]
    if preferred_ext:
        dst_ext = "." + preferred_ext.lstrip(".").lower()
    else:
        dst_ext = src_ext if src_ext else ""

    ascii_name = f"tmp_{uuid.uuid4().hex}{dst_ext}"
    dst_path = os.path.join(temp_root, ascii_name)

    try:
        shutil.copy2(input_path_str, dst_path)
        if not os.path.exists(dst_path):
            raise OSError(f"文件复制失败: {dst_path}")
        return dst_path
    except Exception as e:
        raise OSError(f"无法复制文件到临时目录: {str(e)}") from e


def prepare_ascii_output_path(target_path: str) -> tuple[str, str]:
    try:
        target_str = str(target_path)
        if all(ord(ch) < 128 for ch in target_str):
            return target_str, target_str
    except Exception:
        pass

    temp_root = get_temp_folder()
    os.makedirs(temp_root, exist_ok=True)

    _, ext = os.path.splitext(target_path)
    ascii_name = f"out_{uuid.uuid4().hex}{ext}"
    ascii_temp = os.path.join(temp_root, ascii_name)
    return ascii_temp, target_path


def maybe_delete_temp(file_path: str) -> None:
    try:
        if not file_path:
            return
        temp_root = get_temp_folder()
        fp = os.path.abspath(file_path)
        tr = os.path.abspath(temp_root)
        if fp.startswith(tr) and os.path.exists(fp) and os.path.isfile(fp):
            try:
                os.remove(fp)
            except OSError:
                pass
    except Exception:
        pass
