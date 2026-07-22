"""
博文路由 — CRUD + 统计
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_optional_current_user, require_admin
from app.database import get_db
from app.models.post import Post
from app.models.post_download import PostDownloadJob
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
    build_post_markdown,
    parse_post_markdown,
    safe_post_slug,
)
from app.schemas.post_download import PostDownloadJobCreate, PostDownloadJobResponse
from app.services.post_download import process_post_download_job
from app.services.slug import unique_slug

router = APIRouter(prefix="/posts", tags=["博文"])


def _archive_name(value: str) -> str:
    """清理文章归档文件名。"""
    cleaned = re.sub(r'[\\/:*?"<>|\x00-\x1f]+', "_", value.strip()).strip(" .")
    cleaned = re.sub(r"\.zip$", "", cleaned, flags=re.IGNORECASE).strip(" .")
    return (cleaned or "starlit-posts")[:150]


def _job_response(job: PostDownloadJob) -> PostDownloadJobResponse:
    """转换文章 ZIP 任务响应。"""
    expires_at = job.expires_at
    if expires_at and expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        status_value = "expired"
    else:
        status_value = job.status
    progress = round(job.completed_posts / job.total_posts * 100) if job.total_posts else 0
    return PostDownloadJobResponse(
        id=job.id, status=status_value, total_posts=job.total_posts,
        completed_posts=job.completed_posts, progress=progress,
        error_message=job.error_message,
        download_url=f"/api/v1/posts/download-jobs/{job.id}/file" if status_value == "completed" else None,
        created_at=job.created_at,
    )


@router.get("/{slug}/download", response_class=Response)
async def download_post_markdown(slug: str, db: AsyncSession = Depends(get_db), _: User = Depends(require_admin)):
    """下载单篇文章 Markdown（含可回导的 Front Matter）。"""
    result = await db.execute(select(Post).where(Post.slug == slug))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")
    content = read_md_file(post.md_filename) if post.md_filename else ""
    filename = f"{post.slug}.md"
    encoded_filename = quote(filename, safe="")
    content_disposition = f'attachment; filename="post.md"; filename*=UTF-8\'\'{encoded_filename}'
    return Response(
        content=build_post_markdown(post, content),
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": content_disposition},
    )


@router.post("/import", response_model=PostDetail, status_code=status.HTTP_201_CREATED)
async def import_post_markdown(file: UploadFile = File(...), db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)):
    """导入单篇 Markdown，默认作为草稿创建。"""
    filename = file.filename or "imported-post.md"
    if not filename.lower().endswith(".md"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="只支持 Markdown 文件")
    raw = await file.read()
    await file.close()
    if len(raw) > 5 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Markdown 文件不能超过 5MB")
    data = parse_post_markdown(raw.decode("utf-8-sig"), filename)
    data["slug"] = safe_post_slug(str(data["slug"]))
    existing = await db.execute(select(Post).where(Post.slug == data["slug"]))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="slug 已存在，请修改文件中的 slug")
    md_filename = f"{data['slug']}.md"
    body = str(data["content_md"])
    write_md_file(md_filename, body)
    post = Post(slug=data["slug"], title=data["title"], description=data["description"], date=data["date"],
                category=data["category"], tags=data["tags"], is_draft=True, is_pinned=data["is_pinned"],
                content_html=render_post_content(body), md_filename=md_filename)
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return await get_post(post.slug, db, admin)


async def _read_import_file(file: UploadFile) -> tuple[str, dict]:
    """读取并解析一个待导入 Markdown 文件。"""
    filename = file.filename or "imported-post.md"
    if not filename.lower().endswith(".md"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{filename} 不是 Markdown 文件")
    raw = await file.read()
    await file.close()
    if len(raw) > 5 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=f"{filename} 超过 5MB")
    return filename, parse_post_markdown(raw.decode("utf-8-sig"), filename)


@router.post("/import-preview")
async def preview_post_import(files: list[UploadFile] = File(...), _: User = Depends(require_admin)):
    """预览批量 Markdown 导入，不写入数据库。"""
    if len(files) > 100:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="一次最多导入 100 个文件")
    previews = []
    for file in files:
        filename, data = await _read_import_file(file)
        previews.append({"filename": filename, **{key: data[key] for key in ("slug", "title", "date", "is_draft")}})
    return previews


@router.post("/import-batch")
async def import_post_batch(
    files: list[UploadFile] = File(...),
    conflict: str = Form("skip"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """批量导入 Markdown，支持跳过、覆盖和自动改名。"""
    if conflict not in {"skip", "overwrite", "rename"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的冲突处理方式")
    if len(files) > 100:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="一次最多导入 100 个文件")
    results = []
    for file in files:
        filename, data = await _read_import_file(file)
        slug = safe_post_slug(str(data["slug"]))
        existing_result = await db.execute(select(Post).where(Post.slug == slug))
        existing = existing_result.scalar_one_or_none()
        if existing and conflict == "skip":
            results.append({"filename": filename, "slug": slug, "status": "skipped"})
            continue
        if existing and conflict == "rename":
            base = slug
            index = 2
            while True:
                candidate = f"{base}-{index}"
                check = await db.execute(select(Post.id).where(Post.slug == candidate))
                if check.scalar_one_or_none() is None:
                    slug = candidate
                    break
                index += 1
        body = str(data["content_md"])
        md_filename = f"{slug}.md"
        write_md_file(md_filename, body)
        if existing and conflict == "overwrite":
            existing.title = data["title"]
            existing.description = data["description"]
            existing.date = data["date"]
            existing.category = data["category"]
            existing.tags = data["tags"]
            existing.is_draft = True
            existing.is_pinned = data["is_pinned"]
            existing.content_html = render_post_content(body)
            existing.md_filename = md_filename
            result_status = "overwritten"
        else:
            db.add(Post(slug=slug, title=data["title"], description=data["description"], date=data["date"],
                        category=data["category"], tags=data["tags"], is_draft=True, is_pinned=data["is_pinned"],
                        content_html=render_post_content(body), md_filename=md_filename))
            result_status = "created"
        results.append({"filename": filename, "slug": slug, "status": result_status})
    await db.commit()
    return results


@router.post("/download-jobs", response_model=PostDownloadJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_post_download_job(data: PostDownloadJobCreate, background_tasks: BackgroundTasks,
                                    db: AsyncSession = Depends(get_db), user: User = Depends(require_admin)):
    """创建文章 ZIP 导出任务。"""
    slugs = list(dict.fromkeys(data.slugs))
    result = await db.execute(select(Post).where(Post.slug.in_(slugs)))
    if len(list(result.scalars().all())) != len(slugs):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="部分文章不存在")
    job = PostDownloadJob(user_id=user.id, slugs_json=json.dumps(slugs), total_posts=len(slugs),
                          archive_name=_archive_name(data.archive_name), include_images=data.include_images)
    db.add(job)
    await db.commit()
    await db.refresh(job)
    background_tasks.add_task(process_post_download_job, job.id)
    return _job_response(job)


@router.get("/download-jobs/{job_id}", response_model=PostDownloadJobResponse)
async def get_post_download_job(job_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(require_admin)):
    """查询文章 ZIP 任务。"""
    job = await db.get(PostDownloadJob, job_id)
    if not job or job.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="下载任务不存在")
    return _job_response(job)


@router.get("/download-jobs/{job_id}/file", response_class=FileResponse)
async def download_post_archive(job_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(require_admin)):
    """下载已完成的文章 ZIP。"""
    job = await db.get(PostDownloadJob, job_id)
    expires_at = job.expires_at if job else None
    if expires_at and expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="文章归档已过期，请重新打包")
    if not job or job.user_id != user.id or job.status != "completed":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章归档不存在")
    path = Path(job.output_path)
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章归档文件不存在")
    return FileResponse(path, filename=f"{_archive_name(job.archive_name)}.zip", media_type="application/zip")


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
async def get_post(
    slug: str,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_optional_current_user),
):
    """获取博文详情（含 Markdown 原文 + 渲染 HTML）"""
    result = await db.execute(select(Post).where(Post.slug == slug))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")
    if post.is_draft and (user is None or not user.is_admin):
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
    slug = await unique_slug(db, Post, body.slug or body.title, "post")

    md_filename = slug_to_filename(slug)

    # 写入 .md 文件
    if body.content_md:
        write_md_file(md_filename, body.content_md)

    # 渲染 HTML
    content_html = render_post_content(body.content_md) if body.content_md else ""

    post = Post(
        slug=slug,
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
