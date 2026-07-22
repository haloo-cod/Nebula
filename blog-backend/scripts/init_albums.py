"""
初始化脚本 — 将前端现有 3 个相册数据迁移到后端数据库
运行方式: cd blog-backend && python -m scripts.init_albums [--force]

注意: 此脚本复用 init_carousel 已入库的 carousel 图片（它们来自同一目录 img2/）。
如果 init_carousel 尚未运行，此脚本会自动复制图片。
"""

import asyncio
import mimetypes
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image
from sqlalchemy import select

from app.config import settings
from app.database import engine, AsyncSessionLocal
from app.models import Base
from app.models.album import Album, AlbumPhoto
from app.models.image import UploadedImage


FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "blog-frontend" / "src" / "assets" / "img2"

# 相册定义：(title, description, orientation, [(文件名, caption)])
ALBUMS_DATA = [
    {
        "title": "光影碎片",
        "description": "随手收集的光与影,一些不成系列的瞬间",
        "orientation": "portrait",
        "photos": [
            ("01.PNG", "第一束光"),
            ("02.PNG", "午后窗边"),
            ("03.PNG", "街角一瞥"),
        ],
    },
    {
        "title": "旅途拾遗",
        "description": "路上捡到的风景",
        "orientation": "portrait",
        "photos": [
            ("04.PNG", "出发"),
            ("05.PNG", "远山"),
        ],
    },
    {
        "title": "日常切片",
        "description": "平凡日子的横截面",
        "orientation": "portrait",
        "photos": [
            ("06.JPG", "清晨"),
            ("07.PNG", "夜幕"),
        ],
    },
]

# 文件名 → 目标名映射（复用 carousel 的命名或单独命名到 albums 子目录）
def get_dest_name(src_name: str) -> str:
    """生成目标文件名：albums/album-{原名小写}"""
    stem = Path(src_name).stem.lower()
    ext = Path(src_name).suffix.lower()
    return f"album-{stem}{ext}"


def ensure_image_file(src_name: str, dest_name: str) -> dict:
    """确保图片文件存在于 uploads/images/albums/ 并返回元信息"""
    src_path = FRONTEND_DIR / src_name
    if not src_path.exists():
        raise FileNotFoundError(f"源文件不存在: {src_path}")

    dest_dir = settings.UPLOAD_DIR / "images" / "albums"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / dest_name

    shutil.copy2(src_path, dest_path)

    file_size = dest_path.stat().st_size
    width, height = 0, 0
    try:
        with Image.open(dest_path) as img:
            width, height = img.size
    except Exception:
        pass

    mime_type, _ = mimetypes.guess_type(dest_name)
    if not mime_type:
        mime_type = "image/png"

    relative_path = f"images/albums/{dest_name}"
    url = f"/uploads/{relative_path}"

    return {
        "filename": relative_path,
        "original_name": dest_name,
        "url": url,
        "file_size": file_size,
        "width": width,
        "height": height,
        "mime_type": mime_type,
    }


async def get_or_create_image(session, src_name: str) -> int:
    """获取或创建图片记录，返回 image_id"""
    dest_name = get_dest_name(src_name)
    relative_path = f"images/albums/{dest_name}"

    # 检查是否已存在
    existing = await session.execute(
        select(UploadedImage).where(UploadedImage.filename == relative_path)
    )
    existing_img = existing.scalar_one_or_none()
    if existing_img:
        return existing_img.id

    # 复制文件并创建记录
    info = ensure_image_file(src_name, dest_name)
    img_record = UploadedImage(
        filename=info["filename"],
        original_name=info["original_name"],
        url=info["url"],
        file_size=info["file_size"],
        width=info["width"],
        height=info["height"],
        mime_type=info["mime_type"],
    )
    session.add(img_record)
    await session.flush()
    print(f"    新增图片: {dest_name} ({info['width']}x{info['height']})")
    return img_record.id


async def main():
    force = "--force" in sys.argv

    print(f"准备初始化 {len(ALBUMS_DATA)} 个相册" + ("（强制覆盖模式）" if force else ""))

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        created_albums = 0
        skipped_albums = 0

        for album_data in ALBUMS_DATA:
            title = album_data["title"]

            # 检查相册是否已存在（按标题判断）
            existing = await session.execute(
                select(Album).where(Album.title == title)
            )
            existing_album = existing.scalar_one_or_none()

            if existing_album and not force:
                print(f"  跳过相册（已存在）: {title}")
                skipped_albums += 1
                continue

            if existing_album and force:
                # 强制模式：删除旧相册重建
                await session.delete(existing_album)
                await session.flush()

            # 创建相册
            album = Album(
                title=title,
                description=album_data["description"],
                orientation=album_data["orientation"],
            )
            session.add(album)
            await session.flush()
            print(f"  创建相册: {title} (id={album.id})")

            # 添加照片
            for order, (src_name, caption) in enumerate(album_data["photos"]):
                try:
                    image_id = await get_or_create_image(session, src_name)
                except FileNotFoundError as e:
                    print(f"    错误: {e}")
                    continue

                photo = AlbumPhoto(
                    album_id=album.id,
                    image_id=image_id,
                    caption=caption,
                    sort_order=order,
                )
                session.add(photo)

            created_albums += 1

        await session.commit()

    print(f"\n完成! 新增 {created_albums} 个相册，跳过 {skipped_albums} 个")


if __name__ == "__main__":
    asyncio.run(main())
