"""
Worker 使用的最小 ORM：仅映射 files 表（无 Flask-SQLAlchemy）。
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class File(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_path: Mapped[str] = mapped_column(String(512), nullable=False)
    watermarked_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    file_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    file_watermark_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    has_watermark: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)
    file_format: Mapped[str] = mapped_column(String(20), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    watermark_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    watermark_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    original_watermark_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    watermark_seed: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    processing_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    uploader_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    group_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("groups.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
