"""
初始化脚本 — 将前端深夜酒馆硬编码数据写入后端数据库
运行方式: cd blog-backend && python -m scripts.init_tavern [--force]
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.database import engine, AsyncSessionLocal
from app.models import Base
from app.models.tavern import TavernPost


# 前端 midnight-tavern.vue 中的硬编码数据
TAVERN_DATA = [
    {
        "author": "赶末班车的人",
        "topic": "今天差点哭出来",
        "body": "加班到十点半，赶上最后一班地铁。车厢里只有三个人，我靠着门，眼泪突然就掉下来了。不知道是累的还是委屈。明天还要继续，但至少今天撑过去了。",
    },
    {
        "author": "躲雨的猫",
        "topic": "捡到一点好运气",
        "body": "下午突然暴雨，没带伞。躲在便利店门口的时候，一个路过的阿姨把伞塞给我说'年轻人别淋雨'。伞是透明的，上面印着小花。世界有时候真的很温柔。",
    },
    {
        "author": "旧车票",
        "topic": "没说出口的话",
        "body": "翻抽屉找东西，掉出来一张两年前的高铁票。那天送你去另一个城市，站台上想说'别走'，最后只说了'路上小心'。票根都皱了，我还留着。",
    },
    {
        "author": "亮着灯的窗",
        "topic": "终于做完了",
        "body": "毕设论文终于过了。答辩的时候老师问了个刁钻问题，我居然接住了。走出教室那一刻，阳光特别好。四年了，不管怎样，我真的毕业了。",
    },
    {
        "author": "安静的星星",
        "topic": "想睡个好觉",
        "body": "失眠第五天。数羊没用，喝牛奶没用，白噪音也没用。脑子里反复放映白天开会时说错的那句话。明明没人在意，但我就是放不下。好想有个开关可以关掉大脑。",
    },
    {
        "author": "冰镇汽水",
        "topic": "小小开心",
        "body": "今天去超市，发现最喜欢的那款限定汽水又上架了！买了三瓶，一瓶现在喝，一瓶明天喝，一瓶放冰箱里看着就开心。有时候快乐就是这么简单。",
    },
    {
        "author": "深夜食堂",
        "topic": "凌晨三点的泡面",
        "body": "写代码写到凌晨三点，泡了一碗面。加了两个蛋，番茄酱挤了个笑脸。窗外城市安静得像另一个世界。这碗面，是今天最好吃的一餐。",
    },
    {
        "author": "路灯下的影子",
        "topic": "散步的意义",
        "body": "晚上十一点出门散步，没有目的地。经过关门的花店、亮着暖光的咖啡馆、一只蹲在墙头的猫。走了四十分钟，什么都没想明白，但心情好了很多。",
    },
]


async def main():
    force = "--force" in sys.argv

    print(f"准备初始化 {len(TAVERN_DATA)} 条酒馆留言" + ("（强制覆盖模式）" if force else ""))

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        created = 0
        skipped = 0

        for data in TAVERN_DATA:
            # 按 author + topic 判断是否已存在
            existing = await session.execute(
                select(TavernPost).where(
                    TavernPost.author == data["author"],
                    TavernPost.topic == data["topic"],
                )
            )
            existing_post = existing.scalar_one_or_none()

            if existing_post and not force:
                print(f"  跳过（已存在）: {data['author']} - {data['topic']}")
                skipped += 1
                continue

            if existing_post and force:
                existing_post.body = data["body"]
                print(f"  更新: {data['author']} - {data['topic']}")
            else:
                post = TavernPost(
                    author=data["author"],
                    topic=data["topic"],
                    body=data["body"],
                    ip_hash="init_script",
                    is_visible=True,
                )
                session.add(post)
                created += 1
                print(f"  新增: {data['author']} - {data['topic']}")

        await session.commit()

    print(f"\n完成! 新增 {created} 条，跳过 {skipped} 条")


if __name__ == "__main__":
    asyncio.run(main())
