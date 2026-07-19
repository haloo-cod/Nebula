"""
图书路由 — Books CRUD
"""

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.database import get_db
from app.models.book import Book
from app.models.user import User
from app.schemas.book import BookDetail, BookCreate, BookListItem, BookListResponse
from app.services.book import (
    BOOKS_DIR,
    extract_cover_image,
    get_epub_files,
    read_epub_metadata,
    slugify,
)

router = APIRouter(prefix="/books", tags=["图书"])


@router.get("", response_model=BookListResponse)
async def list_books(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str | None = Query(None, description="搜索关键词（标题/作者模糊匹配）"),
    db: AsyncSession = Depends(get_db),
):
    """获取图书列表（分页 + 搜索）"""
    stmt = select(Book)

    if keyword:
        pattern = f"%{keyword}%"
        stmt = stmt.where(
            or_(
                Book.title.ilike(pattern),
                Book.author.ilike(pattern),
            )
        )

    stmt = stmt.order_by(Book.created_at.desc())

    # 总数
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # 分页
    paged_stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(paged_stmt)
    items = list(result.scalars().all())

    return BookListResponse(items=items, total=total)


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

    # 保存文件
    BOOKS_DIR.mkdir(parents=True, exist_ok=True)
    content = await file.read()
    internal_path = f"books/{filename}"
    (BOOKS_DIR / filename).write_bytes(content)

    # 提取元数据
    meta = read_epub_metadata(internal_path)
    book_title = title or meta.get("title") or slug
    book_author = author or meta.get("author") or ""

    # 提取封面
    cover_url = extract_cover_image(internal_path, slug)

    # 检查 slug 唯一性
    existing = await db.execute(select(Book).where(Book.slug == slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="slug 已存在")

    book = Book(
        slug=slug,
        title=book_title,
        author=book_author,
        description=description or meta.get("description", ""),
        cover_url=cover_url,
        file_path=f"/uploads/books/{filename}",
    )
    db.add(book)
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
    epub_path = BOOKS_DIR / f"{slug}.epub"
    if epub_path.exists():
        epub_path.unlink()

    await db.delete(book)
    await db.commit()
