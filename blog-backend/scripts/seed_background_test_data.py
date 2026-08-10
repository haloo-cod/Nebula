"""为动态背景联调准备可重复执行的测试记录。"""

import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.background import Background
from app.services.analytics import utc_now

TEST_ITEMS = [
    ("dark", "desktop", "/api/v1/files/1/media", "video/mp4"),
    ("dark", "mobile", "/api/v1/files/1/media", "video/mp4"),
    ("light", "desktop", "https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4", "video/mp4"),
    ("light", "mobile", "https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4", "video/mp4"),
]

async def main() -> None:
    async with AsyncSessionLocal() as db:
        created = 0
        for theme, device, media_url, mime_type in TEST_ITEMS:
            stmt = select(Background).where(
                Background.theme == theme,
                Background.device == device,
                Background.media_url == media_url,
                Background.sort_order == 90,
            )
            if (await db.execute(stmt)).scalar_one_or_none():
                continue
            db.add(Background(
                image_id=None, media_type="video", media_url=media_url,
                poster_url="", mime_type=mime_type, file_size=0,
                theme=theme, device=device, sort_order=90,
                created_at=utc_now(), updated_at=utc_now(),
            ))
            created += 1
        await db.commit()
    print(f"Created {created} background test records (existing records unchanged).")

if __name__ == "__main__":
    asyncio.run(main())
