"""
通用文件存储 service — 任意类型文件的分块写入与删除
"""

import uuid
from pathlib import Path

from fastapi import UploadFile

from app.config import settings


CHUNK_SIZE = 1024 * 1024


def generate_file_path(original_name: str) -> str:
    """生成安全且不重复的 files 相对路径，并保留原始扩展名。"""

    safe_name = Path(original_name).name or "download"
    suffixes = "".join(Path(safe_name).suffixes)
    return f"files/{uuid.uuid4().hex}{suffixes}"


async def save_file(file: UploadFile, relative_path: str) -> int:
    """按块保存上传文件，返回文件大小，不对文件类型和大小设应用层限制。"""

    full_path = settings.UPLOAD_DIR / relative_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    file_size = 0

    try:
        with full_path.open("wb") as target:
            while chunk := await file.read(CHUNK_SIZE):
                target.write(chunk)
                file_size += len(chunk)
    except Exception:
        full_path.unlink(missing_ok=True)
        raise

    return file_size


def get_file_path(relative_path: str) -> Path:
    """返回上传文件的绝对路径。"""

    return settings.UPLOAD_DIR / relative_path


def delete_file(relative_path: str) -> None:
    """删除磁盘上的上传文件。"""

    get_file_path(relative_path).unlink(missing_ok=True)
