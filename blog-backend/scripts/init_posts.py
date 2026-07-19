"""
初始化脚本 — 扫描 content/posts/*.md，解析 frontmatter，写入数据库
运行方式: cd blog-backend && python -m scripts.init_posts
"""

import asyncio
import re
import sys
from pathlib import Path

# 把项目根目录加入 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.config import settings
from app.database import engine, AsyncSessionLocal
from app.models import Base
from app.models.post import Post
from app.services.markdown import render_markdown


def parse_frontmatter(raw: str) -> tuple[dict, str]:
    """解析 Markdown frontmatter，返回 (元数据字典, 正文)"""
    raw = raw.lstrip("\ufeff")  # 去除 BOM
    match = re.match(r"^---\r?\n([\s\S]*?)\r?\n---\r?\n?([\s\S]*)$", raw)
    if not match:
        return {}, raw

    data: dict = {}
    for line in match.group(1).split("\n"):
        sep = line.find(":")
        if sep == -1:
            continue
        key = line[:sep].strip()
        value = line[sep + 1:].strip()

        # 去除引号
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]

        # 解析特殊类型
        if value.lower() in ("true", "false"):
            data[key] = value.lower() == "true"
        elif key == "tags" and value.startswith("["):
            # 简单解析 [tag1, tag2] 格式
            tags_str = value.strip("[]")
            data[key] = [t.strip().strip("'\"") for t in tags_str.split(",") if t.strip()]
        else:
            data[key] = value

    return data, match.group(2)


def slugify(filename: str) -> str:
    """文件名 → slug"""
    return Path(filename).stem.lower().replace(" ", "-")


async def main():
    force = "--force" in sys.argv

    posts_dir = settings.CONTENT_DIR / "posts"
    if not posts_dir.exists():
        print(f"目录不存在: {posts_dir}")
        return

    md_files = sorted(posts_dir.glob("*.md"))
    if not md_files:
        print("没有找到 .md 文件")
        return

    print(f"找到 {len(md_files)} 个 .md 文件" + ("（强制覆盖模式）" if force else ""))

    # 确保表存在
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        created = 0
        updated = 0
        skipped = 0

        for md_file in md_files:
            raw = md_file.read_text(encoding="utf-8")
            frontmatter, content = parse_frontmatter(raw)
            slug = slugify(md_file.name)

            # 提取字段
            title = frontmatter.get("title", slug)
            description = frontmatter.get("description", "")
            date = frontmatter.get("published", "")
            category = frontmatter.get("category", "")
            tags = frontmatter.get("tags", [])
            is_draft = frontmatter.get("draft", False)
            is_pinned = frontmatter.get("pinned", False)
            cover_url = frontmatter.get("image", "")

            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",")]

            # 渲染 HTML
            content_html = render_markdown(content)

            # 检查是否已存在
            result = await session.execute(select(Post).where(Post.slug == slug))
            existing = result.scalar_one_or_none()

            if existing:
                if force:
                    # 覆盖更新
                    existing.title = title
                    existing.description = description
                    existing.date = date
                    existing.cover_url = cover_url
                    existing.category = category
                    existing.tags = tags
                    existing.is_draft = is_draft
                    existing.is_pinned = is_pinned
                    existing.content_html = content_html
                    existing.md_filename = md_file.name
                    updated += 1
                    print(f"  更新: {slug} ({title})")
                else:
                    print(f"  跳过（已存在）: {slug}")
                    skipped += 1
                continue

            post = Post(
                slug=slug,
                title=title,
                description=description,
                date=date,
                cover_url=cover_url,
                category=category,
                tags=tags,
                is_draft=is_draft,
                is_pinned=is_pinned,
                content_html=content_html,
                md_filename=md_file.name,
            )
            session.add(post)
            created += 1
            print(f"  创建: {slug} ({title})")

        await session.commit()
        print(f"\n完成: 创建 {created} 篇，更新 {updated} 篇，跳过 {skipped} 篇")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
