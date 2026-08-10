# Starlit Blog

> 当前版本支持图片和 MP4/WebM/MOV 视频背景。视频可由后台上传，也可从文件管理中的视频选择；桌面端使用 WebGL 液态玻璃采样，移动端使用 CSS 毛玻璃。

一个前后端分离的个人博客与内容管理系统，包含公开博客、图书阅读、相册、说说、藏宝阁、自习室、访问统计和管理后台。

## 特性

- Vue 3 + TypeScript + Vite 前端 SPA
- FastAPI + SQLAlchemy 2.0 异步后端
- Markdown 文章管理、导入、导出和代码高亮
- JWT 登录、刷新令牌、邮箱验证和 GitHub OAuth
- 文章、相册、图书、背景图、轮播图、友链和文件管理
- WebGL 液态玻璃效果，桌面端默认启用，移动端默认使用 CSS 毛玻璃
- EPUB 阅读器、访问统计和管理员后台
- SQLite 开箱即用，同时保留迁移到 PostgreSQL 的配置空间

## 目录结构

```text
My_blog/
├── blog-frontend/       # Vue 3 前端
├── blog-backend/        # FastAPI 后端
├── docs/                # 架构、API、数据库和部署文档
├── AGENTS.md            # 项目开发约定
└── README.md
```

## 环境要求

- Node.js `20.19+` 或 `22.12+`
- pnpm
- Python `3.11+`

## 本地运行

### 后端

```bash
cd blog-backend
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
```

编辑 `.env`，至少设置一个随机的 `SECRET_KEY` 和长度不少于 12 位的 `ADMIN_PASSWORD`，然后启动：

```bash
python main.py
```

后端默认地址为 `http://localhost:8000`，健康检查地址为 `http://localhost:8000/health`。

### 前端

```bash
cd blog-frontend
pnpm install
cp .env.example .env
pnpm dev
```

前端默认地址为 `http://localhost:5173`。开发环境下，如果没有设置 `VITE_API_BASE_URL`，前端会请求 `http://localhost:8000`。

常用命令：

```bash
pnpm type-check
pnpm build
pnpm test:unit
```

## 资源与数据

生产环境的图片、文章、图书和上传文件由后端管理，运行时数据不会提交到仓库。前端 `src/assets/` 中保留了按用途划分的空目录，方便开发者放入本地 UI 预览资源。

后端运行时目录包括：

- `blog-backend/uploads/`：上传图片、EPUB 和其他文件
- `blog-backend/content/`：Markdown 内容
- `blog-backend/data/`：动态 JSON 数据
- `blog-backend/blog.db`：SQLite 数据库

这些目录均不应提交到公开仓库。仓库中的 `.env.example` 只提供配置模板，不包含真实密钥。

## 文档

- `docs/architecture.md`：系统架构
- `docs/api-reference.md`：API 参考
- `docs/database.md`：数据库说明
- `docs/deployment.md`：部署说明
- `docs/frontend-features.md`：液态玻璃与 EPUB 阅读器实现说明
- `AGENTS.md`：开发约定

## 当前状态

项目仍在持续开发中，API 和管理后台可能发生变化。欢迎提交 Issue 或 Pull Request。

文档补充：

- `docs/background-media.md`：图片/视频背景、媒体访问和引用保护
- `docs/production-update.md`：生产环境更新、备份和重启流程

## License

本项目使用 [MIT License](LICENSE)。
