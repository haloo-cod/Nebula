"""
图片上传 service — 本地文件存储
未来切 R2 时替换此文件即可
"""

import uuid
from datetime import datetime
from pathlib import Path

from fastapi import UploadFile

from app.config import settings


def generate_upload_path(original_name: str) -> tuple[str, str]:
    """
    生成上传路径：uploads/images/{year}/{month}/{uuid}_{name}
    返回 (相对路径, 完整 URL)
    """
    now = datetime.now()
    ext = Path(original_name).suffix.lower()
    unique_name = f"{uuid.uuid4().hex[:12]}_{Path(original_name).stem}{ext}"
    relative_dir = f"images/{now.year}/{now.month:02d}"
    relative_path = f"{relative_dir}/{unique_name}"
    return relative_path, f"/uploads/{relative_path}"


async def save_upload_file(file: UploadFile, relative_path: str) -> int:
    """
    保存上传文件到本地磁盘
    返回文件大小（bytes）
    """
    full_path = settings.UPLOAD_DIR / relative_path
    full_path.parent.mkdir(parents=True, exist_ok=True)

    content = await file.read()
    full_path.write_bytes(content)
    return len(content)


def delete_file(relative_path: str) -> None:
    """删除本地文件"""
    full_path = settings.UPLOAD_DIR / relative_path
    if full_path.exists():
        full_path.unlink()
