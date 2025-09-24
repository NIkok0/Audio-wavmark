import os
import time
from datetime import datetime, timezone
from typing import Optional
try:
    # Python 3.9+
    from zoneinfo import ZoneInfo  # type: ignore
except Exception:
    ZoneInfo = None  # type: ignore

try:
    import requests  # type: ignore
except Exception:  # requests 不一定存在于离线环境，运行时再说
    requests = None  # type: ignore


_CACHE_TTL_SECONDS = 60
_cache_expires_at: float = 0.0
_cache_now_utc: Optional[datetime] = None
_local_tz_cache: Optional[timezone] = None


def _parse_datetime_from_response(resp) -> Optional[datetime]:
    """尽量从常见字段/头部解析 UTC 时间，解析失败返回 None。"""
    # 1) 优先解析 JSON 常见字段
    try:
        data = resp.json()
        # 常见字段集合
        for key in [
            "utc", "now", "datetime", "currentDateTime", "iso", "timestamp",
        ]:
            if key in data and isinstance(data[key], str):
                try:
                    # 兼容 ISO-8601 格式
                    dt = datetime.fromisoformat(data[key].replace("Z", "+00:00"))
                    return dt.astimezone(timezone.utc)
                except Exception:
                    pass
        # epoch 秒/毫秒
        if "epoch_ms" in data and isinstance(data["epoch_ms"], (int, float)):
            return datetime.fromtimestamp(float(data["epoch_ms"]) / 1000.0, tz=timezone.utc)
        if "epoch" in data and isinstance(data["epoch"], (int, float)):
            return datetime.fromtimestamp(float(data["epoch"]), tz=timezone.utc)
    except Exception:
        pass

    # 2) 回退使用 Date 响应头
    try:
        date_header = resp.headers.get("Date")
        if date_header:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(date_header)
            return dt.astimezone(timezone.utc)
    except Exception:
        pass

    return None


def _fetch_now_utc_from_api() -> Optional[datetime]:
    url = os.environ.get("COMMON_TIME_API_URL") or os.environ.get("TIME_API_URL")
    if not url or not requests:
        return None
    try:
        resp = requests.get(url, timeout=2.0)
        resp.raise_for_status()
        dt = _parse_datetime_from_response(resp)
        return dt
    except Exception:
        return None


def get_now_utc() -> datetime:
    """统一获取 UTC 时间：优先使用公共时间 API（带 60s 缓存），失败回退到本机 UTC。

    返回 naive UTC（无 tzinfo），以兼容现有 SQLAlchemy DateTime 字段。
    """
    global _cache_expires_at, _cache_now_utc
    now_ts = time.time()
    if _cache_now_utc is None or now_ts >= _cache_expires_at:
        dt = _fetch_now_utc_from_api()
        if dt is None:
            dt = datetime.utcnow().replace(tzinfo=timezone.utc)
        _cache_now_utc = dt
        _cache_expires_at = now_ts + _CACHE_TTL_SECONDS

    # 转为 naive UTC，避免和现有 schema 冲突
    naive_utc = _cache_now_utc.astimezone(timezone.utc).replace(tzinfo=None)
    return naive_utc


def _get_local_tz() -> timezone:
    """获取本地显示时区，默认 Asia/Shanghai，可通过 APP_TIMEZONE 覆盖。"""
    global _local_tz_cache
    if _local_tz_cache is not None:
        return _local_tz_cache
    tz_name = os.environ.get("APP_TIMEZONE", "Asia/Shanghai")
    if ZoneInfo is not None:
        try:
            _local_tz_cache = ZoneInfo(tz_name)  # type: ignore
            return _local_tz_cache
        except Exception:
            pass
    # 回退本机本地时区（不精确，但避免报错）
    _local_tz_cache = datetime.now().astimezone().tzinfo or timezone.utc
    return _local_tz_cache  # type: ignore


def to_local_time(dt: Optional[datetime], fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """将数据库中的 UTC 时间（naive 或 aware）格式化为本地时区字符串。

    - None 返回空串
    - naive 视为 UTC
    - aware 若非 UTC，先转换至 UTC 再到本地（保证一致）
    """
    if dt is None:
        return ""
    # 规范化成 UTC aware
    if dt.tzinfo is None:
        dt_aware = dt.replace(tzinfo=timezone.utc)
    else:
        dt_aware = dt.astimezone(timezone.utc)
    local_dt = dt_aware.astimezone(_get_local_tz())
    try:
        return local_dt.strftime(fmt)
    except Exception:
        return local_dt.isoformat()


