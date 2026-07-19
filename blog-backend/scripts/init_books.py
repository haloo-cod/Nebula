"""
初始化脚本 — 扫描 uploads/books/*.epub，提取元数据，写入数据库
运行方式: cd blog-backend && python -m scripts.init_books
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.config import settings
from app.database import engine, AsyncSessionLocal
from app.models import Base
from app.models.book import Book
from app.services.book import (
    extract_cover_image,
    get_epub_files,
    read_epub_metadata,
    slugify,
    title_from_filename,
)


async def main():
    force = "--force" in sys.argv

    epub_files = get_epub_files()
    if not epub_files:
        print("没有找到 EPUB 文件")
        return

    print(f"找到 {len(epub_files)} 个 EPUB 文件" + ("（强制覆盖模式）" if force else ""))

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        created = 0
        updated = 0
        skipped = 0

        for epub_file in epub_files:
            slug = slugify(epub_file.name)
            # 内部路径（相对于 UPLOAD_DIR，用于文件系统操作）
            internal_path = f"books/{epub_file.name}"
            # URL 路径（存入 DB，前端 resolveUrl 补全后可访问）
            url_path = f"/uploads/books/{epub_file.name}"

            # 提取元数据
            meta = read_epub_metadata(internal_path)
            title = meta.get("title") or title_from_filename(epub_file.name)
            author = meta.get("author", "")
            description = meta.get("description", "")

            # 提取封面
            cover_url = extract_cover_image(internal_path, slug)

            # 检查是否已存在
            result = await session.execute(select(Book).where(Book.slug == slug))
            existing = result.scalar_one_or_none()

            if existing:
                if force:
                    existing.title = title
                    existing.author = author
                    existing.description = description
                    existing.cover_url = cover_url or existing.cover_url
                    existing.file_path = url_path
                    updated += 1
                    print(f"  更新: {slug} ({title})")
                else:
                    print(f"  跳过（已存在）: {slug}")
                    skipped += 1
                continue

            book = Book(
                slug=slug,
                title=title,
                author=author,
                description=description,
                cover_url=cover_url,
                file_path=url_path,
            )
            session.add(book)
            created += 1
            print(f"  创建: {slug} ({title[:40]}...)")

        await session.commit()
        print(f"\n完成: 创建 {created} 本，更新 {updated} 本，跳过 {skipped} 本")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
