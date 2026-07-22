# 前端数据流与 Fallback 机制

## 设计理念

Starlit Blog 前端采用 **API 优先 + 静态 Fallback** 双层数据策略。这意味着：

1. 前端可以**独立运行**（不启动后端也能展示内容）
2. 后端 API 恢复后**自动切换**到动态数据
3. 通过环境变量可**完全禁用** API 调用

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
| `'false'` | 所有 API 请求立即抛出 `ApiError`，触发各页面 catch fallback |

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
| 友链 | `fetchFriends()` | `getFriends()` | 标准 |
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

### 扩展路径（未来）

```
site-text.ts (静态默认值)
      ↓ 被覆盖
SiteConfig API (管理员后台设置)
      ↓ 注入
页面模板 (优先使用 API 值)
```

---

## API 层文件结构

```
src/api/
├── client.ts          # HTTP 客户端封装 + USE_API 开关 + resolveUrl
├── posts.ts           # 博文 API
├── comments.ts        # 评论 API
├── moments.ts         # 说说 API
├── books.ts           # 图书 API（含搜索分页）
├── gallery.ts         # 展览 API
├── albums.ts          # 相册 API
├── backgrounds.ts     # 背景图 API
├── carousel.ts        # 轮播图 API
├── friends.ts         # 友链 API
├── treasures.ts       # 藏宝阁 API
├── profile.ts         # 个人资料 API
└── tavern.ts          # 深夜酒馆 API
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
| API 返回 4xx/5xx | 抛出 `ApiError`，页面 catch 保留 fallback |
| 网络不可达 | fetch 抛 TypeError，页面 catch 保留 fallback |
| `USE_API=false` | `request()` 直接抛 `ApiError`，页面 catch 保留 fallback |
| API 返回空数据 | 不替换 fallback（`if (data.length > 0)` 检查） |
| 401 Unauthorized | 自动清除本地 Token |

所有错误都是**静默处理**（不弹窗不提示），用户无感知地使用 fallback 数据。
