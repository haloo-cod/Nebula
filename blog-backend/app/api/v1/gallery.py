"""
展览页路由 — Gallery CRUD
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.database import get_db
from app.models.gallery import GalleryProject
from app.models.user import User
from app.schemas.gallery import (
    GalleryCreate,
    GalleryDetail,
    GalleryListItem,
    GalleryUpdate,
)
from app.services.gallery import (
    delete_md_file,
    read_md_file,
    render_gallery_content,
    slug_to_filename,
    write_md_file,
)

router = APIRouter(prefix="/gallery", tags=["展览"])


@router.get("", response_model=list[GalleryListItem])
async def list_gallery(db: AsyncSession = Depends(get_db)):
    """获取展览项目列表"""
    result = await db.execute(
        select(GalleryProject).order_by(GalleryProject.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/{slug}", response_model=GalleryDetail)
async def get_gallery_project(slug: str, db: AsyncSession = Depends(get_db)):
    """获取展览项目详情（含 Markdown 原文）"""
    result = await db.execute(select(GalleryProject).where(GalleryProject.slug == slug))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")

    content_md = read_md_file(project.md_filename) if project.md_filename else ""

    return GalleryDetail(
        id=project.id,
        slug=project.slug,
        title=project.title,
        description=project.description,
        tags=project.tags,
        status=project.status,
        year=project.year,
        is_featured=project.is_featured,
        content_md=content_md,
        content_html=project.content_html,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.post("", response_model=GalleryDetail, status_code=status.HTTP_201_CREATED)
async def create_gallery_project(
    body: GalleryCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """创建展览项目"""
    existing = await db.execute(select(GalleryProject).where(GalleryProject.slug == body.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="slug 已存在")

    md_filename = slug_to_filename(body.slug)
    if body.content_md:
        write_md_file(md_filename, body.content_md)

    content_html = render_gallery_content(body.content_md) if body.content_md else ""

    project = GalleryProject(
        slug=body.slug,
        title=body.title,
        description=body.description,
        tags=body.tags,
        status=body.status,
        year=body.year,
        is_featured=body.is_featured,
        content_html=content_html,
        md_filename=md_filename,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)

    return GalleryDetail(
        id=project.id,
        slug=project.slug,
        title=project.title,
        description=project.description,
        tags=project.tags,
        status=project.status,
        year=project.year,
        is_featured=project.is_featured,
        content_md=body.content_md,
        content_html=content_html,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.put("/{slug}", response_model=GalleryDetail)
async def update_gallery_project(
    slug: str,
    body: GalleryUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """更新展览项目"""
    result = await db.execute(select(GalleryProject).where(GalleryProject.slug == slug))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")

    if body.title is not None:
        project.title = body.title
    if body.description is not None:
        project.description = body.description
    if body.tags is not None:
        project.tags = body.tags
    if body.status is not None:
        project.status = body.status
    if body.year is not None:
        project.year = body.year
    if body.is_featured is not None:
        project.is_featured = body.is_featured

    content_md = ""
    if body.content_md is not None:
        md_filename = project.md_filename or slug_to_filename(slug)
        write_md_file(md_filename, body.content_md)
        project.content_html = render_gallery_content(body.content_md)
        project.md_filename = md_filename
        content_md = body.content_md
    else:
        content_md = read_md_file(project.md_filename) if project.md_filename else ""

    await db.commit()
    await db.refresh(project)

    return GalleryDetail(
        id=project.id,
        slug=project.slug,
        title=project.title,
        description=project.description,
        tags=project.tags,
        status=project.status,
        year=project.year,
        is_featured=project.is_featured,
        content_md=content_md,
        content_html=project.content_html,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_gallery_project(
    slug: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """删除展览项目"""
    result = await db.execute(select(GalleryProject).where(GalleryProject.slug == slug))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")

    if project.md_filename:
        delete_md_file(project.md_filename)

    await db.delete(project)
    await db.commit()
