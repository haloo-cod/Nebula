"""
初始化脚本 — 写入个人资料和社交链接
运行方式: cd blog-backend && python -m scripts.init_profile [--force]
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.database import engine, AsyncSessionLocal
from app.models import Base
from app.models.profile import Profile, SocialLink


PROFILE_DATA = {
    "name": "Starlit",
    "bio_md": "分享技术、生活和思考的个人博客",
    "avatar_url": "/uploads/images/backgrounds/dark-desktop-01.jpg",  # 暂用背景图做头像占位
    "cover_url": "/uploads/images/backgrounds/light-desktop-02.png",
}

SOCIAL_LINKS = [
    {"label": "GitHub", "icon": "github", "url": "https://github.com", "sort_order": 0},
    {"label": "Bilibili", "icon": "bilibili", "url": "https://space.bilibili.com", "sort_order": 1},
]


async def main():
    force = "--force" in sys.argv

    print("准备初始化个人资料" + ("（强制覆盖模式）" if force else ""))

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # Profile（singleton id=1）
        result = await session.execute(select(Profile).where(Profile.id == 1))
        existing = result.scalar_one_or_none()

        if existing and not force:
            print("  跳过 Profile（已存在）")
        elif existing and force:
            existing.name = PROFILE_DATA["name"]
            existing.bio_md = PROFILE_DATA["bio_md"]
            existing.avatar_url = PROFILE_DATA["avatar_url"]
            existing.cover_url = PROFILE_DATA["cover_url"]
            print("  更新 Profile")
        else:
            profile = Profile(
                id=1,
                name=PROFILE_DATA["name"],
                bio_md=PROFILE_DATA["bio_md"],
                avatar_url=PROFILE_DATA["avatar_url"],
                cover_url=PROFILE_DATA["cover_url"],
            )
            session.add(profile)
            print("  新增 Profile")

        # Social Links
        for link_data in SOCIAL_LINKS:
            link_existing = await session.execute(
                select(SocialLink).where(SocialLink.label == link_data["label"])
            )
            link_record = link_existing.scalar_one_or_none()

            if link_record and not force:
                print(f"  跳过社交链接（已存在）: {link_data['label']}")
            elif link_record and force:
                link_record.icon = link_data["icon"]
                link_record.url = link_data["url"]
                link_record.sort_order = link_data["sort_order"]
                print(f"  更新社交链接: {link_data['label']}")
            else:
                link = SocialLink(
                    label=link_data["label"],
                    icon=link_data["icon"],
                    url=link_data["url"],
                    sort_order=link_data["sort_order"],
                )
                session.add(link)
                print(f"  新增社交链接: {link_data['label']}")

        await session.commit()

    print("\n完成!")


if __name__ == "__main__":
    asyncio.run(main())
