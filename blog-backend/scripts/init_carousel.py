"""
初始化脚本 — 将前端首页轮播图片复制到后端 uploads 并入库
运行方式: cd blog-backend && python -m scripts.init_carousel [--force]
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
from app.models.carousel import CarouselSlide
from app.models.image import UploadedImage


# 前端 img2 目录下的 7 张图片（首页轮播用）
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "blog-frontend" / "src" / "assets" / "img2"

# (源文件名, 目标文件名, sort_order)
CAROUSEL_IMAGES = [
    ("01.PNG", "carousel-01.png", 0),
    ("02.PNG", "carousel-02.png", 1),
    ("03.PNG", "carousel-03.png", 2),
    ("04.PNG", "carousel-04.png", 3),
    ("05.PNG", "carousel-05.png", 4),
    ("06.JPG", "carousel-06.jpg", 5),
    ("07.PNG", "carousel-07.png", 6),
]


def copy_and_get_info(src_name: str, dest_name: str) -> dict:
    """复制图片到 uploads/images/carousel/ 并返回元信息"""
    src_path = FRONTEND_DIR / src_name
    if not src_path.exists():
        raise FileNotFoundError(f"源文件不存在: {src_path}")

    dest_dir = settings.UPLOAD_DIR / "images" / "carousel"
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

    relative_path = f"images/carousel/{dest_name}"
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


async def main():
    force = "--force" in sys.argv

    print(f"准备初始化 {len(CAROUSEL_IMAGES)} 张轮播图" + ("（强制覆盖模式）" if force else ""))

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        created = 0
        skipped = 0

        for src_name, dest_name, sort_order in CAROUSEL_IMAGES:
            relative_path = f"images/carousel/{dest_name}"

            # 检查是否已存在
            existing = await session.execute(
                select(UploadedImage).where(UploadedImage.filename == relative_path)
            )
            existing_img = existing.scalar_one_or_none()

            if existing_img and not force:
                print(f"  跳过（已存在）: {dest_name}")
                skipped += 1
                continue

            # 复制文件
            try:
                info = copy_and_get_info(src_name, dest_name)
            except FileNotFoundError as e:
                print(f"  错误: {e}")
                continue

            # 插入或更新 uploaded_images
            if existing_img and force:
                existing_img.file_size = info["file_size"]
                existing_img.width = info["width"]
                existing_img.height = info["height"]
                existing_img.mime_type = info["mime_type"]
                image_id = existing_img.id
                print(f"  更新图片: {dest_name} ({info['width']}x{info['height']})")
            else:
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
                image_id = img_record.id
                print(f"  新增图片: {dest_name} ({info['width']}x{info['height']})")

            # 插入或更新 carousel_slides
            cs_existing = await session.execute(
                select(CarouselSlide).where(CarouselSlide.image_id == image_id)
            )
            cs_record = cs_existing.scalar_one_or_none()

            if cs_record:
                cs_record.sort_order = sort_order
            else:
                cs_record = CarouselSlide(image_id=image_id, sort_order=sort_order)
                session.add(cs_record)
                created += 1

        await session.commit()

    print(f"\n完成! 新增 {created} 条轮播记录，跳过 {skipped} 条")


if __name__ == "__main__":
    asyncio.run(main())
