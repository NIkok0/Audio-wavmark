"""
无 Flask 时的实例路径与媒体目录（与历史 app.config 语义一致，供 Worker + utils 使用）。

环境变量：
  INSTANCE_PATH 或 WM_INSTANCE_PATH — 存储根（默认 instance）
  WM_WORKER_FS_USERNAME — 写入按用户分目录时的用户名占位（默认 worker）
"""
from __future__ import annotations

import os


def get_instance_path() -> str:
    return os.environ.get("INSTANCE_PATH") or os.environ.get("WM_INSTANCE_PATH") or "instance"


def get_temp_folder() -> str:
    return os.path.join(get_instance_path(), "temp")


def get_logs_folder() -> str:
    return os.path.join(get_instance_path(), "logs")


def get_media_folders() -> dict[str, dict[str, str]]:
    """与 Flask __init__.py 中 MEDIA_FOLDERS 结构一致。"""
    root = get_instance_path()
    return {
        "image": {
            "upload": os.path.join(root, "uploads", "images"),
            "extract": os.path.join(root, "extracts", "images"),
            "embed": os.path.join(root, "embeds", "images"),
        },
        "audio": {
            "upload": os.path.join(root, "uploads", "audio"),
            "extract": os.path.join(root, "extracts", "audio"),
            "embed": os.path.join(root, "embeds", "audio"),
        },
        "video": {
            "upload": os.path.join(root, "uploads", "video"),
            "extract": os.path.join(root, "extracts", "video"),
            "embed": os.path.join(root, "embeds", "video"),
        },
        "text": {
            "upload": os.path.join(root, "uploads", "documents"),
            "extract": os.path.join(root, "extracts", "documents"),
            "embed": os.path.join(root, "embeds", "documents"),
        },
    }


def get_fs_username_for_paths() -> str:
    """无登录用户时用于 get_user_dated_* 目录名。"""
    return (os.environ.get("WM_WORKER_FS_USERNAME") or "worker").strip() or "worker"


def ensure_base_directories() -> None:
    """确保 temp / logs 及媒体根目录存在。"""
    for d in (get_temp_folder(), get_logs_folder()):
        os.makedirs(d, mode=0o755, exist_ok=True)
    for _mt, folders in get_media_folders().items():
        for _k, path in folders.items():
            os.makedirs(path, mode=0o755, exist_ok=True)
