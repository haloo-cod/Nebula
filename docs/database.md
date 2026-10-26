# 数据库表结构

## 概述

后端默认使用 **SQLite** 数据库（`blog-backend/blog.db`），通过 SQLAlchemy 2.0 async ORM 操作。所有表模型定义在 `app/models/` 目录下。

数据库引擎配置位于 `app/database.py`，连接字符串来自 `DATABASE_URL`，默认 `sqlite+aiosqlite:///./blog.db`，可在 `.env` 中覆盖。数据库是业务数据的唯一权威来源；`data/` 下的 `friends.json` 只是生成副本，评论、友链申请和正式友链均不以 JSON 为准。

生产更新应先停写和备份，在 `blog-backend/` 工作目录用服务用户运行 `.venv/bin/python -m scripts.migrate`，成功后再启动 worker；服务 Python 链接的 SQLite 需至少为 3.35。命令使用同一份 `.env` 和数据库引擎，只校验生产配置并迁移结构，不创建管理员、清理资源或写 JSON。停机、一致性备份与回滚步骤见[生产更新流程](production-update.md)。

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
| `id` | Integer | PK | 业务主键；既有 ID、关联和 API 整数 ID 保持不变 |
| `auth_id` | String(36) | unique, index, NOT NULL | 服务端生成的规范 UUID4 认证主体，应用中不可变 |
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

用户访问 JWT 和用户邮箱验证令牌以 `auth_id` 为主体，禁止回退到整数 ID 或用户名；OAuth state 的非用户主体及令牌类型不变。用户名、邮箱、密码和 GitHub 资料变动不改变 `auth_id`，删除后创建的账户获得新 UUID，即使整数 ID 被复用也不会继承旧令牌的身份。`auth_id` 是认证内部字段，不新增到公开 `UserResponse` 或管理用户资料响应。

---

## auth_sessions — 刷新会话

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK | — |
| `user_id` | Integer | FK→users | 所属用户 |
| `auth_id` | String(36) | NOT NULL | 会话签发时冻结的所属账户 UUID，不随整数 ID 复用而改变 |
| `token_hash` | String(64) | unique, index | 刷新令牌哈希，不保存明文令牌 |
| `expires_at` | DateTime | — | 到期时间 |
| `revoked_at` | DateTime | nullable | 撤销时间 |

刷新令牌通过 HttpOnly Cookie 传输；刷新时旧会话会被撤销并创建新的会话。除检查到期和撤销状态外，还校验 UUID 格式、当前用户仍启用，并要求会话 `auth_id` 与当前 `users.auth_id` 相等；仅有相同 `user_id` 不足以恢复会话。

---

## schema_migrations — 迁移版本

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `version` | String(100) | PK | 已提交的迁移版本，如 `20261023_auth_identity_uuid` |
| `applied_at` | DateTime | default=数据库当前时间 | 迁移完成时间 |

`migrate_existing_schema(engine)` 在同一文件锁内完成建表和升级，SQLite 使用 `BEGIN IMMEDIATE` 保护整个事务；多个 worker 首次启动会串行检查及迁移。CLI 与应用启动共用此入口，生产仍应在 worker 启动前运行 CLI。

`20261023_auth_identity_uuid` 在同一事务内补齐缺失字段，仅为空或缺失的用户认证主体生成 UUID，然后一次性撤销尚未撤销的旧刷新会话并记录版本。旧会话新增的 `auth_id` 保持空值；整数 ID 可能已复用，不能据此把历史会话归属到当前用户，也不回填 UUID。已有非空会话 `auth_id`、`revoked_at` 时间、用户原有字段、整数 ID 和关联保持原值。版本存在后不再执行这次会话撤销；重复迁移保留 UUID，迁移后新建的会话仍有效。

旧表加列遵循轻量迁移约定，使用 `VARCHAR(36) NOT NULL DEFAULT ''`，用户 UUID 在同一事务中回填并建唯一索引；旧会话可保留空值并已撤销。新建用户和新会话始终由应用提供有效 UUID；空值及非规范 UUID 不能用于认证。此次切换要求所有账户重新登录一次；整数／用户名主体的旧 JWT 和邮箱验证链接失效，不提供兼容回退。已验证邮箱状态不变，需要使用旧验证链接的用户应重新发信。

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

## comments — 页面评论

评论保存在 SQLite，不再使用 `data/comments.json`。读取公开，发表和删除需要登录账户。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK | — |
| `page_key` | String(300) | index | 页面标识，如 `post:slug`、`about`、`friend-application:12` |
| `user_id` | Integer | FK→users (SET NULL), index, nullable | 作者；账户删除后置空 |
| `parent_id` | Integer | FK→comments (CASCADE), index, nullable | 父评论；递归形成评论树 |
| `content` | Text | — | 正文，去除首尾空白后 1–2000 字符 |
| `legacy_author` | String(100) | default="" | 历史匿名评论署名，仅用于只读展示 |
| `legacy_avatar_color` | String(20) | default="" | 历史匿名评论头像颜色 |

- `page_key` 去除首尾空白后必须为 1–300 字符；`post:{slug}`、`about` 等普通页面直接按字符串存取。
- `friend-application:{id}` 的可见性不存为字段，而由申请状态派生：只有 `approved` 且 `friend_id` 仍关联正式友链时才允许读取和发表。申请或友链删除后，该键的评论被永久删除，接口返回 `404`。
- 同一 IP 每小时最多创建 20 条评论，记录在 `rate_limit_hits`。发表时 `parent_id` 必须属于同一 `page_key`，否则返回 `400`。
- 删除评论会按 `parent_id` 递归删除全部后代；外键同时使用 `ON DELETE CASCADE`。删除友链申请或正式友链会删除该申请的整段讨论，没有回收站或保留期。

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
| `source_text` | String(120) | NOT NULL, default='' | 背景来源文字，空值隐藏来源牌 |
| `source_url` | String(2048) | NOT NULL, default='' | 可选完整 HTTP(S) 外链 |
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

## friends — 正式友链

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK | — |
| `name` | String(100) | — | 站点名称 |
| `bio` | Text | default="" | 简介 |
| `avatar` | String(500) | default="" | 头像 URL |
| `url` | String(500) | — | 站点地址 |
| `rss_url` | String(2048) | default="", server_default="" | 订阅地址；空值表示未提供 |
| `sort_order` | Integer | default=0 | 排序 |

`rss_url` 是后续版本新增的列。独立 CLI 和应用启动共用的 `migrate_existing_schema()` 检查 `friends` 表，字段缺失时执行一次幂等迁移：

```sql
ALTER TABLE friends ADD COLUMN rss_url VARCHAR(2048) NOT NULL DEFAULT '';
```

旧数据因此得到空字符串，无需手工改库。创建或编辑友链时，`rss_url` 只接受空值或最长 2048 字符、无空白／无凭据的完整 HTTP／HTTPS 地址；公开列表、写入响应和 `friends.json` 均包含该字段。

---

## friend_applications — 友链申请

申请与正式友链分离：申请中的邮箱和审核信息留在本表，只有通过后才生成 `friends` 记录。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK | — |
| `user_id` | Integer | FK→users (SET NULL), index, nullable | 提交账户；账户删除后置空，申请保留 |
| `name` | String(100) | — | 站点名称 |
| `url` | String(500) | — | 站点地址 |
| `avatar` | String(500) | — | 头像 URL |
| `email` | String(320) | — | 私有联络邮箱，绝不进入公开响应或 JSON 副本 |
| `rss_url` | String(2048) | default="", server_default="" | 申请时填写的订阅地址 |
| `status` | String(16) | default="pending", server_default="pending", index | `pending` / `approved` / `rejected` |
| `friend_id` | Integer | FK→friends (CASCADE), unique, nullable | 通过后生成的正式友链 |
| `active_site_key` | String(2048) | unique, nullable | 待审核／已通过站点的规范化键，用于去重 |
| `review_note` | Text | default="", server_default="" | 拒绝原因；通过时为空 |
| `reviewed_at` | DateTime(timezone) | nullable | 审核时间 |

约束与状态转换：

- `CHECK (status IN ('pending', 'approved', 'rejected'))`；`friend_id` 和 `active_site_key` 都是唯一约束（允许 `NULL`）。`active_site_key` 由完整 URL 规范化（保留路径、查询参数，去掉片段）得到。
- `pending → approved`：同一事务创建 `friends` 记录（`bio` 为空，`sort_order` 为当前最大值 + 1），写入 `friend_id`、`reviewed_at`，清空 `review_note`；站点键保留。
- `pending → rejected`：`review_note` 必须为非空且不超过 500 字符，`reviewed_at` 写入时间，`active_site_key` 置 `NULL`，使同站点可重新申请。
- `approved`／`rejected` 为终态。对已通过申请重复执行“通过”是幂等的，不会新建友链；其余重复或反向审核返回 `409`。
- 提交时若站点已在正式友链，或已有同站点待审核／已通过申请，返回 `409`。删除申请会删除其 `friend-application:{id}` 讨论；已通过申请还会一并删除正式友链。删除正式友链同样会级联清理关联申请及讨论。
- 公开申请只来自 `approved` 且 `friend_id` 指向仍存在友链的行；`email`、`user_id`、`status`、`review_note` 仅本人和管理员可见。

SQLite 的申请主键使用 `AUTOINCREMENT`，删除最高 ID 后也不会重用旧申请的讨论地址。结构迁移会在同一事务内升级未启用该约束的申请表，完整保留现有 ID、邮箱、审核、时间和友链关联，并恢复索引；不会重建正式 `friends` 表。

提交申请与删除账户按“账户 → 申请”的顺序取得写锁。提交时重新核对不可变的认证 UUID 与账户启用状态，防止账户删除、整数 ID 复用或账户禁用后仍把私有申请挂到旧 ID。

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

`friends_exchange_info` 使用 JSON 保存本站交换友链信息：`name`、`url`、`avatar`、`bio`、`requirements`、`contact` 和 `rss_url`。`rss_url` 默认空字符串，旧 JSON 缺少字段时由接口补默认值；空值让前台使用本站 `/api/v1/rss.xml`，自定义值须为不超过 2048 字符的完整 HTTP／HTTPS 地址。该配置复用现有 JSON，无需新增列；正式友链表自身的 `rss_url` 列迁移见上方 `friends` 表。

---

## analytics_events — 访问统计事件

用于记录公开页面访问和相关请求元数据。原始 IP 不作为长期业务数据使用，系统会按配置的保留周期清理统计明细。

---

## rate_limit_hits — 限流记录

用于注册、登录、深夜酒馆留言等操作的频率限制。IP 等信息以哈希形式保存，并在过期后清理。

---

## JSON 文件存储

`DATA_DIR` 由 `app/config.py` 的 `Settings` 提供，可由同名环境变量覆盖，默认是 `blog-backend/data`。应用启动时确保目录存在。该目录没有静态挂载，文件不通过 `/uploads` 或其他 HTTP 路由提供。

### `data/moments.json` — 说说

说说仍以 JSON 数组保存，通过 `filelock` 串行读写。其中的 `comments` 是说说自身的附属数据，与通用 `comments` 表无关：

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

### `data/friends.json` — 正式友链生成副本

- 仅由数据库列表生成，字段为 `id`、`name`、`bio`、`avatar`、`url`、`rss_url`、`sort_order`、`created_at`；不包含申请邮箱或其他私有信息。
- 数据库是唯一权威来源；启动时以及正式友链新增、修改、删除、申请通过、已通过申请删除后重建。后端从不读取该文件，也不做反向导入，手工修改会在下次同步时被覆盖。
- 同步在 `friends.json.lock` 锁内用新的数据库会话读取已提交数据，先写同目录的隐藏临时文件，再用原子替换覆盖 `friends.json`；失败保留旧文件。数据库提交和文件同步不是同一事务：提交成功而写入失败时接口返回 `503 FRIEND_JSON_SYNC_FAILED`；重试入口是 `POST /api/v1/friends/sync-json`，它只重建文件、不重复业务写库。
- 可通过 `DATA_DIR` 将副本放到部署需要的目录；无需修改代码。

### `data/comments.json` — 已废弃

旧版本的通用评论 JSON 不再是运行时数据源，后端不读取、不写入该文件。评论以 SQLite `comments` 表为准；如旧文件仍存在，只应作为历史备份处理，不能用于恢复当前评论。

---

## ER 关系图（简化）

```
users ←── auth_sessions (user_id)
      ←── comments (user_id, SET NULL)
      ←── friend_applications (user_id, SET NULL)

comments ←── comments (parent_id, CASCADE)
comments.page_key ── (逻辑关联) ── friend_applications.id（仅 approved 可见）

friends ←── friend_applications (friend_id, CASCADE, unique)

uploaded_images ←── backgrounds (image_id)
                ←── carousel_slides (image_id)
                ←── album_photos (image_id)
                ←── albums (cover_image_id, nullable)

albums ←── album_photos (album_id, CASCADE)
```

`comments.page_key` 与友链申请之间是字符串逻辑关联，没有数据库外键；可见性由 `friend_applications.status` 和 `friend_id` 在查询时校验。其他表之间无外键关系，均为独立实体。
