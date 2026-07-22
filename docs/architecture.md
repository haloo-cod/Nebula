# 项目架构总览

## 概述

Starlit Blog 是一个基于 **Vue 3 + FastAPI** 的全栈个人博客系统，前端采用液态玻璃（Liquid Glass）视觉风格，后端提供 RESTful API + SQLite 持久化。项目设计为开源模板，支持快速部署和二次开发。

## 技术栈

### 前端 (`blog-frontend/`)

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue 3 | 3.5+ | UI 框架（Composition API + `<script setup>`） |
| TypeScript | strict 模式 | 类型安全 |
| Vite | 8 | 构建工具 |
| Vue Router | 5 | 路由（Hash History 模式） |
| Pinia | 3 | 状态管理 |
| Tailwind CSS | v4 | 样式（CSS-first 配置，`@tailwindcss/vite` 插件） |
| marked | v18 | Markdown 渲染 |
| highlight.js | — | 代码高亮（12 种语言按需注册） |
| epubjs | — | EPUB 阅读器 |
| lunar-typescript | — | 中国农历数据 |

### 后端 (`blog-backend/`)

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | ≥3.11 | 运行时 |
| FastAPI | — | Web 框架 |
| SQLAlchemy | 2.0+ (async) | ORM |
| aiosqlite | — | SQLite 异步驱动 |
| Pydantic | v2 | 数据验证/序列化 |
| python-jose | — | JWT 认证 |
| bcrypt | — | 密码哈希 |
| Pillow | — | 图片处理（尺寸检测） |
| ebooklib | — | EPUB 元数据提取 |
| filelock | — | JSON 文件并发保护 |

### 数据存储

| 存储方式 | 内容 |
|----------|------|
| SQLite (`blog.db`) | 结构化数据（博文/图书/相册/友链/藏宝阁/背景图/轮播/个人资料/酒馆留言等） |
| JSON 文件 (`data/`) | 说说（moments）、评论（comments） — filelock 并发保护 |
| 文件系统 (`uploads/`) | 图片/EPUB/静态资源 |
| 文件系统 (`content/`) | Markdown 原文（博文/展览/关于页） |

## 前端特色实现

### Liquid Glass

液态玻璃不是简单地给每个面板添加 `backdrop-filter`。前端通过共享的 WebGL 渲染器，将多个 `LiquidGlass` 组件统一调度到一条渲染管线中。这里的“单一实例”指共享一个 WebGL context 和 renderer singleton，并不是页面只能有一个玻璃面板。每个面板仍然拥有独立的 canvas、尺寸、uniform 状态和背景纹理引用。

渲染器负责统一管理 WebGL 初始化、shader、纹理缓存、动画帧、实例注册以及 context 丢失恢复；组件本身只负责生命周期、尺寸同步、主题参数和交互轨迹。完整说明见 [`frontend-features.md`](frontend-features.md)。

### EPUB Reader

图书页面通过后端 API 获取分页元数据和受保护的 EPUB 资源，阅读器页面使用 `epubjs` 创建 EPUB 实例与 rendition，支持目录导航、分页/滚动模式、CFI 位置恢复、阅读主题、字体缩放和滚动到底自动切换章节。前端 `import.meta.glob()` 仅保留本地 UI 预览 fallback，不是生产图书资源的主要来源。完整说明见 [`frontend-features.md`](frontend-features.md)。

## 目录结构

```
My_blog/
├── blog-frontend/                 # Vue 3 前端 SPA
│   ├── src/
│   │   ├── api/                   # 后端 API 调用层
│   │   ├── assets/                # 静态资源（图片/CSS/Markdown）
│   │   ├── components/            # 共享组件
│   │   │   ├── liquid-glass/      # 液态玻璃 WebGL 渲染器
│   │   │   ├── panels/            # 首页面板组件
│   │   │   ├── music/             # 音乐播放器
│   │   │   └── study/             # 自习室组件
│   │   ├── composables/           # 可复用逻辑（useTypewriter/useMusic 等）
│   │   ├── data/                  # 静态数据层（fallback + site-text）
│   │   ├── i18n/                  # 国际化
│   │   ├── router/                # 路由配置
│   │   ├── stores/                # Pinia 状态管理
│   │   ├── types/                 # TypeScript 类型定义
│   │   ├── utils/                 # 工具函数
│   │   ├── views/                 # 页面视图（按路由分文件夹）
│   │   ├── App.vue                # 根组件
│   │   ├── main.ts                # 入口
│   │   └── env.d.ts               # 全局类型声明
│   ├── public/
│   ├── index.html
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── package.json
│
├── blog-backend/                  # FastAPI 后端
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py            # 公共依赖（认证/鉴权）
│   │   │   └── v1/               # v1 版本路由
│   │   │       ├── router.py      # 路由汇总
│   │   │       ├── auth.py        # 认证（登录/注册）
│   │   │       ├── posts.py       # 博文 CRUD
│   │   │       ├── moments.py     # 说说
│   │   │       ├── comments.py    # 评论
│   │   │       ├── books.py       # 图书（分页+搜索）
│   │   │       ├── gallery.py     # 展览
│   │   │       ├── albums.py      # 相册
│   │   │       ├── images.py      # 图床
│   │   │       ├── backgrounds.py # 背景图
│   │   │       ├── carousel.py    # 首页轮播
│   │   │       ├── friends.py     # 友链
│   │   │       ├── treasures.py   # 藏宝阁
│   │   │       ├── profile.py     # 个人资料
│   │   │       ├── tavern.py      # 深夜酒馆
│   │   │       └── about.py       # 关于页内容
│   │   ├── models/                # SQLAlchemy ORM 模型
│   │   ├── schemas/               # Pydantic 请求/响应模型
│   │   ├── services/              # 业务逻辑层
│   │   ├── utils/                 # 工具（security.py — JWT/bcrypt）
│   │   ├── config.py              # 全局配置
│   │   ├── database.py            # 数据库引擎
│   │   └── main.py                # FastAPI 入口
│   ├── scripts/                   # 初始化/迁移脚本
│   ├── content/                   # Markdown 内容
│   ├── data/                      # JSON 数据（说说/评论/友链）
│   ├── uploads/                   # 上传文件
│   └── requirements.txt
│
├── docs/                          # 项目文档
└── AGENTS.md                      # AI 开发助手指令文件
```

## 核心设计理念

### 1. 渐进式 API 迁移

前端所有页面都采用 **API + Fallback** 双层数据策略：

```
onMounted → 调用后端 API → 成功则使用 API 数据
                          → 失败则保留本地静态数据（import.meta.glob / 硬编码）
```

这意味着：
- **前端可以独立运行**（不启动后端也能展示内容）
- **后端挂了不影响用户体验**（静默降级到静态数据）
- 通过 `VITE_USE_API=false` 环境变量可彻底禁用 API 调用

### 2. 页面文案集中管理

所有页面的 kicker/title/subtitle 统一在 `src/data/site-text.ts` 中定义，修改文案只需编辑一个文件。未来可对接后端 SiteConfig API 实现管理员后台热更新。

### 3. 认证体系

- **当前**：管理员 JWT（账户由环境变量配置）
- **计划**：普通用户注册（邮箱+密码 / GitHub OAuth）

### 4. 部署友好

- 前端：Hash History 模式 + `base: './'`，build 产物可放在任意子目录
- 后端：SQLite 零配置，上线只需部署单个 Python 进程
- 未来可平滑迁移到 PostgreSQL（只改 `DATABASE_URL`）

## 路由表

| 路径 | 页面 | 说明 |
|------|------|------|
| `/` | 首页 | 个人资料面板 + 轮播 + 仪表盘 |
| `/blog` | 博文列表 | 玻璃卡片网格 + 分页 |
| `/post/:slug` | 博文详情 | Markdown 渲染 + 评论 |
| `/archive` | 归档 | 时间线 + 拖拽交互 |
| `/archive/tree` | 归档树 | 树形年月结构 |
| `/moments` | 说说 | 瀑布流 + 无限滚动 |
| `/books` | 书库 | 玻璃书格 + 搜索 + 分页 |
| `/books/read/:slug` | 阅读器 | EPUB 全屏阅读 |
| `/images` | 图片/相册 | 相册网格 → 瀑布流 → 灯箱 |
| `/gallery` | 展览 | 项目卡片 |
| `/gallery/project/:slug` | 项目详情 | Markdown 文档 |
| `/friends` | 友链 | 鱼缸动画 + 链接卡片 |
| `/treasure` | 藏宝阁 | 分类筛选 + 分页 |
| `/about` | 关于 | 个人介绍 + 活动热力图 + 时间线 |
| `/midnight-tavern` | 深夜酒馆 | 匿名留言（彩蛋页，隐藏导航栏） |
| `/study-room` | 自习室 | 番茄钟 + 日程 + 历史（localStorage） |

## 功能模块状态

| 模块 | 后端 API | 前端对接 | 管理后台 |
|------|:---:|:---:|:---:|
| 博文 | ✅ | ✅ | 计划中 |
| 评论 | ✅ | ✅ | 计划中 |
| 说说 | ✅ | ✅ | 计划中 |
| 图书 | ✅（含搜索分页） | ✅ | 计划中 |
| 展览 | ✅ | ✅ | 计划中 |
| 相册 | ✅ | ✅ | 计划中 |
| 友链 | ✅ | ✅ | 计划中 |
| 藏宝阁 | ✅ | ✅ | 计划中 |
| 背景图 | ✅ | ✅ | 计划中 |
| 轮播图 | ✅ | ✅ | 计划中 |
| 个人资料 | ✅ | ✅ | 计划中 |
| 深夜酒馆 | ✅（含 IP 限频） | ✅ | 计划中 |
| 图床 | ✅ | — | 计划中 |
| 自习室 | —（localStorage） | ✅ | — |
| 用户系统 | 计划中 | 计划中 | 计划中 |
| 管理后台 | — | 计划中 | 计划中 |
