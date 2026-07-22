"""
初始化脚本 — 将前端友链静态数据写入后端数据库
运行方式: cd blog-backend && python -m scripts.init_friends [--force]
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.database import engine, AsyncSessionLocal
from app.models import Base
from app.models.friend import Friend


# 前端 friends.ts 中的静态数据
FRIENDS_DATA = [
    {
        "name": "暮色工坊",
        "bio": "记录前端、设计和一些慢慢变好的日常。",
        "avatar": "https://api.dicebear.com/9.x/adventurer/svg?seed=twilight",
        "url": "https://example.com",
    },
    {
        "name": "星河手札",
        "bio": "关于 Vue、工程化和个人知识库的碎片笔记。",
        "avatar": "https://api.dicebear.com/9.x/adventurer/svg?seed=galaxy",
        "url": "https://vuejs.org",
    },
    {
        "name": "北巷代码",
        "bio": "偏爱干净代码,也喜欢把复杂问题讲清楚。",
        "avatar": "https://api.dicebear.com/9.x/adventurer/svg?seed=lane",
        "url": "https://vite.dev",
    },
    {
        "name": "浮光档案",
        "bio": "照片、旅行和那些值得被保存的小瞬间。",
        "avatar": "https://api.dicebear.com/9.x/adventurer/svg?seed=glimmer",
        "url": "https://developer.mozilla.org",
    },
    {
        "name": "青柠实验室",
        "bio": "折腾工具、自动化和效率系统的个人实验田。",
        "avatar": "https://api.dicebear.com/9.x/adventurer/svg?seed=lime",
        "url": "https://github.com",
    },
    {
        "name": "半夏书房",
        "bio": "读书、写作和偶尔出现的技术长文。",
        "avatar": "https://api.dicebear.com/9.x/adventurer/svg?seed=summer",
        "url": "https://www.wikipedia.org",
    },
]


async def main():
    force = "--force" in sys.argv

    print(f"准备初始化 {len(FRIENDS_DATA)} 条友链" + ("（强制覆盖模式）" if force else ""))

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        created = 0
        skipped = 0

        for order, data in enumerate(FRIENDS_DATA):
            # 按名称判断是否已存在
            existing = await session.execute(
                select(Friend).where(Friend.name == data["name"])
            )
            existing_friend = existing.scalar_one_or_none()

            if existing_friend and not force:
                print(f"  跳过（已存在）: {data['name']}")
                skipped += 1
                continue

            if existing_friend and force:
                existing_friend.bio = data["bio"]
                existing_friend.avatar = data["avatar"]
                existing_friend.url = data["url"]
                existing_friend.sort_order = order
                print(f"  更新: {data['name']}")
            else:
                friend = Friend(
                    name=data["name"],
                    bio=data["bio"],
                    avatar=data["avatar"],
                    url=data["url"],
                    sort_order=order,
                )
                session.add(friend)
                created += 1
                print(f"  新增: {data['name']}")

        await session.commit()

    print(f"\n完成! 新增 {created} 条，跳过 {skipped} 条")


if __name__ == "__main__":
    asyncio.run(main())
