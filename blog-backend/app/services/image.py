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


def resolve_upload_path(relative_path: str) -> Path:
    """解析上传目录内的相对路径，拒绝绝对路径、空段和越界符号链接。"""
    if Path(relative_path).is_absolute() or any(not part for part in relative_path.replace("\\", "/").split("/")):
        raise ValueError("上传文件路径越界")
    result = (settings.UPLOAD_DIR / relative_path).resolve()
    if not result.is_relative_to(settings.UPLOAD_DIR.resolve()):
        raise ValueError("上传文件路径越界")
    return result


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
        full_path = resolve_upload_path(relative_path)
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
        resolve_upload_path(relative_path).unlink(missing_ok=True)
