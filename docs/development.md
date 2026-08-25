# 开发指南

## 包管理器

前端使用 **pnpm**（不是 npm/yarn）。锁文件为 `pnpm-lock.yaml`。

```bash
cd blog-frontend
pnpm install
```

后端使用 **pip + venv**：

```bash
cd blog-backend
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 命令速查

### 前端

| 命令 | 说明 |
|------|------|
| `pnpm dev` | 启动开发服务器（Vite HMR） |
| `pnpm build` | 生产构建（type-check + vite build） |
| `pnpm preview` | 预览构建产物 |
| `pnpm type-check` | TypeScript 类型检查（vue-tsc） |
| `pnpm test:unit` | 运行单元测试（Vitest） |
| `pnpm format` | 代码格式化（oxfmt） |

### 后端

| 命令 | 说明 |
|------|------|
| `uvicorn app.main:app --reload` | 启动开发服务器 |
| `python -m scripts.init_xxx` | 运行初始化脚本 |
| `python -m scripts.init_xxx --force` | 强制覆盖重新初始化 |

后端应用启动时会自动创建数据库表、执行兼容性字段迁移、准备运行时目录、清理过期归档和统计限流记录，并创建 `.env` 配置的默认管理员账户。初始化脚本主要用于导入或重置内容数据，不是每次启动的必需步骤。生产环境还会校验密钥、管理员密码、Cookie 安全配置和代理配置等安全参数。

---

## 代码风格

### TypeScript / Vue

- **严格模式**：`strict: true` + `noUnusedLocals` + `noUnusedParameters`
- **格式化工具**：oxfmt（非 Prettier），配置 `.oxfmtrc.json`：`semi: false`, `singleQuote: true`
- **注释风格**：中文注释，所有 `interface`/`type` 和导出函数必须有注释
- **路径别名**：`@` → `./src/*`
- **组件风格**：`<script setup lang="ts">` + Composition API

### Python

- **类型注解**：所有函数参数和返回值使用类型注解
- **docstring**：每个模块、类、公共函数需要有文档字符串
- **命名**：snake_case（变量/函数/文件），PascalCase（类/模型）

---

## 路径别名

前端配置了 `@` → `./src/*`（同时配置在 `vite.config.ts` 和 `tsconfig.json` 中）：

```ts
import { fetchPosts } from '@/api/posts'
import type { Post } from '@/types'
import PageBackground from '@/components/PageBackground.vue'
```

---

## 新增页面的标准流程

### 1. 创建视图文件

```
src/views/my-page/my-page.vue
```

### 2. 注册路由

```ts
// src/router/index.ts
{
  path: '/my-page',
  component: () => import('@/views/my-page/my-page.vue'),
}
```

### 3. 添加页面默认文案

```ts
// src/data/site-text.ts
myPage: {
  kicker: 'MyPage',
  title: '我的页面',
  subtitle: '页面描述文字。',
},
```

### 4. 页面模板标准结构

```vue
<template>
  <PageBackground>
    <main class="my-page">
      <section class="section-heading">
        <span class="kicker">{{ siteText.myPage.kicker }}</span>
        <h1>{{ siteText.myPage.title }}</h1>
        <p>{{ siteText.myPage.subtitle }}</p>
      </section>
      <!-- 页面内容 -->
    </main>
  </PageBackground>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import PageBackground from '@/components/PageBackground.vue'
import { siteText } from '@/data/site-text'
// ...
</script>
```

---

页面默认文案集中在 `src/data/site-text.ts`。后端 `SiteConfig` 目前只覆盖部分站点配置，不会自动覆盖所有页面标题和副标题。

## 新增 API 端点的标准流程

### 后端（5 步）

1. **Model** — `app/models/xxx.py`，定义 SQLAlchemy ORM 模型
2. **Schema** — `app/schemas/xxx.py`，定义 Pydantic 请求/响应模型
3. **Service** — `app/services/xxx.py`，实现业务逻辑
4. **Router** — `app/api/v1/xxx.py`，定义路由端点
5. **注册** — `app/models/__init__.py` + `app/api/v1/router.py` 注册

需要认证的接口通过 `app.api.deps` 中的当前用户或管理员依赖保护。公开内容接口通常应保持前端 API 优先、静态 fallback 的兼容方式。

### 前端（3 步）

1. **API 层** — `src/api/xxx.ts`，封装 HTTP 调用
2. **类型** — `src/types/index.ts`，定义前端接口类型
3. **页面** — `onMounted` 调 API + `try/catch` fallback

---

## 前端数据层约定

### 静态数据（Fallback）

位于 `src/data/`，每个文件导出一个 `getXxx()` 函数返回静态数据：

```ts
// src/data/friends.ts
export function getFriends(): Friend[] {
  return [...]
}
```

### API 调用层

位于 `src/api/`，每个文件对应一个后端模块：

```ts
// src/api/friends.ts
export async function fetchFriends(): Promise<Friend[]> {
  const resp = await api.get<FriendListResponse>('/api/v1/friends')
  return resp.items.map(...)
}
```

### 页面使用模式

```ts
// 初始使用 fallback
const data = ref(getXxx())

// onMounted 尝试 API
onMounted(async () => {
  try {
    const apiData = await fetchXxx()
    if (apiData.length > 0) data.value = apiData
  } catch {
    // 保留 fallback
  }
})
```

---

## Git 工作流

参见 [AGENTS.md](../AGENTS.md) 中的 Git 工作流规范，要点：

- **分支策略**：`main`（稳定）→ `dev`（集成）→ `feat/*`（功能）/ `fix/*`（修复）
- **提交规范**：`<type>(<scope>): <描述>`，如 `feat(frontend): 完成说说页评论功能`
- **提交前检查**：`pnpm type-check` 必须通过
- **单次提交原子化**：一个提交解决一个问题

---

## 调试技巧

### 前端

- **Vue DevTools**：开发时自动加载（`vite-plugin-vue-devtools`）
- **API 请求调试**：打开浏览器 Network 面板查看请求/响应
- **禁用 API**：`.env.local` 设 `VITE_USE_API=false`，只看前端效果
- **液态玻璃关闭**：设置面板中可关闭 LiquidGlass（降低 GPU 负载）
- **登录调试**：检查 `Authorization` 请求头、`blog_admin_token` localStorage 项，以及 `/api/v1/auth/refresh` 的 Cookie 请求

### 后端

- **Swagger 交互测试**：访问 `http://localhost:8000/docs`，可直接发请求
- **SQL 日志**：FastAPI 默认开启 SQLAlchemy echo，控制台可看 SQL
- **数据库直接查看**：用 `sqlite3 blog.db` 或 DB Browser for SQLite

---

## 目录命名约定

| 类型 | 规则 | 示例 |
|------|------|------|
| 视图文件夹 | kebab-case | `views/study-room/` |
| 组件文件 | PascalCase | `NavBar.vue`、`PostCarousel.vue` |
| 工具/数据文件 | camelCase 或 kebab-case | `site-text.ts`、`useTypewriter.ts` |
| 后端模块 | snake_case | `app/models/album.py` |
| 后端脚本 | snake_case + `init_` 前缀 | `scripts/init_albums.py` |

---

## 关键配置文件

| 文件 | 用途 |
|------|------|
| `blog-frontend/vite.config.ts` | Vite 构建配置（插件/别名/chunk 分割） |
| `blog-frontend/tsconfig.json` | TypeScript 配置 |
| `blog-frontend/.oxfmtrc.json` | 格式化配置 |
| `blog-backend/app/config.py` | 后端全局配置（Pydantic Settings） |
| `blog-backend/requirements.txt` | Python 依赖 |
| `AGENTS.md` | AI 助手开发指令 |
