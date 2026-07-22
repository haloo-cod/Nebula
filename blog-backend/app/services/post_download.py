"""文章 Markdown ZIP 导出任务。"""

import json
import re
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import select

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.post import Post
from app.models.post_download import PostDownloadJob
from app.services.post import build_post_markdown, read_md_file

POST_ARCHIVE_DIR = settings.UPLOAD_DIR / "post-archives"


def _safe_name(value: str) -> str:
    return re.sub(r'[\\/:*?"<>|\x00-\x1f]+', "_", value).strip(" .") or "post"


def _image_path(url: str) -> Path | None:
    prefix = "/uploads/"
    if not url.startswith(prefix):
        return None
    path = (settings.UPLOAD_DIR / url.removeprefix(prefix)).resolve()
    return path if settings.UPLOAD_DIR.resolve() in path.parents and path.is_file() else None


def _markdown_image_urls(content: str) -> list[str]:
    """提取本地图床相对地址和同域绝对地址。"""
    return re.findall(
        r"!\[[^]]*\]\((?:(?:https?://[^/\s)]+)?)(/uploads/images/[^)\s]+)",
        content,
    )


def _rewrite_image_paths(content: str, names: dict[str, str]) -> str:
    """将已打包的图片引用改写为 ZIP 内相对路径。"""
    for source, target in names.items():
        content = content.replace(source, f"../images/{target}")
    return content


async def process_post_download_job(job_id: int) -> None:
    """在后台生成文章 ZIP，并可将 Markdown 引用的本地图床图片一并打包。"""
    async with AsyncSessionLocal() as db:
        job = await db.get(PostDownloadJob, job_id)
        if not job:
            return
        archive_path = POST_ARCHIVE_DIR / f"job-{job.id}.zip"
        try:
            slugs = json.loads(job.slugs_json)
            result = await db.execute(select(Post).where(Post.slug.in_(slugs)))
            posts = {post.slug: post for post in result.scalars().all()}
            if len(posts) != len(slugs):
                raise ValueError("部分文章不存在")
            POST_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
            used: set[str] = set()
            manifest = []
            with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as output:
                for index, slug in enumerate(slugs, start=1):
                    post = posts[slug]
                    content = read_md_file(post.md_filename) if post.md_filename else ""
                    image_names: dict[str, str] = {}
                    image_paths: dict[str, Path] = {}
                    if job.include_images:
                        for image_url in _markdown_image_urls(content):
                            image_path = _image_path(image_url)
                            if image_path:
                                image_names[image_url] = image_path.name
                                image_paths[image_url] = image_path
                    filename = _safe_name(post.slug) + ".md"
                    if filename in used:
                        filename = f"{_safe_name(post.slug)}-{post.id}.md"
                    used.add(filename)
                    output.writestr(
                        f"posts/{filename}",
                        build_post_markdown(post, _rewrite_image_paths(content, image_names)),
                    )
                    for image_url, image_path in image_paths.items():
                        output.write(image_path, f"images/{image_names[image_url]}")
                    manifest.append({"slug": post.slug, "title": post.title, "filename": filename})
                    job.completed_posts = index
                    await db.commit()
                output.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
            job.output_path = str(archive_path)
            job.file_size = archive_path.stat().st_size
            job.status = "completed"
            job.expires_at = datetime.now(timezone.utc) + timedelta(days=7)
            await db.commit()
        except Exception as exc:
            archive_path.unlink(missing_ok=True)
            job.status = "failed"
            job.error_message = str(exc)[:1000]
            await db.commit()


async def cleanup_expired_post_archives() -> None:
    """清理过期文章归档。"""
    if not POST_ARCHIVE_DIR.exists():
        return
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(PostDownloadJob))
        jobs = list(result.scalars().all())
        now = datetime.now(timezone.utc)
        for job in jobs:
            expires = job.expires_at
            if expires and (expires.replace(tzinfo=timezone.utc) if expires.tzinfo is None else expires) < now:
                Path(job.output_path).unlink(missing_ok=True) if job.output_path else None
                job.status = "expired"
        await db.commit()
