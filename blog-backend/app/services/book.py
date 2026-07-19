"""
图书 service — EPUB 文件操作 + 元数据提取
"""

from pathlib import Path

from ebooklib import epub, ITEM_IMAGE

from app.config import settings

BOOKS_DIR = settings.UPLOAD_DIR / "books"
BOOK_COVERS_DIR = settings.UPLOAD_DIR / "images" / "book-covers"


def read_epub_metadata(file_path: str) -> dict[str, str]:
    """
    用 ebooklib 从 EPUB 提取 title / author / description
    file_path 是相对于 UPLOAD_DIR 的路径，如 'books/xxx.epub'
    """
    full_path = settings.UPLOAD_DIR / file_path
    meta: dict[str, str] = {"title": "", "author": "", "description": ""}

    if not full_path.exists():
        return meta

    try:
        book = epub.read_epub(str(full_path))
        titles = book.get_metadata("DC", "title")
        if titles:
            meta["title"] = str(titles[0][0])

        creators = book.get_metadata("DC", "creator")
        if creators:
            meta["author"] = str(creators[0][0])

        descriptions = book.get_metadata("DC", "description")
        if descriptions:
            meta["description"] = str(descriptions[0][0])
    except Exception:
        pass

    return meta


def extract_cover_image(file_path: str, slug: str) -> str:
    """
    从 EPUB 提取封面图，保存到 book-covers 目录，返回 URL 路径。
    file_path 是相对于 UPLOAD_DIR 的路径，如 'books/xxx.epub'
    使用固定命名 {slug}_cover.{ext}，避免重复生成。
    """
    full_path = settings.UPLOAD_DIR / file_path
    if not full_path.exists():
        return ""

    try:
        book = epub.read_epub(str(full_path))
        cover_item = _find_cover_image(book)
        if not cover_item:
            return ""

        content = cover_item.get_content()
        if not content or len(content) < 100:
            # 太小的内容不太可能是有效图片
            return ""

        # 确定扩展名
        media_type = cover_item.media_type or "image/jpeg"
        ext = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
            "image/gif": ".gif",
        }.get(media_type, ".jpg")

        # 固定命名（slug 安全化：替换特殊字符）
        safe_slug = slug.replace("/", "_").replace("\\", "_")
        filename = f"{safe_slug}_cover{ext}"

        # 保存
        BOOK_COVERS_DIR.mkdir(parents=True, exist_ok=True)
        cover_path = BOOK_COVERS_DIR / filename

        # 已存在则跳过（除非内容不同）
        if not cover_path.exists():
            cover_path.write_bytes(content)

        return f"/uploads/images/book-covers/{filename}"
    except Exception:
        pass

    return ""


def _find_cover_image(book):
    """在 EPUB 中查找封面图片（按优先级尝试多种方式）"""

    # 方法 1：通过 OPF metadata 中声明的 cover id
    try:
        cover_metas = book.get_metadata("OPF", "cover")
        if cover_metas:
            for meta_item in cover_metas:
                if meta_item[1] and "content" in meta_item[1]:
                    cover_id = meta_item[1]["content"]
                    item = book.get_item_with_id(cover_id)
                    if item and item.get_content():
                        return item
    except Exception:
        pass

    # 方法 2：文件名含 "cover" 的图片
    try:
        for item in book.get_items_of_type(ITEM_IMAGE):
            name = (item.get_name() or "").lower()
            if "cover" in name:
                if item.get_content():
                    return item
    except Exception:
        pass

    # 方法 3：id 含 "cover" 的图片
    try:
        for item in book.get_items_of_type(ITEM_IMAGE):
            item_id = (item.id or "").lower()
            if "cover" in item_id:
                if item.get_content():
                    return item
    except Exception:
        pass

    # 方法 4：取第一张有内容的图片（兜底）
    try:
        for item in book.get_items_of_type(ITEM_IMAGE):
            content = item.get_content()
            if content and len(content) > 100:
                return item
    except Exception:
        pass

    return None


def get_epub_files() -> list[Path]:
    """获取 uploads/books/ 下所有 EPUB 文件"""
    BOOKS_DIR.mkdir(parents=True, exist_ok=True)
    return sorted(b for b in BOOKS_DIR.glob("*.epub") if b.is_file())


def slugify(filename: str) -> str:
    """文件名 → slug"""
    return Path(filename).stem


def title_from_filename(filename: str) -> str:
    """从文件名生成默认书名"""
    return slugify(filename)
