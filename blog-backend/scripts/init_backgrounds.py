"""
初始化脚本 — 将前端静态背景图复制到后端 uploads 并入库
运行方式: cd blog-backend && python -m scripts.init_backgrounds [--force]
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
from app.models.background import Background
from app.models.image import UploadedImage


# 前端图片 → 后端文件映射
# (源文件相对于前端 assets, 新文件名, theme, device, sort_order)
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "blog-frontend" / "src" / "assets"

BACKGROUND_MAPPING = [
    # 桌面端 dark 主题
    ("img/test2.jpg", "dark-desktop-01.jpg", "dark", "desktop", 0),
    ("img/test3.jpg", "dark-desktop-02.jpg", "dark", "desktop", 1),
    ("img/test4.jpg", "dark-desktop-03.jpg", "dark", "desktop", 2),
    # 桌面端 light 主题
    ("img/test6.PNG", "light-desktop-01.png", "light", "desktop", 0),
    ("img/test5.PNG", "light-desktop-02.png", "light", "desktop", 1),
    # 移动端 dark 主题
    ("img2/01.PNG", "dark-mobile-01.png", "dark", "mobile", 0),
    ("img2/03.PNG", "dark-mobile-02.png", "dark", "mobile", 1),
    # 移动端 light 主题
    ("img2/05.PNG", "light-mobile-01.png", "light", "mobile", 0),
    ("img2/07.PNG", "light-mobile-02.png", "light", "mobile", 1),
]


def copy_and_get_info(src_relative: str, dest_name: str) -> dict:
    """
    复制图片到 uploads/images/backgrounds/ 并返回元信息
    """
    src_path = FRONTEND_DIR / src_relative
    if not src_path.exists():
        raise FileNotFoundError(f"源文件不存在: {src_path}")

    dest_dir = settings.UPLOAD_DIR / "images" / "backgrounds"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / dest_name

    shutil.copy2(src_path, dest_path)

    # 获取图片信息
    file_size = dest_path.stat().st_size
    width, height = 0, 0
    try:
        with Image.open(dest_path) as img:
            width, height = img.size
    except Exception:
        pass

    mime_type, _ = mimetypes.guess_type(dest_name)
    if not mime_type:
        mime_type = "image/jpeg"

    # 相对路径（相对于 UPLOAD_DIR）
    relative_path = f"images/backgrounds/{dest_name}"
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

    print(f"准备初始化 {len(BACKGROUND_MAPPING)} 张背景图" + ("（强制覆盖模式）" if force else ""))

    # 确保表存在
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        created = 0
        skipped = 0

        for src_rel, dest_name, theme, device, sort_order in BACKGROUND_MAPPING:
            # 检查是否已存在（通过文件名判断）
            relative_path = f"images/backgrounds/{dest_name}"
            existing = await session.execute(
                select(UploadedImage).where(UploadedImage.filename == relative_path)
            )
            existing_img = existing.scalar_one_or_none()

            if existing_img and not force:
                print(f"  跳过（已存在）: {dest_name}")
                skipped += 1
                continue

            # 复制文件并获取信息
            try:
                info = copy_and_get_info(src_rel, dest_name)
            except FileNotFoundError as e:
                print(f"  错误: {e}")
                continue

            # 插入或更新 uploaded_images 记录
            if existing_img and force:
                # 更新现有记录
                existing_img.file_size = info["file_size"]
                existing_img.width = info["width"]
                existing_img.height = info["height"]
                existing_img.mime_type = info["mime_type"]
                image_id = existing_img.id
                print(f"  更新图片: {dest_name} ({info['width']}x{info['height']})")
            else:
                # 创建新记录
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
                await session.flush()  # 获取 id
                image_id = img_record.id
                print(f"  新增图片: {dest_name} ({info['width']}x{info['height']})")

            # 插入或更新 backgrounds 记录
            bg_existing = await session.execute(
                select(Background).where(
                    Background.image_id == image_id,
                    Background.theme == theme,
                    Background.device == device,
                )
            )
            bg_record = bg_existing.scalar_one_or_none()

            if bg_record:
                bg_record.sort_order = sort_order
            else:
                bg_record = Background(
                    image_id=image_id,
                    theme=theme,
                    device=device,
                    sort_order=sort_order,
                )
                session.add(bg_record)
                created += 1

        await session.commit()

    print(f"\n完成! 新增 {created} 条背景记录，跳过 {skipped} 条")


if __name__ == "__main__":
    asyncio.run(main())
