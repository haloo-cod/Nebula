"""
初始化脚本 — 将 content/gallery/*.md 元数据写入数据库
运行方式: cd blog-backend && python -m scripts.init_gallery
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.config import settings
from app.database import engine, AsyncSessionLocal
from app.models import Base
from app.models.gallery import GalleryProject
from app.services.markdown import render_markdown

# 元数据（gallery .md 没有 frontmatter，需手动定义）
GALLERY_META = [
    {
        "slug": "my-blog",
        "title": "My Blog",
        "description": "围绕内容、液态玻璃视觉和个人表达构建的 Vue 博客前端。",
        "tags": ["Vue", "Vite", "TypeScript", "Markdown", "Liquid Glass"],
        "status": "重构中",
        "year": "2026",
    },
    {
        "slug": "deep-sea-gallery",
        "title": "深海玻璃标本柜",
        "description": "一个用于展示项目与技能的深海感作品展厅。",
        "tags": ["Vue Router", "LiquidGlass", "Design System", "Responsive"],
        "status": "构建中",
        "year": "2026",
    },
    {
        "slug": "project-docs",
        "title": "项目文档系统",
        "description": "独立于博客文章的项目 Markdown 详情链路,为后端接入预留边界。",
        "tags": ["Markdown", "marked", "Data Layer", "API Ready"],
        "status": "规划中",
        "year": "2026",
    },
    {
        "slug": "backend-roadmap",
        "title": "后端接入路线",
        "description": "为项目、资源下载和动态内容准备 FastAPI 接口边界。",
        "tags": ["FastAPI", "API", "Resource", "Deployment"],
        "status": "待接入",
        "year": "2026",
    },
]


async def main():
    gallery_dir = settings.CONTENT_DIR / "gallery"

    # 确保表存在
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        created = 0
        skipped = 0

        for meta in GALLERY_META:
            slug = meta["slug"]

            # 检查是否已存在
            result = await session.execute(
                select(GalleryProject).where(GalleryProject.slug == slug)
            )
            if result.scalar_one_or_none():
                print(f"  跳过（已存在）: {slug}")
                skipped += 1
                continue

            # 读取 .md 文件
            md_filename = f"{slug}.md"
            md_path = gallery_dir / md_filename
            content = md_path.read_text(encoding="utf-8") if md_path.exists() else ""

            # 渲染 HTML
            content_html = render_markdown(content) if content else ""

            project = GalleryProject(
                slug=slug,
                title=meta["title"],
                description=meta["description"],
                tags=meta["tags"],
                status=meta["status"],
                year=meta["year"],
                is_featured=False,
                content_html=content_html,
                md_filename=md_filename,
            )
            session.add(project)
            created += 1
            print(f"  创建: {slug} ({meta['title']})")

        await session.commit()
        print(f"\n完成: 创建 {created} 个项目，跳过 {skipped} 个")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
