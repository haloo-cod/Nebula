# API 参考文档

## 基础信息

| 项目 | 值 |
|------|---|
| Base URL | `http://localhost:8000` |
| API 前缀 | `/api/v1` |
| 认证方式 | 短期 Bearer Token（JWT）+ HttpOnly Refresh Cookie |
| 自动文档 | Swagger UI: `/docs`，ReDoc: `/redoc` |
| 静态文件 | `/uploads/*`（图片/EPUB/资源文件） |

## 认证

### 用户注册、登录与会话

前台账户支持用户名/邮箱密码注册、登录、刷新和退出。刷新令牌不返回到 JavaScript，而是由后端写入限定在 `/api/v1/auth` 路径下的 HttpOnly Cookie。

#### 注册

```
POST /api/v1/auth/register
Content-Type: application/json

{
  "username": "starlit",
  "email": "user@example.com",
  "password": "<password>"
}

→ 201 { "access_token": "eyJ...", "token_type": "bearer" }
```

#### 登录获取 Token

```
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "用户名或邮箱",
  "password": "<password>"
}

→ 200 { "access_token": "eyJ...", "token_type": "bearer" }
```

#### 刷新和退出

```
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
```

浏览器请求需要携带 Cookie。刷新接口会轮换旧会话，退出接口会撤销当前刷新会话并清除 Cookie。

#### 当前用户与邮箱验证

```
GET  /api/v1/auth/me
POST /api/v1/auth/email-verification/send
GET  /api/v1/auth/email-verification/confirm?token=<token>
```

邮箱验证是否强制由后端配置决定。

#### GitHub OAuth

```
GET /api/v1/auth/github?redirect=/target
GET /api/v1/auth/github/callback
```

GitHub 回调成功后，后端创建或恢复账户并写入 Refresh Cookie，再跳转到前端 `/auth/callback` 页面。

### 使用 Token

在需要认证的请求中添加 Header：

```
Authorization: Bearer eyJ...
```

### 权限标记说明

- **公开** — 无需认证
- **已登录用户** — 需要有效 Bearer Token
- **管理员** — 需要有效 Bearer Token + `is_admin = true`

---

## 博文 (`/api/v1/posts`)

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/posts` | 公开 | 博文列表（分页+分类筛选） |
| GET | `/posts/stats` | 公开 | 按年统计数据 |
| GET | `/posts/{slug}` | 公开 | 博文详情（含 Markdown 原文） |
| POST | `/posts` | 管理员 | 创建博文 |
| PUT | `/posts/{slug}` | 管理员 | 更新博文 |
| DELETE | `/posts/{slug}` | 管理员 | 删除博文 |
| POST | `/posts/{slug}/rerender` | 管理员 | 重新渲染 HTML 缓存 |

### GET /posts 参数

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `page` | int | 1 | 页码（≥1） |
| `page_size` | int | 12 | 每页条数（1-100） |
| `category` | string | — | 分类筛选 |

### 响应示例

```json
{
  "items": [
    {
      "slug": "hello-world",
      "title": "Hello World",
      "description": "第一篇博文",
      "category": "技术",
      "tags": ["Vue", "TypeScript"],
      "date": "2026-07-01",
      "cover_url": "/uploads/images/2026/07/abc_cover.jpg",
      "draft": false,
      "created_at": "2026-07-01T10:00:00"
    }
  ],
  "total": 13
}
```

---

## 评论 (`/api/v1/comments`)

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/comments?page_key=xxx` | 公开 | 获取指定页面的评论列表 |
| POST | `/comments` | 公开 | 发表评论 |
| POST | `/comments/batch-count` | 公开 | 批量获取多个页面的评论数 |
| DELETE | `/comments/{id}` | 管理员 | 删除评论 |

### page_key 约定

| 场景 | page_key 格式 |
|------|--------------|
| 博文评论 | `post:hello-world` |
| 关于页评论 | `about` |
| 其他页面 | 自定义字符串 |

### POST /comments 请求体

```json
{
  "page_key": "post:hello-world",
  "author": "访客",
  "content": "写得好！",
  "parent_id": null
}
```

---

## 说说 (`/api/v1/moments`)

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/moments` | 公开 | 说说列表（分页） |
| GET | `/moments/{id}` | 公开 | 单条说说详情 |
| POST | `/moments` | 管理员 | 发布说说 |
| DELETE | `/moments/{id}` | 管理员 | 删除说说 |
| POST | `/moments/{id}/like` | 公开 | 点赞（IP 去重） |
| GET | `/moments/{id}/comments` | 公开 | 说说评论列表 |
| POST | `/moments/{id}/comments` | 公开 | 发表说说评论 |

### GET /moments 参数

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `page` | int | 1 | 页码 |
| `page_size` | int | 10 | 每页条数（1-50） |

---

## 图书 (`/api/v1/books`)

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/books` | 公开 | 图书列表（分页+搜索） |
| GET | `/books/{slug}` | 公开 | 图书详情 |
| POST | `/books` | 管理员 | 上传 EPUB 创建图书 |
| DELETE | `/books/{slug}` | 管理员 | 删除图书 |

### GET /books 参数

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `page` | int | 1 | 页码 |
| `page_size` | int | 20 | 每页条数（1-100） |
| `keyword` | string | — | 搜索关键词（模糊匹配标题/作者） |

### POST /books（multipart/form-data）

| 字段 | 类型 | 说明 |
|------|------|------|
| `file` | File | EPUB 文件（必需） |
| `title` | string | 书名（可选，不填则从 EPUB 元数据提取） |
| `author` | string | 作者（可选） |
| `description` | string | 简介（可选） |

---

## 展览 (`/api/v1/gallery`)

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/gallery` | 公开 | 展览项目列表 |
| GET | `/gallery/{slug}` | 公开 | 项目详情（含 Markdown） |
| POST | `/gallery` | 管理员 | 创建项目 |
| PUT | `/gallery/{slug}` | 管理员 | 更新项目 |
| DELETE | `/gallery/{slug}` | 管理员 | 删除项目 |

---

## 相册 (`/api/v1/albums`)

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/albums` | 公开 | 相册列表（含前 3 张预览图） |
| GET | `/albums/{id}` | 公开 | 相册详情（含全部照片） |
| POST | `/albums` | 管理员 | 创建相册 |
| PUT | `/albums/{id}` | 管理员 | 更新相册信息 |
| DELETE | `/albums/{id}` | 管理员 | 删除相册（级联删除照片记录） |
| POST | `/albums/{id}/photos` | 管理员 | 添加照片到相册 |
| DELETE | `/albums/{id}/photos/{photo_id}` | 管理员 | 删除照片 |
| PUT | `/albums/{id}/photos/reorder` | 管理员 | 调整照片排序 |

### 相册封面逻辑

- `cover_image_id` 为空 → 自动取第一张照片作封面
- `cover_image_id` 有值 → 使用指定图片

### POST /albums 请求体

```json
{
  "title": "旅行日记",
  "description": "2026 年春天的照片",
  "orientation": "portrait"
}
```

### POST /albums/{id}/photos 请求体

```json
{
  "image_id": 42,
  "caption": "日落时分"
}
```

---

## 图床 (`/api/v1/images`)

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| POST | `/images/upload` | 管理员 | 上传图片 |
| GET | `/images` | 管理员 | 图片列表（分页） |
| DELETE | `/images/{id}` | 管理员 | 删除图片 |

### POST /images/upload（multipart/form-data）

| 字段 | 类型 | 说明 |
|------|------|------|
| `file` | File | 图片文件 |

支持格式：`image/jpeg`、`image/png`、`image/webp`、`image/gif`、`image/svg+xml`

最大 10MB。

### 响应

```json
{
  "id": 1,
  "filename": "images/2026/07/abc_photo.jpg",
  "original_name": "my-photo.jpg",
  "url": "/uploads/images/2026/07/abc_photo.jpg",
  "file_size": 524288,
  "width": 1920,
  "height": 1080,
  "mime_type": "image/jpeg",
  "created_at": "2026-07-15T10:30:00"
}
```

---

## 背景图 (`/api/v1/backgrounds`)

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/backgrounds` | 公开 | 背景图列表（可按 theme/device 筛选） |
| POST | `/backgrounds` | 管理员 | 添加背景图 |
| DELETE | `/backgrounds/{id}` | 管理员 | 删除背景图 |
| PUT | `/backgrounds/reorder` | 管理员 | 调整排序 |

### GET /backgrounds 参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `theme` | string | `dark` 或 `light` |
| `device` | string | `desktop` 或 `mobile` |

---

## 首页轮播 (`/api/v1/carousel`)

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/carousel` | 公开 | 轮播图列表 |
| POST | `/carousel` | 管理员 | 添加轮播图 |
| DELETE | `/carousel/{id}` | 管理员 | 删除轮播图 |
| PUT | `/carousel/reorder` | 管理员 | 调整排序 |

---

## 友链 (`/api/v1/friends`)

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/friends` | 公开 | 友链列表 |
| POST | `/friends` | 管理员 | 添加友链 |
| PUT | `/friends/{id}` | 管理员 | 更新友链 |
| DELETE | `/friends/{id}` | 管理员 | 删除友链 |

### POST /friends 请求体

```json
{
  "name": "示例站点",
  "bio": "一个有趣的博客",
  "avatar": "https://example.com/avatar.png",
  "url": "https://example.com",
  "sort_order": 0
}
```

---

## 藏宝阁 (`/api/v1/treasures`)

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/treasures` | 公开 | 藏宝列表（可按分类筛选） |
| GET | `/treasures/categories` | 公开 | 分类列表 |
| POST | `/treasures` | 管理员 | 创建条目 |
| PUT | `/treasures/{id}` | 管理员 | 更新条目 |
| DELETE | `/treasures/{id}` | 管理员 | 删除条目 |

### GET /treasures 参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `category` | string | 分类筛选（如 `开源项目`、`工具`、`资源下载`） |

---

## 个人资料 (`/api/v1/profile`)

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/profile` | 公开 | 获取个人资料（含社交链接） |
| PUT | `/profile` | 管理员 | 更新个人资料 |
| POST | `/profile/social-links` | 管理员 | 添加社交链接 |
| DELETE | `/profile/social-links/{id}` | 管理员 | 删除社交链接 |

### GET /profile 响应

```json
{
  "name": "Starlit",
  "bio": "分享技术、生活和思考的个人博客",
  "avatar_url": "/uploads/images/avatar.jpg",
  "cover_url": "/uploads/images/cover.png",
  "social_links": [
    { "id": 1, "label": "GitHub", "icon": "github", "url": "https://github.com/xxx", "sort_order": 0 },
    { "id": 2, "label": "Bilibili", "icon": "bilibili", "url": "https://space.bilibili.com/xxx", "sort_order": 1 }
  ]
}
```

---

## 深夜酒馆 (`/api/v1/tavern`)

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/tavern` | 公开 | 可见留言列表 |
| POST | `/tavern` | 公开（匿名） | 发布留言（IP 限频 ≤3条/小时） |
| GET | `/tavern/all` | 管理员 | 全部留言（含隐藏的） |
| PUT | `/tavern/{id}/visibility` | 管理员 | 设置可见/隐藏 |
| DELETE | `/tavern/{id}` | 管理员 | 删除留言 |

### POST /tavern 请求体

```json
{
  "author": "晚归的人",
  "topic": "今天的小确幸",
  "body": "下班路上看到一只橘猫在路灯下打盹..."
}
```

### 限频规则

- 基于 IP 地址的 SHA256 哈希（不存明文）
- 同一 IP 每小时最多 3 条
- 超限返回 `429 Too Many Requests`

---

## 关于页 (`/api/v1/about`)

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/about/content` | 公开 | 获取 about.md 内容 |

---

## 用户管理 (`/api/v1/users`)

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/users` | 管理员 | 分页搜索用户 |
| GET | `/users/{id}` | 管理员 | 获取用户详情 |
| PUT | `/users/{id}` | 管理员 | 修改资料、管理员权限和启用状态 |
| POST | `/users/{id}/reset-password` | 管理员 | 重置密码并撤销旧会话 |
| POST | `/users/{id}/revoke-sessions` | 管理员 | 撤销全部刷新会话 |
| DELETE | `/users/{id}` | 管理员 | 删除用户 |

用户管理接口会防止删除当前账户、取消自己的管理员权限，以及清空最后一个可用管理员。

---

## 统计与内容统计 (`/api/v1/analytics`、`/api/v1/content-stats`)

| 模块 | 用途 |
|------|------|
| `/analytics` | 记录和查询公开访问、访客及访问趋势 |
| `/content-stats` | 为管理后台提供文章、说说、评论、图书等内容统计 |

前端路由在导航完成后自动记录公开页面访问，后台路由和认证页面不计入公开访问统计。

---

## 通用响应格式

### 列表响应

```json
{
  "items": [...],
  "total": 42
}
```

### 错误响应

```json
{
  "detail": "错误描述信息"
}
```

### HTTP 状态码

| 码 | 含义 |
|----|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 204 | 删除成功（无响应体） |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 409 | 冲突（如 slug 已存在） |
| 422 | 请求体验证失败 |
| 429 | 请求频率超限 |

---

## 静态文件访问

上传的文件通过以下路径访问：

```
GET /uploads/images/2026/07/abc_photo.jpg     — 图床图片
GET /uploads/images/backgrounds/dark-desktop-01.jpg — 背景图
GET /uploads/images/carousel/carousel-01.png   — 轮播图
GET /uploads/images/albums/album-01.png        — 相册图片
GET /uploads/images/book-covers/xxx_cover.jpg  — 图书封面
GET /uploads/books/xxx.epub                    — EPUB 文件
```
## 视频背景补充

管理员可通过 `POST /api/v1/backgrounds/video-upload` 上传视频，字段为
`multipart/form-data` 的 `file`。支持 MIME 与扩展名匹配的 `video/mp4`（`.mp4`）、
`video/webm`（`.webm`）和 `video/quicktime`（`.mov`）。接口返回的 URL 可用于创建
`media_type=video` 的背景。

后台也可以选择文件管理中的视频，使用 URL `/api/v1/files/{file_id}/media`。该公开媒体接口
只允许当前被视频背景引用的 `video/*` 文件；未引用返回 `404`，非视频返回 `415`。删除仍被
背景引用的文件返回 `409`，请先解除背景引用。
