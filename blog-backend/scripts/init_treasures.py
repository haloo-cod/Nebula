"""
初始化脚本 — 将前端藏宝阁静态数据写入后端数据库
运行方式: cd blog-backend && python -m scripts.init_treasures [--force]
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.database import engine, AsyncSessionLocal
from app.models import Base
from app.models.treasure import Treasure


# 前端 treasures.ts 中的全部静态数据
TREASURES_DATA = [
    # ===== 开源项目 =====
    {"slug": "vue3", "title": "Vue 3", "description": "渐进式 JavaScript 框架，组合式 API + 响应式系统，构建现代 Web 应用的首选。", "category": "开源项目", "icon": "💚", "url": "https://github.com/vuejs/core", "tags": ["前端", "框架", "TypeScript"]},
    {"slug": "vite", "title": "Vite", "description": "下一代前端构建工具，极速冷启动 + 即时热更新，开发体验飞跃。", "category": "开源项目", "icon": "⚡", "url": "https://github.com/vitejs/vite", "tags": ["构建工具", "前端"]},
    {"slug": "tailwindcss", "title": "Tailwind CSS", "description": "实用优先的 CSS 框架，用 class 组合构建任意设计，无需离开 HTML。", "category": "开源项目", "icon": "🎨", "url": "https://github.com/tailwindlabs/tailwindcss", "tags": ["CSS", "样式"]},
    {"slug": "fastapi", "title": "FastAPI", "description": "高性能 Python Web 框架，基于类型注解自动生成文档，异步优先。", "category": "开源项目", "icon": "🚀", "url": "https://github.com/tiangolo/fastapi", "tags": ["Python", "后端", "API"]},
    {"slug": "pinia", "title": "Pinia", "description": "Vue 官方状态管理库，轻量直觉，完美支持 TypeScript 和 DevTools。", "category": "开源项目", "icon": "🍍", "url": "https://github.com/vuejs/pinia", "tags": ["Vue", "状态管理"]},
    {"slug": "nuxt", "title": "Nuxt 3", "description": "基于 Vue 3 的全栈框架，SSR/SSG/ISR 开箱即用，文件路由 + 自动导入。", "category": "开源项目", "icon": "🌊", "url": "https://github.com/nuxt/nuxt", "tags": ["Vue", "全栈", "SSR"]},
    {"slug": "prisma", "title": "Prisma", "description": "下一代 Node.js ORM，类型安全的数据库操作，自动生成查询客户端。", "category": "开源项目", "icon": "💎", "url": "https://github.com/prisma/prisma", "tags": ["数据库", "ORM", "TypeScript"]},
    {"slug": "shadcn-vue", "title": "shadcn-vue", "description": "基于 Radix Vue 的精美组件集合，复制粘贴到项目里，完全可控。", "category": "开源项目", "icon": "🧩", "url": "https://github.com/radix-vue/shadcn-vue", "tags": ["Vue", "UI", "组件库"]},
    {"slug": "unocss", "title": "UnoCSS", "description": "即时按需的原子化 CSS 引擎，极快、灵活，兼容 Tailwind/Windi 语法。", "category": "开源项目", "icon": "🎯", "url": "https://github.com/unocss/unocss", "tags": ["CSS", "原子化"]},
    {"slug": "drizzle-orm", "title": "Drizzle ORM", "description": "轻量级 TypeScript ORM，SQL-like 查询语法，零依赖，边缘运行时友好。", "category": "开源项目", "icon": "💧", "url": "https://github.com/drizzle-team/drizzle-orm", "tags": ["数据库", "ORM", "TypeScript"]},
    # ===== 工具 =====
    {"slug": "excalidraw", "title": "Excalidraw", "description": "手绘风格的在线白板工具，支持协作，适合头脑风暴和架构草图。", "category": "工具", "icon": "✏️", "url": "https://excalidraw.com", "tags": ["绘图", "协作"]},
    {"slug": "squoosh", "title": "Squoosh", "description": "Google 出品的在线图片压缩工具，支持多种格式和编解码器对比。", "category": "工具", "icon": "🖼️", "url": "https://squoosh.app", "tags": ["图片", "压缩"]},
    {"slug": "ray-so", "title": "Ray.so", "description": "生成精美代码截图，支持自定义主题、字体、背景，分享代码更好看。", "category": "工具", "icon": "📸", "url": "https://ray.so", "tags": ["代码", "截图"]},
    {"slug": "regex101", "title": "Regex101", "description": "在线正则表达式测试器，实时匹配高亮、详细解释、多语言支持。", "category": "工具", "icon": "🔍", "url": "https://regex101.com", "tags": ["正则", "调试"]},
    {"slug": "figma", "title": "Figma", "description": "云端协作设计工具，UI/UX 设计行业标准，实时多人编辑。", "category": "工具", "icon": "🖌️", "url": "https://www.figma.com", "tags": ["设计", "UI", "协作"]},
    {"slug": "linear", "title": "Linear", "description": "为开发者打造的项目管理工具，极简高效，流畅体验碾压 Jira。", "category": "工具", "icon": "📐", "url": "https://linear.app", "tags": ["项目管理", "效率"]},
    {"slug": "can-i-use", "title": "Can I Use", "description": "查询前端 API 和 CSS 属性的浏览器兼容性，开发前端的必备参考。", "category": "工具", "icon": "🌐", "url": "https://caniuse.com", "tags": ["兼容性", "前端"]},
    {"slug": "json-crack", "title": "JSON Crack", "description": "将 JSON 数据可视化为交互式图表，快速理解复杂嵌套结构。", "category": "工具", "icon": "🧬", "url": "https://jsoncrack.com", "tags": ["JSON", "可视化"]},
    {"slug": "devtoys", "title": "DevToys", "description": "开发者瑞士军刀，集合编解码、格式化、Hash 等几十种小工具。", "category": "工具", "icon": "🧰", "url": "https://devtoys.app", "tags": ["效率", "多合一"]},
    # ===== 资源下载 =====
    {"slug": "jetbrains-mono", "title": "JetBrains Mono", "description": "专为开发者设计的等宽字体，连字美观，长时间阅读不疲劳。", "category": "资源下载", "icon": "🔤", "url": "https://www.jetbrains.com/lp/mono/", "download_file": "https://github.com/JetBrains/JetBrainsMono/releases", "tags": ["字体", "开发"]},
    {"slug": "vscode-icons", "title": "Material Icon Theme", "description": "VSCode 最受欢迎的图标主题之一，文件类型一目了然。", "category": "资源下载", "icon": "📁", "url": "https://marketplace.visualstudio.com/items?itemName=PKief.material-icon-theme", "tags": ["VSCode", "主题"]},
    {"slug": "developer-wallpapers", "title": "开发者壁纸合集", "description": "精选极简/暗色系桌面壁纸，适合程序员的审美和屏幕。", "category": "资源下载", "icon": "🌌", "url": "#", "download_file": "#", "tags": ["壁纸", "美化"]},
    {"slug": "fira-code", "title": "Fira Code", "description": "带编程连字的等宽字体，免费开源，主流编辑器全支持。", "category": "资源下载", "icon": "✒️", "url": "https://github.com/tonsky/FiraCode", "download_file": "https://github.com/tonsky/FiraCode/releases", "tags": ["字体", "开源"]},
    {"slug": "cascadia-code", "title": "Cascadia Code", "description": "微软出品的等宽字体，专为 Windows Terminal 设计，清晰利落。", "category": "资源下载", "icon": "💠", "url": "https://github.com/microsoft/cascadia-code", "download_file": "https://github.com/microsoft/cascadia-code/releases", "tags": ["字体", "终端"]},
    {"slug": "catppuccin-theme", "title": "Catppuccin", "description": "社区驱动的柔和配色方案，覆盖 200+ 应用和编辑器，护眼又美观。", "category": "资源下载", "icon": "🐱", "url": "https://github.com/catppuccin/catppuccin", "download_file": "https://github.com/catppuccin/catppuccin", "tags": ["主题", "配色"]},
    {"slug": "nerd-fonts", "title": "Nerd Fonts", "description": "给编程字体打补丁，注入 3000+ 图标字形，终端美化必备。", "category": "资源下载", "icon": "🤓", "url": "https://www.nerdfonts.com", "download_file": "https://github.com/ryanoasis/nerd-fonts/releases", "tags": ["字体", "图标", "终端"]},
]


async def main():
    force = "--force" in sys.argv

    print(f"准备初始化 {len(TREASURES_DATA)} 条藏宝" + ("（强制覆盖模式）" if force else ""))

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        created = 0
        skipped = 0

        for order, data in enumerate(TREASURES_DATA):
            slug = data["slug"]

            existing = await session.execute(
                select(Treasure).where(Treasure.slug == slug)
            )
            existing_treasure = existing.scalar_one_or_none()

            if existing_treasure and not force:
                print(f"  跳过（已存在）: {data['title']}")
                skipped += 1
                continue

            if existing_treasure and force:
                existing_treasure.title = data["title"]
                existing_treasure.description = data["description"]
                existing_treasure.category = data["category"]
                existing_treasure.icon = data["icon"]
                existing_treasure.url = data["url"]
                existing_treasure.download_file = data.get("download_file", "")
                existing_treasure.tags = data["tags"]
                existing_treasure.sort_order = order
                print(f"  更新: {data['title']}")
            else:
                treasure = Treasure(
                    slug=slug,
                    title=data["title"],
                    description=data["description"],
                    category=data["category"],
                    icon=data["icon"],
                    url=data["url"],
                    download_file=data.get("download_file", ""),
                    tags=data["tags"],
                    sort_order=order,
                )
                session.add(treasure)
                created += 1
                print(f"  新增: {data['title']}")

        await session.commit()

    print(f"\n完成! 新增 {created} 条，跳过 {skipped} 条")


if __name__ == "__main__":
    asyncio.run(main())
