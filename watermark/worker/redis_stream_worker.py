"""
从 Redis Stream 消费水印嵌入任务，调用现有 process_watermark，并更新 MySQL + 任务态 Hash。

环境变量（与 Java 对齐）：
  WM_REDIS_HOST / WM_REDIS_PORT / WM_REDIS_PASSWORD
  WM_JOBS_STREAM_KEY（默认 wm:stream:watermark）
  WM_JOBS_CONSUMER_GROUP（默认 wm:workers）
  WM_JOBS_JOB_KEY_PREFIX（默认 wm:job:）
  SQLALCHEMY_DATABASE_URI、INSTANCE_PATH（与 Flask 一致）
  s3 输入时：WM_MINIO_ENDPOINT、WM_MINIO_ACCESS_KEY、WM_MINIO_SECRET_KEY、WM_MINIO_BUCKET、WM_MINIO_REGION
  或 COS：WM_STORAGE_BACKEND=cos 时使用 WM_COS_*（与 Java 相同 bucket/region 语义）

运行：
  python -m watermark.worker.redis_stream_worker
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
import uuid
from typing import Any, Optional

import redis

STREAM_KEY = os.environ.get("WM_JOBS_STREAM_KEY", "wm:stream:watermark")
CONSUMER_GROUP = os.environ.get("WM_JOBS_CONSUMER_GROUP", "wm:workers")
JOB_PREFIX = os.environ.get("WM_JOBS_JOB_KEY_PREFIX", "wm:job:")
CONSUMER_NAME = os.environ.get("WM_WORKER_CONSUMER_NAME", f"wm-py-{uuid.uuid4().hex[:8]}")


def _redis_client() -> redis.Redis:
    host = os.environ.get("WM_REDIS_HOST", "localhost")
    port = int(os.environ.get("WM_REDIS_PORT", "6379"))
    password = os.environ.get("WM_REDIS_PASSWORD") or None
    return redis.Redis(host=host, port=port, password=password, decode_responses=True)


def _ensure_group(r: redis.Redis) -> None:
    try:
        r.xgroup_create(STREAM_KEY, CONSUMER_GROUP, id="0", mkstream=True)
    except redis.ResponseError as e:
        if "BUSYGROUP" not in str(e).upper():
            raise


def _job_key(job_id: str) -> str:
    return f"{JOB_PREFIX}{job_id}"


def _hset_job(r: redis.Redis, job_id: str, **fields: str) -> None:
    now = str(int(time.time() * 1000))
    m = {k: str(v) for k, v in fields.items()}
    m["updatedAt"] = now
    r.hset(_job_key(job_id), mapping=m)


def _download_s3_to_temp(bucket: str, key: str, suffix: str) -> str:
    import boto3
    from botocore.client import Config

    backend = (os.environ.get("WM_STORAGE_BACKEND") or "minio").lower()
    if backend == "cos":
        region = os.environ.get("WM_COS_REGION", "ap-guangzhou")
        bucket_name = os.environ.get("WM_COS_BUCKET", bucket)
        sid = os.environ.get("WM_COS_SECRET_ID", "")
        sk = os.environ.get("WM_COS_SECRET_KEY", "")
        endpoint = f"https://cos.{region}.myqcloud.com"
        client = boto3.client(
            "s3",
            region_name=region,
            endpoint_url=endpoint,
            aws_access_key_id=sid,
            aws_secret_access_key=sk,
            config=Config(signature_version="s3v4", s3={"addressing_style": "virtual"}),
        )
    else:
        endpoint = os.environ.get("WM_MINIO_ENDPOINT", "http://127.0.0.1:9000")
        ak = os.environ.get("WM_MINIO_ACCESS_KEY", "minioadmin")
        sk = os.environ.get("WM_MINIO_SECRET_KEY", "minioadmin")
        region = os.environ.get("WM_MINIO_REGION", "us-east-1")
        client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=ak,
            aws_secret_access_key=sk,
            region_name=region,
            config=Config(signature_version="s3v4"),
        )
        bucket_name = os.environ.get("WM_MINIO_BUCKET", bucket)
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    client.download_file(bucket_name or bucket, key, path)
    return path


def _upload_file_to_s3(local_path: str, object_key: str) -> str:
    import boto3
    from botocore.client import Config

    backend = (os.environ.get("WM_STORAGE_BACKEND") or "minio").lower()
    if backend == "cos":
        region = os.environ.get("WM_COS_REGION", "ap-guangzhou")
        bucket = os.environ.get("WM_COS_BUCKET", "")
        sid = os.environ.get("WM_COS_SECRET_ID", "")
        sk = os.environ.get("WM_COS_SECRET_KEY", "")
        endpoint = f"https://cos.{region}.myqcloud.com"
        client = boto3.client(
            "s3",
            region_name=region,
            endpoint_url=endpoint,
            aws_access_key_id=sid,
            aws_secret_access_key=sk,
            config=Config(signature_version="s3v4", s3={"addressing_style": "virtual"}),
        )
    else:
        endpoint = os.environ.get("WM_MINIO_ENDPOINT", "http://127.0.0.1:9000")
        ak = os.environ.get("WM_MINIO_ACCESS_KEY", "minioadmin")
        sk = os.environ.get("WM_MINIO_SECRET_KEY", "minioadmin")
        region = os.environ.get("WM_MINIO_REGION", "us-east-1")
        bucket = os.environ.get("WM_MINIO_BUCKET", "watermark")
        client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=ak,
            aws_secret_access_key=sk,
            region_name=region,
            config=Config(signature_version="s3v4"),
        )
    extra = {}
    mime = "application/octet-stream"
    if local_path.lower().endswith((".jpg", ".jpeg")):
        mime = "image/jpeg"
    elif local_path.lower().endswith(".png"):
        mime = "image/png"
    elif local_path.lower().endswith(".mp4"):
        mime = "video/mp4"
    elif local_path.lower().endswith(".wav"):
        mime = "audio/wav"
    extra["ContentType"] = mime
    client.upload_file(local_path, bucket, object_key, ExtraArgs=extra)
    return f"s3://{bucket}/{object_key}"


def _resolve_input_path(payload: dict[str, Any]) -> tuple[str, Optional[str]]:
    """返回 (本地可读路径, 下载产生的临时路径或 None)。"""
    bucket = (payload.get("bucket") or "").strip()
    key = (payload.get("objectKey") or "").strip()
    if bucket and key:
        ext = os.path.splitext(key)[1] or ".bin"
        tmp = _download_s3_to_temp(bucket, key, ext)
        return tmp, tmp
    if key:
        return key, None
    raise ValueError("objectKey 为空")


def _process_one(SessionLocal, r: redis.Redis, payload: dict[str, Any]) -> None:
    from watermark.models import File as FileModel
    from watermark.utils.watermark_job_core import calculate_file_hash, process_watermark

    job_id = str(payload["jobId"])
    file_id = int(payload["fileId"])
    wm_text = payload.get("watermarkText") or ""
    seed = payload.get("watermarkSeed")

    session = SessionLocal()
    try:
        f = session.get(FileModel, file_id)
        if f is None:
            _hset_job(r, job_id, status="FAILED", errorMessage=f"file not found: {file_id}")
            return

        _hset_job(r, job_id, status="PROCESSING", errorMessage="")

        local_input: Optional[str] = None
        tmp_download: Optional[str] = None
        try:
            local_input, tmp_download = _resolve_input_path(payload)
        except Exception as e:
            f.processing_status = "failed"
            f.error_message = f"准备输入文件失败: {e}"
            session.commit()
            _hset_job(r, job_id, status="FAILED", errorMessage=str(e))
            return

        try:
            rnd = str(seed) if seed else None
            out = process_watermark(local_input, wm_text, "embed", file_id, rnd)
            if len(out) == 4:
                result_path, algorithm, err, _wm_hash = out
            else:
                result_path, algorithm, err = out  # type: ignore[misc]

            if err or not result_path:
                msg = err or "水印处理失败"
                f.processing_status = "failed"
                f.error_message = msg
                session.commit()
                _hset_job(r, job_id, status="FAILED", errorMessage=msg)
                return

            try:
                wm_hash = calculate_file_hash(result_path)
            except OSError:
                wm_hash = None

            final_path = result_path
            if (payload.get("bucket") or "").strip():
                import uuid as u

                base = os.path.basename(f.filename or "out.bin")
                out_key = f"wm/embeds/{file_id}/{u.uuid4().hex}_{base}"
                try:
                    final_path = _upload_file_to_s3(result_path, out_key)
                finally:
                    if os.path.isfile(result_path) and result_path != local_input:
                        try:
                            os.remove(result_path)
                        except OSError:
                            pass

            f.watermarked_path = final_path
            f.watermark_type = algorithm
            f.has_watermark = True
            f.processing_status = "completed"
            f.error_message = None
            f.file_watermark_hash = wm_hash

            session.commit()
            _hset_job(r, job_id, status="COMPLETED", errorMessage="")
        finally:
            if tmp_download and os.path.isfile(tmp_download):
                try:
                    os.remove(tmp_download)
                except OSError:
                    pass
    finally:
        session.close()


def main() -> None:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    uri = os.environ.get("SQLALCHEMY_DATABASE_URI")
    if not uri:
        raise SystemExit("SQLALCHEMY_DATABASE_URI is required")

    engine = create_engine(uri, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    r = _redis_client()
    _ensure_group(r)

    block_ms = int(os.environ.get("WM_WORKER_BLOCK_MS", "5000"))

    print(f"worker started stream={STREAM_KEY} group={CONSUMER_GROUP} name={CONSUMER_NAME}", flush=True)

    while True:
        try:
            resp = r.xreadgroup(
                CONSUMER_GROUP,
                CONSUMER_NAME,
                {STREAM_KEY: ">"},
                count=1,
                block=block_ms,
            )
        except redis.ConnectionError as e:
            print(f"redis connection error: {e}, retry", flush=True)
            time.sleep(2)
            continue

        if not resp:
            continue

        for _stream, messages in resp:
            for msg_id, data in messages:
                raw = data.get("payload") or data.get("data") or "{}"
                try:
                    payload = json.loads(raw)
                except json.JSONDecodeError as e:
                    print(f"bad json id={msg_id}: {e}", flush=True)
                    r.xack(STREAM_KEY, CONSUMER_GROUP, msg_id)
                    continue
                try:
                    _process_one(SessionLocal, r, payload)
                except Exception as e:
                    print(f"job error id={msg_id}: {e}", flush=True)
                    job_id = str(payload.get("jobId", ""))
                    if job_id:
                        _hset_job(r, job_id, status="FAILED", errorMessage=str(e))
                r.xack(STREAM_KEY, CONSUMER_GROUP, msg_id)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
