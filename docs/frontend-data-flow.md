# 前端数据流与 Fallback 机制

## 设计理念

Starlit Blog 前端多数展示页采用 **API 优先 + 静态 Fallback** 双层数据策略。这意味着：

1. 多数展示页可以**独立运行**（不启动后端也能展示静态内容）
2. 后端 API 恢复后**自动切换**到动态数据
3. 通过环境变量可**完全禁用** API 调用

评论、友链申请和后台管理属于真实业务数据，不使用预置内容伪装成功：请求失败时显示加载错误和重试入口，评论区域不会展示 seed／演示评论。

---

## 全局 API 开关

### 配置

文件：`src/api/client.ts`

```ts
export const USE_API = import.meta.env.VITE_USE_API !== 'false'
```

### 行为

| `VITE_USE_API` | 效果 |
|----------------|------|
| 未设置 / `'true'` | 正常调用后端 API |
| `'false'` | 所有 API 请求立即抛出 `ApiError`；展示页使用 fallback，评论与申请显示错误态 |

### 拦截位置

在 `request()` 函数顶部统一拦截：

```ts
async function request<T>(...): Promise<T> {
  if (!USE_API) {
    throw new ApiError(0, 'API 已禁用（VITE_USE_API=false）')
  }
  // 正常请求逻辑...
}
```

各页面的 `try/catch` 自动捕获，无需逐个修改。

---

## 数据流模式

### 标准模式（大多数页面）

```
┌─────────────────────────────────────────────────┐
│                   Vue 组件                       │
├─────────────────────────────────────────────────┤
│ const data = ref(getStaticData())   ← fallback │
│                                                 │
│ onMounted(async () => {                         │
│   try {                                         │
│     const apiData = await fetchXxx()  ← API    │
│     data.value = apiData              ← 替换   │
│   } catch {                                     │
│     // 保留 fallback 静态数据                    │
│   }                                             │
│ })                                              │
└─────────────────────────────────────────────────┘
```

### 真实数据区域（评论与友链申请）

这些区域不加载静态 fallback，接口就是唯一数据源：

- **评论**：`AboutComments` 接收 `pageKey`（关于页默认 `about`，博文为 `post:{slug}`，友链申请为 `friend-application:{id}`）。初次加载显示“正在加载评论…”，失败时清空列表并保留错误和“重试”按钮；不会出现预置评论。发表成功后把服务器返回的评论追加到对应父节点，删除后重新加载评论树。页面标识或登录身份变化会清空旧评论、输入和回复对象，并用请求序号丢弃过期响应。
- **友链申请**：`/friends` 的申请区分别加载公开申请和本人申请，初始为空而不是静态数据。公开列表失败时显示错误和重试，同时保留上一次成功加载的卡片；本人列表失败时显示错误和重试。提交成功后只清空站点字段并刷新本人第一页；登录用户变化时清空私有记录，避免账号串数据。
- **焦点刷新**：友链页主列表和申请区监听 `window` 的 `focus`；窗口重新获得焦点时主列表重新请求友链，申请区重新请求公开申请和本人记录。没有轮询。评论组件不自动轮询，按页面打开或重试加载。
- **申请讨论**：公开申请卡片展开时才挂载 `AboutComments`，折叠即卸载，避免进入友链页就请求所有申请的评论。管理员讨论抽屉独立加载同一 `page_key`，申请删除或不再公开时后端返回 `404`，前端关闭讨论并刷新列表。

### 后端分页模式（图书页）

```
┌─────────────────────────────────────────────────┐
│ const books = ref([])                           │
│ const totalBooks = ref(0)                       │
│                                                 │
│ async function loadBooks() {                    │
│   try {                                         │
│     const resp = await fetchBooks(              │
│       page, PAGE_SIZE, keyword                  │
│     )                                           │
│     books.value = resp.items                    │
│     totalBooks.value = resp.total               │
│   } catch {                                     │
│     // fallback 到本地 glob 数据 + 前端分页     │
│   }                                             │
│ }                                               │
│                                                 │
│ watch(currentPage, loadBooks)                   │
│ watch(searchQuery, debounce(loadBooks, 300))    │
│ onMounted(loadBooks)                            │
└─────────────────────────────────────────────────┘
```

### Store 加载模式（背景图）

```
┌─────────────────────────────────────────────────┐
│ // stores/ui.ts                                 │
│                                                 │
│ const darkBgs = ref([...defaultDarkBgs])        │
│                                                 │
│ async function loadBackgrounds() {              │
│   const [dark, light, ...] = await Promise.all( │
│     fetchBackgrounds('dark', 'desktop'),        │
│     fetchBackgrounds('light', 'desktop'),       │
│     ...                                         │
│   )                                             │
│   if (dark.length > 0) darkBgs.value = dark     │
│ }                                               │
│                                                 │
│ // App.vue onMounted 中调用                      │
│ ui.loadBackgrounds()                            │
└─────────────────────────────────────────────────┘
```

---

## 各页面数据源一览

| 页面 | API 调用 | Fallback 数据源 | 模式 |
|------|---------|----------------|------|
| 首页个人资料 | `fetchProfile()` | `src/data/profile.ts` | 标准 |
| 首页轮播 | `fetchCarouselSlides()` | 本地 `img2/*.PNG` | 标准 |
| 首页博文轮播 | `fetchPosts(1, 5)` | `getPosts()` glob | 标准 |
| 首页说说轮播 | `fetchMoments(1, 5)` | `getMoments()` | 标准 |
| 博文列表 | `fetchPosts(page, size)` | `getPosts()` glob | 标准 |
| 博文详情 | `fetchPost(slug)` | glob md 文件 | 标准 |
| 归档 | `fetchPosts(1, 200)` | `getPosts()` glob | 标准 |
| 说说 | `fetchMoments(page, size)` | `getMoments()` | 标准 |
| 图书 | `fetchBooks(page, size, keyword)` | `getBooks()` glob | 后端分页 |
| 相册列表 | `fetchAlbums()` | `getAlbums()` | 标准 |
| 相册详情 | `fetchAlbumDetail(id)` | fallback 数据 | 标准 |
| 展览 | `fetchGalleryProjects()` | `getGalleryProjects()` glob | 标准 |
| 友链 | `fetchFriends()` | `getFriends()`；错误显示并保留旧列表 | 标准 + 焦点刷新 |
| 评论（关于/博文/申请讨论） | `fetchComments(pageKey)` | 无，错误 + 重试 | 真实数据 |
| 友链公开申请 | `fetchFriendApplications(page, size)` | 无，错误 + 重试 | 真实数据 + 焦点刷新 |
| 我的友链申请 | `fetchMyFriendApplications(page, size)` | 无，错误 + 重试 | 真实数据 + 焦点刷新 |
| 藏宝阁 | `fetchTreasures()` | `getTreasures()` | 标准 |
| 背景图 | `fetchBackgrounds(theme, device)` | `src/data/backgrounds.ts` | Store |
| 关于页内容 | API 获取 about.md | 本地 md 文件 | 标准 |
| 活动日志 | 3 个 API 并行调用 | `getPosts()` glob | 标准 |
| 深夜酒馆 | `fetchTavernPosts()` | 组件内硬编码 | 标准 |
| 自习室 | — | localStorage | 纯本地 |

---

## 页面文案管理

### 集中配置

文件：`src/data/site-text.ts`

```ts
export const siteText: Record<string, PageText> = {
  images:   { kicker: 'Images',   title: '图片',   subtitle: '...' },
  friends:  { kicker: 'Friends',  title: '友链',   subtitle: '...' },
  // ...
}
```

### 页面使用

```vue
<template>
  <span class="kicker">{{ siteText.images.kicker }}</span>
  <h1>{{ siteText.images.title }}</h1>
  <p>{{ siteText.images.subtitle }}</p>
</template>

<script setup>
import { siteText } from '@/data/site-text'
</script>
```

### 当前使用范围

```
site-text.ts (静态默认值)
      ↓
页面模板 (直接使用静态文案)

SiteConfig API 当前主要用于少量可配置内容（例如关于页封面、友链交换信息、酒馆背景），
尚未统一覆盖所有页面的 kicker/title/subtitle。
```

---

## API 层文件结构

```
src/api/
├── client.ts          # HTTP 客户端封装 + USE_API 开关 + resolveUrl
├── posts.ts           # 博文 API
├── comments.ts        # 评论 API（读取、发表、删除、批量计数）
├── moments.ts         # 说说 API
├── books.ts           # 图书 API（含搜索分页）
├── gallery.ts         # 展览 API
├── albums.ts          # 相册 API
├── backgrounds.ts     # 背景图 API
├── carousel.ts        # 轮播图 API
├── friends.ts         # 友链、申请审核与 JSON 同步 API
├── treasures.ts       # 藏宝阁 API
├── profile.ts         # 个人资料 API
├── tavern.ts          # 深夜酒馆 API
├── analytics.ts       # 访问统计与公开统计摘要
├── content-stats.ts   # 内容统计
└── files.ts           # 文件上传、列表和下载
```

### client.ts 公共功能

| 导出 | 用途 |
|------|------|
| `api.get/post/put/delete` | HTTP 方法封装 |
| `resolveUrl(path)` | 补全后端静态资源 URL（自动加 BASE_URL + 前导 `/` + encodeURI） |
| `getToken()` / `setToken()` / `clearToken()` | JWT 管理 |
| `ApiError` | 统一错误类（status + detail） |
| `USE_API` | API 开关常量 |

---

## resolveUrl 说明

后端返回的图片/文件路径通常是相对路径（如 `/uploads/images/xxx.jpg`）。`resolveUrl()` 负责将其补全为完整可访问 URL：

```ts
export function resolveUrl(url: string): string {
  if (!url) return ''
  if (url.startsWith('http')) return url  // 已是完整 URL，不处理
  const path = url.startsWith('/') ? url : `/${url}`  // 补前导 /
  return encodeURI(`${BASE_URL}${path}`)  // 编码特殊字符
}
```

所有从 API 获取的图片 URL 都需要经过 `resolveUrl()` 处理后才能用于 `<img :src="...">` 或 CSS `background-image`。

---

## 错误处理策略

| 场景 | 处理方式 |
|------|---------|
| API 返回 4xx/5xx | 抛出 `ApiError`；展示页可保留 fallback，评论/申请显示错误并可重试 |
| 网络不可达 | fetch 抛 TypeError；同上 |
| `USE_API=false` | `request()` 直接抛 `ApiError`；展示页使用静态数据，真实数据区域显示加载失败 |
| API 返回空数据 | 多数静态 fallback 页面仅在非空时替换；友链、评论和申请以接口空列表为准 |
| 401 Unauthorized | 自动清除本地 Token；申请提交提示重新登录 |
| 友链 JSON 同步失败 | `503 FRIEND_JSON_SYNC_FAILED`：数据已保存，界面提示并提供“重新同步”且不重复写库 |

展示页的错误通常是**静默降级**，用户继续看到静态内容；评论、友链申请和后台管理会显示明确的加载/操作错误与重试入口，不会用演示数据掩盖失败。删除评论或申请后，相关区域重新请求服务器数据，避免本地乐观数据与服务端不一致。
