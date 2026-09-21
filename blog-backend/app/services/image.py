"""
图片上传服务 — 支持本地存储和 R2
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


async def save_upload_file(
    file: UploadFile,
    relative_path: str,
    storage_backend: str = "local"
) -> int:
    """
    保存上传文件（支持本地或 R2）
    返回文件大小（bytes）
    """
    if storage_backend == "r2" and settings.R2_ENABLED:
        from app.services.r2_storage import get_r2_client
        r2 = get_r2_client()
        return await r2.upload_file(relative_path, file, content_type=file.content_type)
    else:
        # 本地存储
        full_path = settings.UPLOAD_DIR / relative_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        content = await file.read()
        full_path.write_bytes(content)
        return len(content)


def delete_file(relative_path: str, storage_backend: str = "local") -> None:
    """删除文件（支持本地/R2）"""
    if storage_backend == "r2" and settings.R2_ENABLED:
        from app.services.r2_storage import get_r2_client
        r2 = get_r2_client()
        r2.delete_file(relative_path)
    else:
        full_path = settings.UPLOAD_DIR / relative_path
        if full_path.exists():
            full_path.unlink()
