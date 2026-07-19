"""
博文路由 — CRUD + 统计
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.database import get_db
from app.models.post import Post
from app.models.user import User
from app.schemas.post import (
    PostCreate,
    PostDetail,
    PostListItem,
    PostListResponse,
    PostStat,
    PostUpdate,
)
from app.services.post import (
    delete_md_file,
    read_md_file,
    render_post_content,
    slug_to_filename,
    write_md_file,
)

router = APIRouter(prefix="/posts", tags=["博文"])


@router.get("", response_model=PostListResponse)
async def list_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=500),
    category: str = Query("", description="按分类筛选"),
    db: AsyncSession = Depends(get_db),
):
    """获取博文列表（分页 + 分类筛选），草稿不返回"""
    query = select(Post).where(Post.is_draft == False)  # noqa: E712
    count_query = select(func.count(Post.id)).where(Post.is_draft == False)  # noqa: E712

    if category:
        query = query.where(Post.category == category)
        count_query = count_query.where(Post.category == category)

    # 置顶优先，再按日期倒序
    query = query.order_by(Post.is_pinned.desc(), Post.date.desc())
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    result = await db.execute(query)
    items = list(result.scalars().all())

    return PostListResponse(items=items, total=total)


@router.get("/stats", response_model=list[PostStat])
async def post_stats(db: AsyncSession = Depends(get_db)):
    """按年统计文章数量"""
    result = await db.execute(
        select(Post.date).where(Post.is_draft == False)  # noqa: E712
    )
    dates = [r[0] for r in result.all() if r[0]]

    counts: dict[str, int] = {}
    for d in dates:
        year = d[:4]
        if year.isdigit():
            counts[year] = counts.get(year, 0) + 1

    return [PostStat(label=y, count=c) for y, c in sorted(counts.items())]


@router.get("/{slug}", response_model=PostDetail)
async def get_post(slug: str, db: AsyncSession = Depends(get_db)):
    """获取博文详情（含 Markdown 原文 + 渲染 HTML）"""
    result = await db.execute(select(Post).where(Post.slug == slug))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")

    # 读取 .md 文件原文
    content_md = read_md_file(post.md_filename) if post.md_filename else ""

    return PostDetail(
        id=post.id,
        slug=post.slug,
        title=post.title,
        description=post.description,
        date=post.date,
        cover_url=post.cover_url,
        category=post.category,
        tags=post.tags,
        is_draft=post.is_draft,
        is_pinned=post.is_pinned,
        content_md=content_md,
        content_html=post.content_html,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )


@router.post("", response_model=PostDetail, status_code=status.HTTP_201_CREATED)
async def create_post(
    body: PostCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """创建博文"""
    # 检查 slug 唯一性
    existing = await db.execute(select(Post).where(Post.slug == body.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="slug 已存在")

    md_filename = slug_to_filename(body.slug)

    # 写入 .md 文件
    if body.content_md:
        write_md_file(md_filename, body.content_md)

    # 渲染 HTML
    content_html = render_post_content(body.content_md) if body.content_md else ""

    post = Post(
        slug=body.slug,
        title=body.title,
        description=body.description,
        date=body.date,
        cover_url=body.cover_url,
        category=body.category,
        tags=body.tags,
        is_draft=body.is_draft,
        is_pinned=body.is_pinned,
        content_html=content_html,
        md_filename=md_filename,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)

    return PostDetail(
        id=post.id,
        slug=post.slug,
        title=post.title,
        description=post.description,
        date=post.date,
        cover_url=post.cover_url,
        category=post.category,
        tags=post.tags,
        is_draft=post.is_draft,
        is_pinned=post.is_pinned,
        content_md=body.content_md,
        content_html=content_html,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )


@router.put("/{slug}", response_model=PostDetail)
async def update_post(
    slug: str,
    body: PostUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """更新博文"""
    result = await db.execute(select(Post).where(Post.slug == slug))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")

    # 更新可选字段
    if body.title is not None:
        post.title = body.title
    if body.description is not None:
        post.description = body.description
    if body.date is not None:
        post.date = body.date
    if body.cover_url is not None:
        post.cover_url = body.cover_url
    if body.category is not None:
        post.category = body.category
    if body.tags is not None:
        post.tags = body.tags
    if body.is_draft is not None:
        post.is_draft = body.is_draft
    if body.is_pinned is not None:
        post.is_pinned = body.is_pinned

    # 更新 Markdown 正文
    content_md = ""
    if body.content_md is not None:
        md_filename = post.md_filename or slug_to_filename(slug)
        write_md_file(md_filename, body.content_md)
        post.content_html = render_post_content(body.content_md)
        post.md_filename = md_filename
        content_md = body.content_md
    else:
        content_md = read_md_file(post.md_filename) if post.md_filename else ""

    await db.commit()
    await db.refresh(post)

    return PostDetail(
        id=post.id,
        slug=post.slug,
        title=post.title,
        description=post.description,
        date=post.date,
        cover_url=post.cover_url,
        category=post.category,
        tags=post.tags,
        is_draft=post.is_draft,
        is_pinned=post.is_pinned,
        content_md=content_md,
        content_html=post.content_html,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    slug: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """删除博文（含 .md 文件）"""
    result = await db.execute(select(Post).where(Post.slug == slug))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")

    if post.md_filename:
        delete_md_file(post.md_filename)

    await db.delete(post)
    await db.commit()


@router.post("/{slug}/rerender", status_code=status.HTTP_200_OK)
async def rerender_post(
    slug: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """重新渲染博文 HTML（修改 .md 后手动触发）"""
    result = await db.execute(select(Post).where(Post.slug == slug))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")

    content_md = read_md_file(post.md_filename) if post.md_filename else ""
    post.content_html = render_post_content(content_md)
    await db.commit()

    return {"message": "重新渲染完成", "slug": slug}
