"""
图书路由 — Books CRUD 与下载
"""

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.database import get_db
from app.models.book import Book
from app.models.book_download import BookDownloadJob
from app.models.user import User
from app.schemas.book import (
    BookDetail,
    BookCoverCandidate,
    BookCoverSelection,
    BookListItem,
    BookListResponse,
    BookReorderRequest,
    BookUpdate,
)
from app.schemas.book_download import (
    BookDownloadJobCreate,
    BookDownloadJobExtend,
    BookDownloadJobListResponse,
    BookDownloadJobResponse,
)
from app.services.book import (
    BOOKS_DIR,
    extract_cover_image,
    get_epub_files,
    list_cover_candidates,
    read_epub_metadata,
    save_epub_upload,
    select_cover_image,
    delete_book_files,
    slugify,
)
from app.services.book_download import archive_path, existing_archive_path, normalize_utc, process_book_download_job
from app.models.treasure import Treasure
from app.models.analytics import AnalyticsEvent
from app.services.analytics import get_client_ip, hash_ip, utc_now

router = APIRouter(prefix="/books", tags=["图书"])


def _download_name(book: Book) -> str:
    """生成安全的 EPUB 下载文件名。"""
    value = re.sub(r'[\\/:*?"<>|\x00-\x1f]+', "_", f"{book.title} - {book.author}".strip(" -"))
    return f"{value or book.slug}.epub"


def _archive_name(value: str) -> str:
    """清理管理员填写的 ZIP 文件名，避免路径注入和重复扩展名。"""
    cleaned = re.sub(r'[\\/:*?"<>|\x00-\x1f]+', "_", value.strip()).strip(" .")
    cleaned = re.sub(r"\.zip$", "", cleaned, flags=re.IGNORECASE).strip(" .")
    return (cleaned or "starlit-books")[:150]


def _book_path(book: Book):
    """解析图书文件路径，并确保文件位于图书存储目录内。"""
    path = BOOKS_DIR / f"{book.slug}.epub"
    try:
        path.resolve().relative_to(BOOKS_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="图书文件路径无效")
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图书文件不存在")
    return path


@router.post("/download-jobs", response_model=BookDownloadJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_book_download_job(
    data: BookDownloadJobCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    """创建批量下载任务，打包工作在响应返回后执行。"""
    unique_slugs = list(dict.fromkeys(data.slugs))
    if not unique_slugs or len(unique_slugs) > 100:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="一次最多选择 100 本图书")
    result = await db.execute(select(Book).where(Book.slug.in_(unique_slugs)))
    books = list(result.scalars().all())
    if len(books) != len(unique_slugs):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="部分图书不存在")
    job = BookDownloadJob(
        user_id=user.id,
        slugs_json=json.dumps(unique_slugs),
        total_books=len(unique_slugs),
        archive_name=_archive_name(data.archive_name),
        expire_days=data.expire_days,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    background_tasks.add_task(process_book_download_job, job.id)
    return _job_response(job)


def _job_response(job: BookDownloadJob) -> BookDownloadJobResponse:
    """将任务模型转换为前端状态响应。"""
    progress = round(job.completed_books / job.total_books * 100) if job.total_books else 0
    expires_at = normalize_utc(job.expires_at)
    is_expired = bool(expires_at and expires_at < datetime.now(timezone.utc))
    has_file = existing_archive_path(job) is not None
    display_status = "expired" if job.status == "completed" and is_expired else job.status
    if display_status == "completed" and not has_file:
        display_status = "missing"
    download_url = (
        f"/api/v1/books/download-jobs/{job.id}/file"
        if display_status == "completed"
        else None
    )
    return BookDownloadJobResponse(
        id=job.id, status=display_status, total_books=job.total_books,
        completed_books=job.completed_books, progress=progress, file_size=job.file_size,
        error_message=job.error_message,
        archive_name=job.archive_name,
        expire_days=job.expire_days,
        expires_at=expires_at,
        download_url=download_url,
        created_at=normalize_utc(job.created_at),
    )


@router.get("/download-jobs/{job_id}", response_model=BookDownloadJobResponse)
async def get_book_download_job(job_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(require_admin)):
    """查询管理员创建的批量下载任务。"""
    job = await db.get(BookDownloadJob, job_id)
    if not job or job.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="下载任务不存在")
    return _job_response(job)


@router.get("/download-jobs", response_model=BookDownloadJobListResponse)
async def list_book_download_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    """获取当前管理员创建的图书归档历史。"""
    count = await db.execute(
        select(func.count(BookDownloadJob.id)).where(BookDownloadJob.user_id == user.id)
    )
    total = count.scalar() or 0
    result = await db.execute(
        select(BookDownloadJob)
        .where(BookDownloadJob.user_id == user.id)
        .order_by(BookDownloadJob.created_at.desc(), BookDownloadJob.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return BookDownloadJobListResponse(
        items=[_job_response(job) for job in result.scalars().all()],
        total=total,
    )


@router.post("/download-jobs/{job_id}/retry", response_model=BookDownloadJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def retry_book_download_job(
    job_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    """重新生成已完成、已过期或失败的图书归档。"""
    job = await db.get(BookDownloadJob, job_id)
    if not job or job.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="下载任务不存在")
    if job.status in {"pending", "running"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="任务正在打包中")
    background_tasks.add_task(process_book_download_job, job.id)
    job.status = "pending"
    await db.commit()
    await db.refresh(job)
    return _job_response(job)


@router.patch("/download-jobs/{job_id}/expires", response_model=BookDownloadJobResponse)
async def extend_book_download_job(
    job_id: int,
    data: BookDownloadJobExtend,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    """手动调整图书归档到期日期。"""
    job = await db.get(BookDownloadJob, job_id)
    if not job or job.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="下载任务不存在")
    if job.status != "completed" or existing_archive_path(job) is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="归档文件已不可延期")
    expires_at = datetime.combine(data.expires_on, datetime.max.time(), tzinfo=timezone.utc)
    if expires_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="到期日期必须晚于今天")
    job.expires_at = expires_at.replace(microsecond=0)
    job.expire_days = max(1, (data.expires_on - datetime.now(timezone.utc).date()).days)
    job.status = "completed"
    await db.commit()
    await db.refresh(job)
    return _job_response(job)


@router.delete("/download-jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book_download_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    """删除图书归档历史和对应的 ZIP 文件。"""
    job = await db.get(BookDownloadJob, job_id)
    if not job or job.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="下载任务不存在")
    mounted = await db.execute(
        select(Treasure.id)
        .where(
            or_(
                Treasure.download_file.like(f"%/archive/{job.id}/download%"),
                Treasure.download_file.like(f"%archive={job.id}"),
            )
        )
        .limit(1)
    )
    if mounted.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该归档已挂载到藏宝阁，请先解除挂载")
    archive_path(job.id).unlink(missing_ok=True)
    await db.delete(job)
    await db.commit()


@router.get("/download-jobs/{job_id}/file", response_class=FileResponse)
async def download_book_job_file(job_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(require_admin)):
    """下载已完成的 ZIP，并拒绝过期任务。"""
    job = await db.get(BookDownloadJob, job_id)
    if not job or job.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="下载任务不存在")
    path = existing_archive_path(job)
    if job.status != "completed" or path is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="ZIP 尚未准备好")
    expires_at = normalize_utc(job.expires_at)
    if expires_at and expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="ZIP 已过期，请重新打包")
    return FileResponse(path, filename=f"{_archive_name(job.archive_name)}.zip", media_type="application/zip")


@router.get("/{slug}/download", response_class=FileResponse)
async def download_book(
    slug: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    """下载单本 EPUB。"""
    result = await db.execute(select(Book).where(Book.slug == slug))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图书不存在")
    ip_address = get_client_ip(request)
    ip_hash = hash_ip(ip_address)
    since = utc_now() - timedelta(hours=1)
    recent = await db.execute(
        select(func.count(AnalyticsEvent.id)).where(
            AnalyticsEvent.event_type == "book_download",
            AnalyticsEvent.ip_hash == ip_hash,
            AnalyticsEvent.occurred_at >= since,
        )
    )
    if int(recent.scalar() or 0) >= 20:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="下载过于频繁，请稍后再试")
    db.add(
        AnalyticsEvent(
            event_type="book_download",
            path=f"/api/v1/books/{slug}/download",
            title=book.title,
            user_agent=request.headers.get("user-agent", "")[:1000],
            ip_address=ip_address,
            ip_hash=ip_hash,
            user_id=user.id,
            occurred_at=utc_now(),
        )
    )
    await db.commit()
    return FileResponse(_book_path(book), filename=_download_name(book), media_type="application/epub+zip")


@router.get("/{slug}/read", response_class=FileResponse)
async def read_book(slug: str, request: Request, db: AsyncSession = Depends(get_db)):
    """公开提供 EPUB 阅读内容，不开放附件下载。"""
    result = await db.execute(select(Book).where(Book.slug == slug))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图书不存在")
    ip_address = get_client_ip(request)
    ip_hash = hash_ip(ip_address)
    since = utc_now() - timedelta(minutes=10)
    recent = await db.execute(
        select(func.count(AnalyticsEvent.id)).where(
            AnalyticsEvent.event_type == "book_open",
            AnalyticsEvent.ip_hash == ip_hash,
            AnalyticsEvent.path == f"/api/v1/books/{slug}/read",
            AnalyticsEvent.occurred_at >= since,
        )
    )
    if int(recent.scalar() or 0) >= 10:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="访问过于频繁，请稍后再试")
    db.add(
        AnalyticsEvent(
            event_type="book_open",
            path=f"/api/v1/books/{slug}/read",
            title=book.title,
            user_agent=request.headers.get("user-agent", "")[:1000],
            ip_address=ip_address,
            ip_hash=ip_hash,
            occurred_at=utc_now(),
        )
    )
    await db.commit()
    return FileResponse(_book_path(book), media_type="application/epub+zip", content_disposition_type="inline")


@router.get("", response_model=BookListResponse)
async def list_books(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str | None = Query(None, description="搜索关键词（标题/作者模糊匹配）"),
    sort: str = Query("newest", pattern="^(newest|oldest|custom)$"),
    db: AsyncSession = Depends(get_db),
):
    """获取图书列表（分页 + 搜索 + 排序）。"""
    stmt = select(Book)

    if keyword:
        pattern = f"%{keyword}%"
        stmt = stmt.where(
            or_(
                Book.title.ilike(pattern),
                Book.author.ilike(pattern),
            )
        )

    if sort == "oldest":
        stmt = stmt.order_by(Book.created_at.asc(), Book.id.asc())
    elif sort == "custom":
        stmt = stmt.order_by(Book.sort_order.asc(), Book.created_at.desc())
    else:
        stmt = stmt.order_by(Book.created_at.desc(), Book.id.desc())

    # 总数
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # 分页
    paged_stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(paged_stmt)
    items = list(result.scalars().all())

    return BookListResponse(items=items, total=total)


@router.get("/admin/all", response_model=list[BookListItem])
async def list_all_books_for_admin(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """获取全部图书，用于后台全局排序。"""

    result = await db.execute(
        select(Book).order_by(Book.sort_order.asc(), Book.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/{slug}", response_model=BookDetail)
async def get_book(slug: str, db: AsyncSession = Depends(get_db)):
    """获取图书详情"""
    result = await db.execute(select(Book).where(Book.slug == slug))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图书不存在")
    return book


@router.post("", response_model=BookDetail, status_code=status.HTTP_201_CREATED)
async def create_book(
    title: str = Form(""),
    author: str = Form(""),
    description: str = Form(""),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """上传 EPUB 并创建图书记录"""
    if not file.filename or not file.filename.lower().endswith(".epub"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="仅支持 EPUB 文件")

    slug = slugify(file.filename)
    filename = f"{slug}.epub"

    # 写盘前检查 slug，避免重复上传覆盖现有 EPUB
    existing = await db.execute(select(Book).where(Book.slug == slug))
    if existing.scalar_one_or_none():
        await file.close()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="slug 已存在")

    # 分块保存到临时文件，完整写入后再原子移动到正式路径
    internal_path = f"books/{filename}"
    await save_epub_upload(file, filename)

    try:
        # 提取元数据
        meta = read_epub_metadata(internal_path)
        book_title = title or meta.get("title") or slug
        book_author = author or meta.get("author") or ""

        # 提取封面
        cover_url = extract_cover_image(internal_path, slug)

        max_order = (await db.execute(select(func.max(Book.sort_order)))).scalar()
        book = Book(
            slug=slug,
            title=book_title,
            author=book_author,
            description=description or meta.get("description", ""),
            cover_url=cover_url,
            file_path=f"/uploads/books/{filename}",
            sort_order=(max_order + 1) if max_order is not None else 0,
        )
        db.add(book)
        await db.commit()
        await db.refresh(book)
        return book
    except Exception:
        await db.rollback()
        delete_book_files(slug)
        raise


@router.put("/reorder", status_code=status.HTTP_204_NO_CONTENT)
async def reorder_books(
    data: BookReorderRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """按 slug 列表保存全局排序。"""

    if len(data.slugs) != len(set(data.slugs)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="排序列表包含重复 slug")
    result = await db.execute(select(Book))
    books = list(result.scalars().all())
    book_map = {book.slug: book for book in books}
    if set(data.slugs) != set(book_map):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="排序列表与现有图书不一致")
    for index, slug in enumerate(data.slugs):
        book_map[slug].sort_order = index
    await db.commit()


@router.put("/{slug}", response_model=BookDetail)
async def update_book(
    slug: str,
    data: BookUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """更新图书标题、作者、简介、封面和排序值。"""

    result = await db.execute(select(Book).where(Book.slug == slug))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图书不存在")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(book, field, value)
    await db.commit()
    await db.refresh(book)
    return book


@router.post("/{slug}/extract-cover", response_model=BookDetail)
async def reextract_book_cover(
    slug: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """使用改进后的规则重新从 EPUB 提取封面。"""

    result = await db.execute(select(Book).where(Book.slug == slug))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图书不存在")
    cover_url = extract_cover_image(f"books/{slug}.epub", slug, force=True)
    if not cover_url:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="未能从 EPUB 识别封面")
    book.cover_url = cover_url
    await db.commit()
    await db.refresh(book)
    return book


@router.get("/{slug}/cover-candidates", response_model=list[BookCoverCandidate])
async def get_book_cover_candidates(
    slug: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """列出当前 EPUB 内可预览和选择的图片。"""

    result = await db.execute(select(Book).where(Book.slug == slug))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图书不存在")
    return list_cover_candidates(f"books/{slug}.epub")


@router.post("/{slug}/select-cover", response_model=BookDetail)
async def select_book_cover(
    slug: str,
    data: BookCoverSelection,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """选择当前 EPUB manifest 中的一张图片作为封面。"""

    result = await db.execute(select(Book).where(Book.slug == slug))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图书不存在")
    cover_url = select_cover_image(f"books/{slug}.epub", slug, data.item_name)
    if not cover_url:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="无法使用该候选图片")
    book.cover_url = cover_url
    await db.commit()
    await db.refresh(book)
    return book


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(
    slug: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """删除图书"""
    result = await db.execute(select(Book).where(Book.slug == slug))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="图书不存在")

    # 删除 EPUB 文件
    delete_book_files(slug)

    await db.delete(book)
    await db.commit()
