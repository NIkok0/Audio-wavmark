"""
数字水印 Python 包（Worker 与算法 utils）。

不再初始化 Flask 应用。Worker 入口：
  python -m watermark.worker.redis_stream_worker

启动前请设置 SQLALCHEMY_DATABASE_URI；可选 INSTANCE_PATH / WM_INSTANCE_PATH、WM_WORKER_FS_USERNAME。
"""

from watermark.runtime_paths import ensure_base_directories

ensure_base_directories()
