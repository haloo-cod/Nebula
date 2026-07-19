# 部署指南

## 环境要求

| 组件 | 版本要求 |
|------|---------|
| Node.js | `≥20.19.0` 或 `≥22.12.0` |
| pnpm | 最新版 |
| Python | ≥3.11 |
| SQLite | 系统自带即可 |

## 快速启动（开发模式）

### 1. 克隆项目

```bash
git clone https://github.com/your-username/My_blog.git
cd My_blog
```

### 2. 启动后端

```bash
cd blog-backend

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 初始化数据库（自动创建表 + 默认管理员）
python -m scripts.init_posts
python -m scripts.init_gallery
python -m scripts.init_books
python -m scripts.init_backgrounds
python -m scripts.init_carousel
python -m scripts.init_albums
python -m scripts.init_friends
python -m scripts.init_treasures
python -m scripts.init_profile
python -m scripts.init_tavern

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端启动后可访问：
- API: `http://localhost:8000/api/v1/`
- Swagger 文档: `http://localhost:8000/docs`
- ReDoc 文档: `http://localhost:8000/redoc`

### 3. 启动前端

```bash
cd blog-frontend

# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev
```

前端启动后访问：`http://localhost:5173`

---

## 环境变量

### 后端 (`blog-backend/.env`)

```env
# 应用配置
SECRET_KEY=change-me-in-production
DEBUG=True

# 数据库
DATABASE_URL=sqlite+aiosqlite:///./blog.db

# 管理员默认账户
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

# CORS 允许来源（逗号分隔）
CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]

# 文件上传限制
MAX_IMAGE_SIZE=10485760  # 10MB
```

### 前端 (`blog-frontend/.env.local`)

```env
# API 开关：设为 false 时禁用所有 API 调用，使用本地静态数据
VITE_USE_API=true

# API 地址（上线时改为实际域名）
# VITE_API_BASE_URL=https://your-domain.com
```

---

## 生产部署

### 方案一：Nginx 反向代理（推荐）

```
┌─────────────┐      ┌─────────────┐
│   Nginx     │ ───→ │  Uvicorn    │ :8000
│   :80/443   │      │  (FastAPI)  │
│             │      └─────────────┘
│  /          │ ──→  前端静态文件
│  /api/      │ ──→  proxy_pass :8000
│  /uploads/  │ ──→  proxy_pass :8000 (或直接 alias)
└─────────────┘
```

#### 1. 构建前端

```bash
cd blog-frontend
pnpm build
# 产物在 dist/ 目录
```

#### 2. Nginx 配置

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    root /path/to/blog-frontend/dist;
    index index.html;

    # SPA fallback（Hash 模式其实不需要，但保险起见）
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API 反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # 静态文件（上传的图片/EPUB）
    location /uploads/ {
        proxy_pass http://127.0.0.1:8000;
        # 或者直接映射目录（更高效）：
        # alias /path/to/blog-backend/uploads/;
    }
}
```

#### 3. 启动后端（生产模式）

```bash
cd blog-backend
source .venv/bin/activate

# 使用 gunicorn + uvicorn worker
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# 或使用 systemd 管理（推荐）
```

#### 4. systemd 服务文件示例

```ini
# /etc/systemd/system/blog-backend.service
[Unit]
Description=Starlit Blog Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/blog-backend
Environment="PATH=/path/to/blog-backend/.venv/bin"
ExecStart=/path/to/blog-backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 方案二：Docker Compose

> 待补充（TODO）

---

## 数据初始化

首次部署后需要运行初始化脚本将演示数据导入数据库：

```bash
cd blog-backend
source .venv/bin/activate

# 按顺序运行（有依赖关系）
python -m scripts.init_posts       # 13 篇博文
python -m scripts.init_gallery     # 4 个展览项目
python -m scripts.init_books       # 21 本图书 + 封面提取
python -m scripts.init_backgrounds # 9 张背景图
python -m scripts.init_carousel    # 7 张轮播图
python -m scripts.init_albums      # 3 个相册 + 7 张照片
python -m scripts.init_friends     # 6 条友链
python -m scripts.init_treasures   # 26 条藏宝
python -m scripts.init_profile     # 个人资料 + 社交链接
python -m scripts.init_tavern      # 8 条酒馆留言
```

所有脚本支持 `--force` 参数强制覆盖已有数据：

```bash
python -m scripts.init_posts --force
```

---

## 前端无后端运行（纯前端模式）

如果只想展示前端效果，不需要启动后端：

```bash
cd blog-frontend

# 创建 .env.local 禁用 API
echo "VITE_USE_API=false" > .env.local

pnpm dev
```

此时所有页面使用 `src/data/` 下的静态数据和 `src/assets/` 下的本地图片。

---

## HTTPS 配置

推荐使用 Let's Encrypt + Certbot：

```bash
sudo certbot --nginx -d your-domain.com
```

---

## 数据备份

关键数据文件：

```
blog-backend/
├── blog.db              # SQLite 数据库（核心！）
├── data/
│   ├── moments.json     # 说说数据
│   └── comments.json    # 评论数据
├── uploads/             # 所有上传文件
└── content/             # Markdown 原文
```

备份建议：

```bash
# 每日备份数据库和数据目录
tar -czf backup-$(date +%Y%m%d).tar.gz \
  blog-backend/blog.db \
  blog-backend/data/ \
  blog-backend/uploads/ \
  blog-backend/content/
```

---

## 迁移到 PostgreSQL（可选）

当并发写入成为瓶颈时，可以迁移到 PostgreSQL：

1. 安装 `asyncpg`：`pip install asyncpg`
2. 修改 `.env`：`DATABASE_URL=postgresql+asyncpg://user:pass@localhost/blogdb`
3. 重新运行初始化脚本

代码层面无需修改（SQLAlchemy ORM 抽象了数据库差异）。
