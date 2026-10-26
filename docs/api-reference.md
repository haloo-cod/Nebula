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

用户访问 JWT 的 `sub` 和用户邮箱验证令牌的主体均为服务端生成、不可变的规范 UUID `users.auth_id`；签名、令牌类型和 UUID 格式都必须有效，整数 ID／用户名主体不再作为用户身份接受，也不做兼容查询。登录仍使用用户名或邮箱；`/auth/me` 等用户资料响应与管理接口继续使用整数 `id`，不新增 `auth_id` 字段。OAuth state 使用原有的非用户主体及独立令牌类型。

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

注册及管理员重置的新密码至少为 8 个 Unicode 字符，UTF-8 编码后最多 72 字节；超过边界返回 `422`。登录输入超过 72 字节按凭据错误返回 `401`，不会截断密码或返回服务器异常。

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

浏览器请求需要携带 Cookie。刷新接口会轮换旧会话，退出接口会撤销当前刷新会话并清除 Cookie。刷新时会检查过期、撤销状态和账户启用状态，并要求会话中冻结的 `auth_id` 为有效 UUID、与当前账户一致；整数 `user_id` 相同不能恢复其他身份的会话。

部署 UUID 认证切换时，迁移会一次性撤销旧刷新会话，所有用户（包括管理员）需要重新登录一次。旧整数／用户名主体访问令牌在需要登录的接口返回 `401`；旧邮箱验证链接失效，应重新发送验证邮件。用户资料、邮箱验证状态、业务整数 ID 和关联保留。重复运行迁移不会更换 UUID 或再次撤销新会话；`schema_migrations` 中的 `20261023_auth_identity_uuid` 是内部版本记录，不属于 API 响应字段。操作步骤见[生产更新流程](production-update.md)。

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

GitHub 已绑定的账户和新建 OAuth 账户仍写入 Refresh Cookie，并跳转到前端 `/auth/callback`。GitHub 的已验证主邮箱命中已有密码账户时，不自动合并身份、不建立会话；回调跳转到 `/auth/link-github?token=...&redirect=...`，要求输入现有账户密码。已有无密码 OAuth 账户保留按邮箱绑定行为。OAuth state 包含随机 nonce，绑定令牌有效期为 10 分钟，不能作为 Bearer 登录令牌使用。

```http
POST /api/v1/auth/github/confirm-link
Content-Type: application/json

{"link_token": "<callback token>", "password": "<existing account password>"}
```

确认成功返回与密码登录相同的 `TokenResponse` 并设置 Refresh Cookie。密码错误、无效或过期令牌返回 `401`；账户已绑定、重复/并发确认或 GitHub 身份已被其他账户绑定返回 `409`。只有当前邮箱仍匹配 GitHub 的已验证邮箱时才补充邮箱验证状态；绑定页不记录访问统计，避免令牌写入统计 URL。过期后需重新使用 GitHub 登录。

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
| `page_size` | int | 12 | 每页条数（1-500） |
| `category` | string | — | 分类筛选 |

列表在分页前依次按置顶状态、发布日期、创建时间、ID 倒序排列。发布日期按年、月、日的数值比较，兼容历史 `YYYY-M-D` 和标准 `YYYY-MM-DD` 格式；同一天新创建的文章优先。

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

评论保存在 SQLite 的 `comments` 表，不再读写 `data/comments.json`；读取匿名可用，发表和删除需要登录。

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/comments?page_key=xxx` | 公开 | 获取主评论及扁平回复（按创建时间、ID 升序） |
| GET | `/comments/count?page_key=xxx` | 公开 | 获取单页评论数 |
| POST | `/comments/batch-count` | 公开 | 批量获取多个页面的评论数 |
| POST | `/comments` | 已登录用户 | 发表评论或回复 |
| DELETE | `/comments/{id}` | 评论本人或管理员 | 删除评论及其全部回复 |

评论响应固定为“主评论 → 回复列表”两层：所有后代均归入对应主评论的 `children`，回复本身的 `children` 为空。每条回复包含原始 `parent_id` 和 `reply_to_author`，用于表示真正回复的对象；不修改数据库中的父子关系。历史孤立评论作为主评论展示，异常循环也不会阻断读取。前台评论区与后台友链讨论默认显示每个主评论的前三条回复，更多回复支持展开、收起；发布回复后自动展开所在讨论串。

### page_key 约定

| 场景 | page_key 格式 |
|------|--------------|
| 博文评论 | `post:hello-world` |
| 关于页评论 | `about` |
| 已通过友链申请的讨论 | `friend-application:{申请ID}` |
| 其他页面 | 自定义字符串，去除首尾空白后 1–300 字符 |

`friend-application:{id}` 只对 `approved` 且仍关联正式友链的申请开放：列表、计数和发表接口在申请不存在、未通过或正式友链已删除时返回 `404`；批量计数把这类键记作 `0`，不抛错。删除申请或正式友链会永久删除对应讨论。历史匿名评论以 `legacy_author` 保留只读展示，作者显示为“已注销用户”时不可再登录编辑。

### POST /comments 请求体

```json
{
  "page_key": "post:hello-world",
  "content": "写得好！",
  "parent_id": null
}
```

- `content` 去除首尾空白后必须为 1–2000 字符，`page_key` 不能为空。
- `parent_id` 必须是同一 `page_key` 下已存在的评论，否则返回 `400`。
- 同一 IP 每小时最多创建 20 条评论，超限返回 `429`；启用邮箱验证且账户邮箱未验证时返回 `403`。
- 友链申请讨论先写入并提交限频记录，再锁定对应申请行并复查公开状态；申请删除也锁定同一行，因此评论写入与申请删除串行，避免评论落到刚刚删除的申请上。
- 删除评论会一并删除其全部后代回复，遍历具有循环保护；删除申请或正式友链会删除该申请的整段讨论。响应分别为 `201`（新评论）和 `204`（删除）。

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
| GET | `/images` | 管理员 | 图片列表（分页、全库文件名搜索、存储后端筛选） |
| DELETE | `/images/{id}` | 管理员 | 删除图片 |

`GET /images` 接收 `page`、`page_size`（1–100）、可选 `storage_backend` 以及 `keyword`（最多 300 字符）。关键词按原文件名或内部文件名进行不区分大小写的字面子串匹配，分页列表与 `total` 使用相同过滤条件，按创建时间及 ID 降序返回。

删除正在被轮播、相册、图书封面、文章封面、背景或视频封面引用的图片返回 `409`，响应包含引用原因，文件和记录保留。

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

## 后台目录浏览 (`/api/v1/storage`)

`GET /api/v1/storage/browse` 仅管理员可用。按目录合并本地文件与数据库中已登记的 R2 对象，
保留只有 R2 对象或只有数据库记录的文件，并合并迁移后仍存在的本地副本；不读取文件正文、
不列举整个 R2 存储桶，也不修改存储记录或磁盘文件。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `root` | `uploads` | 只允许 `uploads`、`content`，对应后端配置的业务根目录 |
| `path` | 空字符串 | 根目录内相对路径，例如 `images/2026/10`，最多 2048 字符 |
| `page` | `1` | 文件页码，从 1 开始 |
| `page_size` | `100` | 每页文件数，1–200；子目录始终完整返回 |

响应包含 `root`、`path`、`directories`、`items`、`total`、`page`、`page_size`、`r2_enabled`。
每个文件条目包含 `name`、`path`、`title`、`file_size`、`modified_at`、`local_exists`、
`storage_backend`、`record_kind`、`record_id`、`r2_key`、`r2_url`、`url`、`manage_url`。
未登记文件的关联字段为空；没有本地副本时，时间使用登记时间，大小可能未知。
R2 标签表示数据库中的存储配置，不执行远程对象存在性检查。

目录涵盖上传图片、普通文件、EPUB、背景自有视频、图书 / 文章 ZIP，以及 Markdown 原文件。
背景引用的图片和文件库视频仍归其原目录，不重复生成文件。隐藏路径、绝对路径、`..`、
符号链接和越出根目录的路径不允许浏览；未知目录返回 `404`。

后台入口为 `/admin/files`，默认显示左侧目录树与右侧文件列表。文件行可展开查看对象键和地址；
“管理”跳到现有业务页面，“文件库”保留原有上传、下载、删除及归档任务操作。

---

## 背景图 (`/api/v1/backgrounds`)

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/backgrounds` | 公开 | 背景图列表（可按 theme/device 筛选） |
| POST | `/backgrounds` | 管理员 | 添加背景图 |
| PATCH | `/backgrounds/{id}/source` | 管理员 | 修改或清空背景来源 |
| DELETE | `/backgrounds/{id}` | 管理员 | 删除背景图 |
| PUT | `/backgrounds/reorder` | 管理员 | 调整排序 |

### GET /backgrounds 参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `theme` | string | `dark` 或 `light` |
| `device` | string | `desktop` 或 `mobile` |

创建背景时可传 `source_text`（最多 120 字符）和 `source_url`（最多 2048 字符），缺省为空。
列表、创建和编辑响应均返回这两个字段。字段首尾空白会去除，非空链接必须是完整 HTTP/HTTPS 地址。

`PATCH /backgrounds/{id}/source` 必须同时提交 `{ "source_text": "画师 · 作品", "source_url": "https://example.com/work" }`。
空字符串可清空字段；成功返回背景记录，不存在返回 `404`，字段校验失败返回 `422`，未登录／非管理员返回 `401`／`403`。

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
| GET | `/friends` | 公开 | 正式友链列表（按 `sort_order`、`id` 升序） |
| GET | `/friends/exchange-info` | 公开 | 本站交换友链信息及 RSS 地址配置 |
| PUT | `/friends/exchange-info` | 管理员 | 保存本站交换友链信息及 RSS 地址配置 |
| POST | `/friends` | 管理员 | 添加正式友链 |
| PUT | `/friends/{id}` | 管理员 | 更新正式友链 |
| DELETE | `/friends/{id}` | 管理员 | 删除正式友链，并清理关联申请与讨论 |
| POST | `/friends/applications` | 已登录用户 | 提交友链申请（待审核，不直接公开） |
| GET | `/friends/applications` | 公开 | 已通过且仍关联正式友链的申请 |
| GET | `/friends/applications/mine` | 已登录用户 | 当前账户的申请历史（含私有字段） |
| GET | `/friends/applications/admin` | 管理员 | 全部申请，可按状态筛选 |
| PATCH | `/friends/applications/{id}/review` | 管理员 | 通过或拒绝申请 |
| DELETE | `/friends/applications/{id}` | 管理员 | 删除申请；已通过时同时删除正式友链与讨论 |
| POST | `/friends/sync-json` | 管理员 | 仅重建 `friends.json` 副本，不写数据库 |

### POST /friends 请求体

```json
{
  "name": "示例站点",
  "bio": "一个有趣的博客",
  "avatar": "https://example.com/avatar.png",
  "url": "https://example.com",
  "rss_url": "https://example.com/rss.xml",
  "sort_order": 0
}
```

`name`、`url` 必填；`rss_url` 可为空或最长 2048 字符的完整 HTTP／HTTPS 地址。列表和写入响应都包含 `rss_url` 与 `created_at`。编辑友链时可只提交要修改的字段；`rss_url: ""` 会清空订阅地址。

### 友链申请

提交体只包含站点与联络字段，未知字段返回 `422`：

```json
{
  "name": "星尘小站",
  "url": "https://example.com",
  "avatar": "https://example.com/avatar.png",
  "email": "owner@example.com",
  "rss_url": ""
}
```

- `name` 1–100 字符；`url`、`avatar` 为 1–500 字符的完整 HTTP／HTTPS 地址；`email` 最长 320 字符；`rss_url` 为空或最长 2048 字符的完整 HTTP／HTTPS 地址；字段首尾空白会去除。
- 上述地址不能包含空白或 URL 凭据（用户名／密码）。
- 提交成功返回 `201` 的私有申请。`email` 只在本人和管理员接口出现，公开接口不返回。
- 提交时站点不得与正式友链重复，也不得有同站点待审核／已通过申请：前者返回 `409`，后者由唯一约束返回 `409`。被拒绝后站点键释放，可重新申请。
- 同一站点由 `active_site_key` 唯一约束保证在待审核／已通过阶段不可重复。

公开分页 `GET /friends/applications`：`page` 默认 1，`page_size` 默认 10（1–50），按 `reviewed_at`、`id` 倒序；响应为 `{ "items": [...], "total": n }`。每项仅含 `id`、`name`、`url`、`avatar`、`rss_url`、`created_at`、`reviewed_at`、`friend_id`，不包含 `email`、`user_id`、`status`、`review_note`。

`GET /friends/applications/mine` 同样分页，只返回当前账户的申请，按 `created_at`、`id` 倒序；`GET /friends/applications/admin` 默认 `page_size=20`（1–100），可用 `status=pending|approved|rejected` 筛选，列表同样按 `created_at`、`id` 倒序。私有项包含：

```json
{
  "id": 12,
  "name": "星尘小站",
  "url": "https://example.com",
  "avatar": "https://example.com/avatar.png",
  "rss_url": "",
  "created_at": "2026-10-20T08:00:00Z",
  "reviewed_at": null,
  "friend_id": null,
  "email": "owner@example.com",
  "user_id": 3,
  "status": "pending",
  "review_note": ""
}
```

`user_id` 在账户删除后为 `null`，申请和审核记录保留；显示为“已注销用户”。公开列表只包含 `approved` 且 `friend_id` 仍指向存在友链的记录，友链删除后该申请不再公开。

### 审核、幂等与冲突

`PATCH /friends/applications/{id}/review` 请求体：

```json
{ "decision": "approved", "reason": "" }
```

- 仅 `pending` 可转换。通过时在同一事务内用申请的 `name`、`url`、`avatar`、`rss_url` 创建正式友链（`bio` 为空、`sort_order` 取当前最大值 + 1），并写入 `status=approved`、`friend_id`、`reviewed_at`；正式友链与公开申请同时生效。
- 拒绝时 `reason` 去除首尾空白后必须为 1–500 字符，写入 `review_note`，状态变为 `rejected` 并释放站点键；通过时忽略并清空 `reason`。
- 已 `approved` 的申请再次提交 `approved` 是幂等的：不重复创建友链，返回现有记录和 `200`。
- 已拒绝的申请再次审核、已通过申请改为拒绝、或并发审核已被处理时返回 `409`（“申请已处理，请刷新列表”）。
- 申请不存在返回 `404`；通过时站点已在正式友链中也返回 `409`。
- 删除申请返回 `204`。`approved` 申请会同时删除关联正式友链、公开申请及 `friend-application:{id}` 全部讨论；`pending`／`rejected` 只删除申请与其讨论。操作先锁定申请行，避免与评论写入交错。
- 申请 ID 删除后不会复用；旧审核操作与旧讨论地址继续返回 `404`，不会指向后续申请。
- 通过 `PUT /friends/{id}` 编辑由申请生成的友链时，`name`、`url`、`avatar`、`rss_url` 会同步回关联申请并重新校验站点唯一性，重复站点返回 `409`、字段校验失败返回 `422`；`DELETE /friends/{id}` 会删除关联申请和讨论。

### friends.json 公开副本

数据库是唯一权威数据源；`friends.json` 只是正式友链的生成副本，后端从不读取或反向导入它。每次新增、修改、删除正式友链、通过申请或删除已通过申请，都在数据库提交后重建副本；提交申请、拒绝申请和删除未通过申请不触发同步。

- 路径为 `DATA_DIR/friends.json`。`DATA_DIR` 可由环境变量覆盖，默认 `blog-backend/data`。
- 同步使用 `friends.json.lock` 串行化，在新数据库会话中读取已提交列表，写入同目录临时文件后用原子替换覆盖目标，失败时保留旧文件。
- 副本字段与公开友链响应一致，不包含申请邮箱或其他私有联络信息。
- 数据库提交成功但文件同步失败时，接口返回 `503`，`detail` 为 `FRIEND_JSON_SYNC_FAILED`；数据库结果已保留，不可回滚。客户端应保留成功状态并调用 `POST /friends/sync-json` 仅重试文件同步；后续正式友链写操作也会再次重建副本，但不应通过重复业务写操作来修复。
- `POST /friends/sync-json` 成功返回 `204`，失败同样返回 `503` 和 `FRIEND_JSON_SYNC_FAILED`。
- `data/` 未挂载为静态目录，`friends.json` 不通过 HTTP 对外提供。

### 交换友链信息中的 RSS 配置

GET／PUT `/api/v1/friends/exchange-info` 在原有 `name`、`url`、`avatar`、`bio`、`requirements`、`contact` 字段外增加 `rss_url: string`，默认 `""`。PUT 仍提交完整交换信息；地址会移除首尾空白，只允许空值或最长 2048 字符的完整 HTTP／HTTPS 地址。

空值表示前台使用现有 API 基址下的 `/api/v1/rss.xml`，同域部署会补全当前站点来源。后台填写自定义地址后，友链页和首页图标共同使用该地址；清空恢复本站默认值。地址配置只控制两个可见入口，本站 RSS 接口和静态自动发现标签始终可用。

配置仍存储在 `site_config` 的 `friends_exchange_info` JSON 中；旧 JSON 缺少 `rss_url` 时读取为空，该配置本身无需数据库结构迁移（正式友链的 `friends.rss_url` 列迁移见数据库文档）。

---

## RSS 订阅 (`/api/v1/rss.xml`)

`GET /api/v1/rss.xml` 无需认证，返回 UTF-8 RSS 2.0 XML，`Content-Type: application/rss+xml; charset=utf-8`，`Cache-Control: public, max-age=300`。

- 返回最近 20 篇已发布博文；按实际发布日期、创建时间、ID 倒序，置顶不影响订阅顺序，草稿始终排除。
- 兼容 `YYYY-M-D` 与 `YYYY-MM-DD`，发布日期按北京时间零点解释；为空或无效时使用创建时间，数据库无时区时间按 UTC 解释。
- 每项包含标题、摘要、原文链接、发布日期、稳定 GUID，以及非空的分类。简介为空时，摘要从数据库中预渲染正文提取前 200 字纯文本，排除脚本和样式内容。
- 原文地址使用后端 `FRONTEND_URL` 与编码后的文章 slug；GUID 由站点、文章 ID、创建时间组成，编辑标题、slug、正文时保持稳定。
- 频道名称和简介使用交换友链配置，空值回退到博客默认名称及简介。XML 直接从数据库生成，文章发布后在阅读器下次抓取且缓存过期时体现。
- 前端静态 HTML 中的 `link[rel="alternate"][type="application/rss+xml"]` 始终指向本站接口，构建时沿用 `VITE_API_BASE_URL`。

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
| 503 | 公开 JSON 副本同步失败（`FRIEND_JSON_SYNC_FAILED`；写操作通常已先提交数据库） |

---

## 静态文件访问

是否访问 R2 取决于每条记录的 `storage_backend` 和 `r2_key`，启用 `R2_ENABLED` 不会自动迁移本地文件。

| 访问入口 | R2 文件的实际分发方式 |
|----------|----------------------|
| `/uploads/...` 中登记的图片、通用文件和背景自有视频 | 配置公开域名时通常 `307`；带 `download=1` 或 Authorization 时由后端代理；无公开域名时也代理 |
| `/api/v1/files/{id}/media`、`/api/v1/backgrounds/media/{name}` | 配置公开域名时 `307`，否则后端代理 |
| `/api/v1/files/{id}/download` | 后端从 R2 取回并发送附件，仍占用服务器流量 |
| 图书 `/read`、`/read-resource/...`、管理员 `/download` | 从本地 EPUB 提供；缺少副本时从 R2 回填，再由服务器响应 |
| 已派生的 `r2_url` 直链 | 浏览器直接访问 R2，没有本站 `307` 这一步 |

本地记录直接返回本地文件；`/uploads/books/...` 等未匹配上述存储记录的路径也使用本地兜底。由相对路径派生的文件访问先解析真实路径并检查其仍位于 `UPLOAD_DIR` 内，绝对路径、空路径段和解析后越界的路径会被拒绝（包括指向目录外的符号链接）。公开下载、媒体和 `/uploads/` 访问返回 `404`；删除服务抛出异常并保留目录外文件，不自动修复损坏记录。
跨域媒体的 CORS 由 R2 桶策略放行；前端另以 `_cors=2` 查询参数隔离浏览器缓存键
（详见 [background-media.md](./background-media.md)）。

上传也有不同入口：文件管理页选 R2 时，图片 / 普通文件使用预签名 PUT 直传，再登记数据库；
其他仍调用 `/images/upload`、`/files/upload` 的入口先将内容交给后端，再按存储选项写入本地或 R2。
EPUB 和背景自有视频经服务器处理并保留本地副本。已有本地文件迁移到 R2 后，当前实现保留本地文件，
更新存储记录并维持原访问地址；上传不会为每个文件新增 FastAPI 路由。

`POST /api/v1/r2-migration/register-upload` 仅接受预签名上传使用的键结构：`files/<32位小写十六进制UUID>.<1–10位小写字母数字扩展名>`，或 `images/YYYY/MM/<12位小写十六进制UUID>_<1–200位安全文件名>.<扩展名>`。图片键中的文件名仅保留 `A–Z a–z 0–9 . _ -`，其他字符替换为下划线，最长 200 字符；原始文件名独立保存在记录中。格式不合法返回 `400`，校验通过后仍须确认对象已上传。检查只约束新登记，不重写历史记录或 R2 对象键。

历史同源路径（用于后台管理与兼容）：

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
