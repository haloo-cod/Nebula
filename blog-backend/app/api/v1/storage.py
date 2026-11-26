"""管理员专用的本地 / R2 目录浏览接口。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.database import get_db
from app.schemas.storage import StorageBrowseResponse, StorageRoot
from app.services.storage_browser import browse_storage


router = APIRouter(prefix="/storage", tags=["文件目录"])


@router.get("/browse", response_model=StorageBrowseResponse)
async def list_storage_directory(
    root: StorageRoot = "uploads",
    path: str = Query("", max_length=2048),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    """返回直接子目录及分页文件；R2 信息来自数据库，不探测远程存储桶。"""
    return await browse_storage(db, root, path, page, page_size)
