"""
图书 service — EPUB 文件操作 + 元数据提取
"""

from io import BytesIO
from pathlib import Path, PurePosixPath
import base64
import hashlib
import posixpath
import uuid
import re
import unicodedata
import xml.etree.ElementTree as ET

from fastapi import UploadFile

from ebooklib import epub, ITEM_COVER, ITEM_IMAGE
from PIL import Image

from app.config import settings

BOOKS_DIR = settings.UPLOAD_DIR / "books"
BOOK_COVERS_DIR = settings.UPLOAD_DIR / "images" / "book-covers"
UPLOAD_CHUNK_SIZE = 1024 * 1024


async def save_epub_upload(file: UploadFile, filename: str) -> Path:
    """将 EPUB 分块写入临时文件，完成后原子移动到正式路径。"""

    BOOKS_DIR.mkdir(parents=True, exist_ok=True)
    final_path = BOOKS_DIR / filename
    temp_path = BOOKS_DIR / f".{filename}.{uuid.uuid4().hex}.uploading"

    try:
        with temp_path.open("wb") as target:
            while chunk := await file.read(UPLOAD_CHUNK_SIZE):
                target.write(chunk)
        temp_path.replace(final_path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise
    finally:
        await file.close()

    return final_path


def delete_book_files(slug: str) -> None:
    """删除指定 slug 的 EPUB 及其提取封面。"""

    (BOOKS_DIR / f"{slug}.epub").unlink(missing_ok=True)
    if BOOK_COVERS_DIR.exists():
        for cover_path in BOOK_COVERS_DIR.glob(f"{slug}_cover.*"):
            cover_path.unlink(missing_ok=True)
        for cover_path in BOOK_COVERS_DIR.glob(f"{slug}_cover_*.*"):
            cover_path.unlink(missing_ok=True)


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


def extract_cover_image(file_path: str, slug: str, force: bool = False) -> str:
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

        return _save_cover_item(cover_item, slug, force)
    except Exception:
        pass

    return ""


def list_cover_candidates(file_path: str) -> list[dict[str, object]]:
    """列出 EPUB manifest 中可作为封面的位图资源。"""

    full_path = settings.UPLOAD_DIR / file_path
    if not full_path.exists():
        return []
    book = epub.read_epub(str(full_path))
    recommended = _find_cover_image(book)
    recommended_name = recommended.get_name() if recommended else ""
    candidates: list[dict[str, object]] = []
    for item in _get_image_items(book):
        media_type = item.media_type or ""
        if media_type not in {"image/jpeg", "image/png", "image/webp", "image/gif"}:
            continue
        content = item.get_content()
        if not content or len(content) < 100:
            continue
        try:
            with Image.open(BytesIO(content)) as image:
                width, height = image.size
                preview = image.convert("RGB")
                preview.thumbnail((180, 240))
                preview_buffer = BytesIO()
                preview.save(preview_buffer, format="JPEG", quality=80, optimize=True)
        except Exception:
            continue
        name = item.get_name() or item.id
        score = _score_cover_candidate(item)
        candidates.append({
            "item_name": name,
            "filename": PurePosixPath(name).name,
            "media_type": media_type,
            "width": width,
            "height": height,
            "size": len(content),
            "score": score or 0,
            "recommended": name == recommended_name,
            "preview_data_url": f"data:image/jpeg;base64,{base64.b64encode(preview_buffer.getvalue()).decode()}",
        })
    candidates.sort(
        key=lambda candidate: (
            bool(candidate["recommended"]),
            float(candidate["score"]),
        ),
        reverse=True,
    )
    return candidates


def get_cover_candidate(file_path: str, item_name: str):
    """按 manifest 名称读取当前 EPUB 中的封面候选，找不到时返回 None。"""

    full_path = settings.UPLOAD_DIR / file_path
    if not full_path.exists():
        return None
    book = epub.read_epub(str(full_path))
    for item in _get_image_items(book):
        if item.get_name() == item_name:
            return item
    return None


def _get_image_items(book) -> list:
    """返回去重后的普通图片和显式封面资源。"""

    items = list(book.get_items_of_type(ITEM_IMAGE))
    known_names = {item.get_name() for item in items}
    items.extend(
        item
        for item in book.get_items_of_type(ITEM_COVER)
        if item.get_name() not in known_names
    )
    return items


def select_cover_image(file_path: str, slug: str, item_name: str) -> str:
    """将当前 EPUB 中指定的 manifest 图片提取为图书封面。"""

    item = get_cover_candidate(file_path, item_name)
    if not item:
        return ""
    return _save_cover_item(item, slug, force=True)


def _save_cover_item(item, slug: str, force: bool = False) -> str:
    """保存封面资源，并以内容摘要区分不同选择以规避浏览器缓存。"""

    content = item.get_content()
    if not content or len(content) < 100:
        return ""
    media_type = item.media_type or "image/jpeg"
    ext = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/gif": ".gif",
    }.get(media_type)
    if not ext:
        return ""
    safe_slug = slug.replace("/", "_").replace("\\", "_")
    digest = hashlib.sha256(content).hexdigest()[:12]
    filename = f"{safe_slug}_cover_{digest}{ext}"
    BOOK_COVERS_DIR.mkdir(parents=True, exist_ok=True)
    cover_path = BOOK_COVERS_DIR / filename
    if force or not cover_path.exists():
        cover_path.write_bytes(content)
    for old_cover in BOOK_COVERS_DIR.glob(f"{safe_slug}_cover.*"):
        old_cover.unlink(missing_ok=True)
    for old_cover in BOOK_COVERS_DIR.glob(f"{safe_slug}_cover_*.*"):
        if old_cover != cover_path:
            old_cover.unlink(missing_ok=True)
    return f"/uploads/images/book-covers/{filename}"


def _find_cover_image(book):
    """在 EPUB 中查找封面图片（按优先级尝试多种方式）"""

    # 方法 1：ebooklib 已明确识别为 ITEM_COVER 的资源
    cover_items = list(book.get_items_of_type(ITEM_COVER))
    if cover_items and cover_items[0].get_content():
        return cover_items[0]

    # 方法 2：通过 OPF metadata 中声明的 cover id
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

    # 方法 3：解析阅读顺序中的 cover.xhtml，找到它实际引用的图片
    cover_page_item = _find_cover_page_image(book)
    if cover_page_item:
        return cover_page_item

    # 方法 4：文件名含 cover 且不是 backcover 的图片
    try:
        for item in book.get_items_of_type(ITEM_IMAGE):
            name = (item.get_name() or "").lower()
            if "cover" in name and "backcover" not in name:
                if item.get_content():
                    return item
    except Exception:
        pass

    # 方法 5：id 含 cover 且不是 backcover 的图片
    try:
        for item in book.get_items_of_type(ITEM_IMAGE):
            item_id = (item.id or "").lower()
            if "cover" in item_id and "backcover" not in item_id:
                if item.get_content():
                    return item
    except Exception:
        pass

    # 方法 6：按名称、尺寸和纵横比评分，避免误选 note/logo/icon/横幅
    candidates = []
    for item in book.get_items_of_type(ITEM_IMAGE):
        score = _score_cover_candidate(item)
        if score is not None:
            candidates.append((score, item))
    if candidates:
        candidates.sort(key=lambda candidate: candidate[0], reverse=True)
        return candidates[0][1]

    return None


def _find_cover_page_image(book):
    """解析 cover XHTML 中 img/svg image 的引用并返回对应 manifest 图片。"""

    image_items = [
        item for item in book.get_items()
        if item.get_type() in {ITEM_IMAGE, ITEM_COVER}
    ]
    image_by_name = {
        posixpath.normpath((item.get_name() or "").lstrip("/")): item
        for item in image_items
    }
    document_items = {item.id: item for item in book.get_items() if hasattr(item, "get_content")}

    cover_documents = []
    for spine_id, _ in getattr(book, "spine", []):
        item = document_items.get(spine_id)
        name = (item.get_name() if item else "") or ""
        marker = f"{spine_id} {name}".lower()
        if "cover" in marker and "backcover" not in marker:
            cover_documents.append(item)
    if not cover_documents:
        cover_documents = [
            item for item in document_items.values()
            if "cover" in f"{item.id} {item.get_name()}".lower()
            and "backcover" not in f"{item.id} {item.get_name()}".lower()
        ]

    for document in cover_documents:
        try:
            root = ET.fromstring(document.get_content())
        except Exception:
            continue
        document_dir = str(PurePosixPath(document.get_name()).parent)
        for element in root.iter():
            tag = element.tag.rsplit("}", 1)[-1].lower()
            if tag not in {"img", "image"}:
                continue
            source = element.attrib.get("src") or element.attrib.get("href")
            if not source:
                source = next((value for key, value in element.attrib.items() if key.endswith("}href")), None)
            if not source:
                continue
            resolved = posixpath.normpath(posixpath.join(document_dir, source.split("#", 1)[0])).lstrip("/")
            item = image_by_name.get(resolved)
            if item and item.get_content():
                return item
    return None


def _score_cover_candidate(item) -> float | None:
    """为无声明的封面候选评分；返回 None 表示明确排除。"""

    name = f"{item.id} {item.get_name()}".lower()
    if any(marker in name for marker in ("note", "logo", "icon", "avatar", "backcover", "back_cover")):
        return None
    content = item.get_content()
    if not content or len(content) < 1024:
        return None
    try:
        with Image.open(BytesIO(content)) as image:
            width, height = image.size
    except Exception:
        return None
    if width < 300 or height < 300:
        return None

    ratio = width / height
    score = min(width * height / 100_000, 40)
    if 0.55 <= ratio <= 0.82:
        score += 60
    elif ratio < 1:
        score += 25
    else:
        score -= 20
    if any(marker in name for marker in ("cover", "/001.", "x001", "p1.")):
        score += 35
    return score


def get_epub_files() -> list[Path]:
    """获取 uploads/books/ 下所有 EPUB 文件"""
    BOOKS_DIR.mkdir(parents=True, exist_ok=True)
    return sorted(b for b in BOOKS_DIR.glob("*.epub") if b.is_file())


def slugify(filename: str) -> str:
    """文件名 → slug"""
    value = Path(filename).stem
    value = unicodedata.normalize("NFKC", value).strip().lower()
    value = re.sub(r"[^\w\u4e00-\u9fff]+", "-", value, flags=re.UNICODE)
    return re.sub(r"[-_]+", "-", value).strip("-") or "book"


def title_from_filename(filename: str) -> str:
    """从文件名生成默认书名"""
    return slugify(filename)
