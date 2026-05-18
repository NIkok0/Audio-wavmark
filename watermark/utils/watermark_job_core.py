"""水印任务核心逻辑（供 Redis Worker 使用，不依赖 Flask / views）。"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Optional

from watermark.utils.algorithm_selector import AlgorithmSelector


def calculate_file_hash(file_path: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def process_watermark(
    file_path: str,
    watermark_text: str,
    operation_type: str = "embed",
    file_id: Any = None,
    random_seed: Any = None,
):
    """
    与历史 views.process_watermark 对齐的 Worker 子集：仅 embed 在队列中使用。
    extract 分支依赖 ORM 中的 File 记录，若在无会话环境下调用需自行传入上下文（当前 Worker 未使用）。
    """
    try:
        selector = AlgorithmSelector()
        if operation_type == "embed":
            if random_seed:
                result = selector.select_algorithm(file_path, watermark_text, random_seed)
                return result.get("result"), result.get("algorithm"), None, result.get("watermark_hash")
            result = selector.select_algorithm(file_path, watermark_text)
            return result.get("result"), result.get("algorithm"), None
        if operation_type == "extract":
            raise NotImplementedError("extract 请在有完整 ORM 会话的上下文中实现（Worker 仅 embed）")
        return None, None, f"未知操作: {operation_type}"
    except Exception as e:
        return None, None, str(e)
