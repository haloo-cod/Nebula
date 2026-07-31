# 数据库表结构

## 概述

后端使用 **SQLite** 数据库（`blog-backend/blog.db`），通过 SQLAlchemy 2.0 async ORM 操作。所有表模型定义在 `app/models/` 目录下。

数据库引擎配置位于 `app/database.py`，连接字符串：`sqlite+aiosqlite:///./blog.db`

## 公共字段（TimestampMixin）

以下字段自动添加到所有带 `TimestampMixin` 的表中：

| 字段 | 类型 | 说明 |
|------|------|------|
| `created_at` | DateTime(timezone) | 创建时间，自动填充 |
| `updated_at` | DateTime(timezone) | 更新时间，自动更新 |

---

## users — 用户

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK | — |
| `username` | String(100) | unique, index | 用户名 |
| `password_hash` | String(200) | — | bcrypt 哈希 |
| `is_admin` | Boolean | default=False | 是否管理员 |
| `email` | String(320) | unique, nullable | 邮箱 |
| `display_name` | String(100) | — | 显示名称 |
| `avatar_url` | String(500) | — | 头像 URL |
| `github_id` | String(100) | unique, nullable | GitHub 用户 ID |
| `email_verified` | Boolean | default=False | 邮箱是否已验证 |
| `is_active` | Boolean | default=True | 账户是否启用 |
| `last_login_at` | DateTime | nullable | 最近登录时间 |

管理员账户由 `.env` 中的 `ADMIN_USERNAME` 和 `ADMIN_PASSWORD` 配置；应用启动时如果不存在则创建。普通用户可通过注册接口创建。请不要在生产环境使用示例密码。

---

## auth_sessions — 刷新会话

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK | — |
| `user_id` | Integer | FK→users | 所属用户 |
| `token_hash` | String(64) | unique, index | 刷新令牌哈希，不保存明文令牌 |
| `expires_at` | DateTime | — | 到期时间 |
| `revoked_at` | DateTime | nullable | 撤销时间 |

刷新令牌通过 HttpOnly Cookie 传输；刷新时旧会话会被撤销并创建新的会话。

---

## posts — 博文

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK | — |
| `slug` | String(200) | unique, index | URL 标识 |
| `title` | String(300) | — | 标题 |
| `description` | Text | default="" | 摘要 |
| `category` | String(50) | default="" | 分类 |
| `tags` | JSON | default=[] | 标签数组 |
| `date` | String(20) | default="" | 发布日期（YYYY-MM-DD） |
| `cover_url` | String(500) | default="" | 封面图 URL |
| `content_md` | Text | default="" | Markdown 原文路径标识 |
| `content_html` | Text | default="" | 预渲染 HTML 缓存 |
| `draft` | Boolean | default=False | 是否草稿 |

---

## books — 图书

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK | — |
| `slug` | String(200) | unique, index | URL 标识 |
| `title` | String(300) | — | 书名 |
| `author` | String(200) | default="" | 作者 |
| `description` | Text | default="" | 简介 |
| `cover_url` | String(500) | default="" | 封面图 URL |
| `file_path` | String(500) | default="" | EPUB 文件路径 |

---

## gallery_projects — 展览项目

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK | — |
| `slug` | String(200) | unique, index | URL 标识 |
| `title` | String(300) | — | 项目名 |
| `description` | Text | default="" | 简介 |
| `tags` | JSON | default=[] | 标签数组 |
| `status` | String(50) | default="" | 状态（进行中/已完成等） |
| `year` | String(10) | default="" | 年份 |
| `is_featured` | Boolean | default=False | 是否精选 |
| `content_md` | Text | default="" | Markdown 原文 |
| `content_html` | Text | default="" | 预渲染 HTML |

---

## uploaded_images — 图床图片

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK | — |
| `filename` | String(300) | unique | 相对路径（如 `images/2026/07/abc.jpg`） |
| `original_name` | String(300) | — | 原始文件名 |
| `url` | String(500) | — | 访问 URL（如 `/uploads/images/...`） |
| `file_size` | Integer | default=0 | 文件大小（bytes） |
| `width` | Integer | default=0 | 图片宽度 |
| `height` | Integer | default=0 | 图片高度 |
| `mime_type` | String(50) | default="" | MIME 类型 |

---

## backgrounds — 背景图

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK | — |
| `image_id` | Integer | FK→uploaded_images | 关联图片 |
| `theme` | String(10) | — | `'dark'` 或 `'light'` |
| `device` | String(10) | — | `'desktop'` 或 `'mobile'` |
| `sort_order` | Integer | default=0 | 排序 |

---

## carousel_slides — 首页轮播

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK | — |
| `image_id` | Integer | FK→uploaded_images | 关联图片 |
| `sort_order` | Integer | default=0 | 排序 |

---

## albums — 相册

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK | — |
| `title` | String(200) | — | 相册标题 |
| `description` | Text | default="" | 相册描述 |
| `orientation` | String(20) | default="portrait" | 方向：`portrait` / `landscape` |
| `cover_image_id` | Integer | FK→uploaded_images, nullable | 手动指定封面（null 则取第一张） |

---

## album_photos — 相册照片

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK | — |
| `album_id` | Integer | FK→albums (CASCADE) | 所属相册 |
| `image_id` | Integer | FK→uploaded_images | 关联图片 |
| `caption` | Text | nullable | 照片说明 |
| `sort_order` | Integer | default=0 | 排序 |

---

## friends — 友链

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK | — |
| `name` | String(100) | — | 站点名称 |
| `bio` | Text | default="" | 简介 |
| `avatar` | String(500) | default="" | 头像 URL |
| `url` | String(500) | — | 站点地址 |
| `sort_order` | Integer | default=0 | 排序 |

---

## treasures — 藏宝阁

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK | — |
| `slug` | String(200) | unique, index | 唯一标识 |
| `title` | String(200) | — | 名称 |
| `description` | Text | default="" | 描述 |
| `category` | String(50) | — | 分类（开源项目/工具/资源下载） |
| `icon` | String(100) | default="" | 图标（emoji） |
| `url` | String(500) | default="" | 外链地址 |
| `download_file` | String(500) | default="" | 下载文件路径/链接 |
| `tags` | JSON | default=[] | 标签数组 |
| `sort_order` | Integer | default=0 | 排序 |

---

## tavern_posts — 深夜酒馆留言

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK | — |
| `author` | String(100) | — | 匿名署名 |
| `topic` | String(200) | — | 话题/标题 |
| `body` | Text | — | 正文（不限字数） |
| `ip_hash` | String(64) | default="" | IP 的 SHA256（限频用，不存明文） |
| `is_visible` | Boolean | default=True | 是否可见（管理员可隐藏） |

---

## profile — 个人资料（singleton）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK（固定为 1） | — |
| `name` | String(100) | default="" | 昵称 |
| `bio_md` | Text | default="" | 个人简介（Markdown） |
| `bio_html` | Text | default="" | 简介预渲染 HTML |
| `avatar_url` | String(500) | default="" | 头像 URL |
| `cover_url` | String(500) | default="" | 封面图 URL |

---

## social_links — 社交链接

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK | — |
| `label` | String(50) | — | 平台名称（如 GitHub） |
| `icon` | String(50) | — | 图标标识（对应前端 SvgIcon name） |
| `url` | String(500) | — | 链接地址 |
| `sort_order` | Integer | default=0 | 排序 |

---

## study_todos — 自习室待办（预留）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK | — |
| `title` | String(200) | — | 任务名 |
| `duration_minutes` | Integer | default=25 | 专注时长 |
| `break_minutes` | Integer | default=5 | 休息时长 |
| `completed_pomodoros` | Integer | default=0 | 累计完成数 |
| `is_completed` | Boolean | default=False | 是否完成 |

> 注：自习室当前使用 localStorage，此表为未来跨设备同步预留。

---

## study_schedule — 自习室日程（预留）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK | — |
| `title` | String(200) | — | 日程标题 |
| `start_time` | String(10) | — | 开始时间（HH:MM） |
| `end_time` | String(10) | — | 结束时间（HH:MM） |
| `is_completed` | Boolean | default=False | 是否完成 |

---

## study_history — 自习室历史（预留）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK | — |
| `date` | String(10) | — | 日期（YYYY-MM-DD） |
| `completed_pomodoros` | Integer | default=0 | 当日完成番茄数 |
| `total_focus_minutes` | Integer | default=0 | 当日专注总时长 |

---

## site_config — 站点配置

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK | — |
| `key` | String(100) | unique | 配置键 |
| `value` | Text | default="" | 配置值（JSON 或纯文本） |

当前由管理后台提供配置编辑入口，具体配置项以接口和实现为准。

---

## analytics_events — 访问统计事件

用于记录公开页面访问和相关请求元数据。原始 IP 不作为长期业务数据使用，系统会按配置的保留周期清理统计明细。

---

## rate_limit_hits — 限流记录

用于注册、登录、深夜酒馆留言等操作的频率限制。IP 等信息以哈希形式保存，并在过期后清理。

---

## JSON 文件存储

以下数据使用 JSON 文件存储（`blog-backend/data/` 目录），通过 `filelock` 保证并发安全：

### `data/moments.json` — 说说

```json
[
  {
    "id": 1,
    "date": "2026-07-10T13:37:15",
    "content": "今天天气真好...",
    "mood": "开心",
    "tags": ["日常"],
    "images": ["/uploads/images/moments/photo1.jpg"],
    "likes": 5,
    "comments": [
      { "id": 1, "author": "访客", "content": "赞！", "date": "..." }
    ]
  }
]
```

### `data/comments.json` — 通用评论

```json
{
  "post:hello-world": [
    { "id": 1, "author": "访客", "content": "好文！", "date": "...", "parent_id": null }
  ],
  "about": [...]
}
```

---

## ER 关系图（简化）

```
uploaded_images ←── backgrounds (image_id)
                ←── carousel_slides (image_id)
                ←── album_photos (image_id)
                ←── albums (cover_image_id, nullable)

albums ←── album_photos (album_id, CASCADE)
```

其他表之间无外键关系，均为独立实体。
