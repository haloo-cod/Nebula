# AGENTS.md

## Project overview

`blog-frontend/` — Vue 3 + Vite blog frontend SPA with Vue Router, Pinia, and Tailwind CSS v4. Written in **TypeScript** (`<script setup lang="ts">`). Static Markdown loaded via `import.meta.glob`.

`blog-backend/` — Python FastAPI scaffold (bare-bones, not wired to the frontend yet).

Non-project dirs: `.codegraph/` (code intelligence index), `.agents/` (skill definitions), `示例代码/` (reference examples, ignore).

## Package manager

Use **pnpm** (not npm). The lockfile is `pnpm-lock.yaml`.

```bash
cd blog-frontend
pnpm install
```

## Commands

| Command | Script | Notes |
|---------|--------|-------|
| `pnpm dev` | `vite` | Dev server |
| `pnpm build` | `vue-tsc --noEmit && vite build` | Type-check then production build |
| `pnpm preview` | `vite preview` | Preview built output |
| `pnpm type-check` | `vue-tsc --noEmit` | Standalone type check |
| `pnpm test:unit` | `vitest` | Test runner (jsdom env) |
| `pnpm format` | `oxfmt src/` | Formatter |

No ESLint is configured. Type checking is done via `vue-tsc` (`pnpm type-check`).

## TypeScript

- Source is TypeScript with `strict: true`, plus `noUnusedLocals` and `noUnusedParameters` — unused code will fail type-check. Config: `tsconfig.json` (app, `src/`) + `tsconfig.node.json` (Vite/Vitest config files).
- Global declarations live in `src/env.d.ts`: `*.vue` / `*.md?raw` / `*.svg?url` module shims, the `i18n-jsautotranslate` type shim, and the `Window.translate` augmentation. Do **not** edit the i18n library source — extend the shim instead.
- Shared domain types live in `src/types/index.ts` (`Post`, `Profile`, `Language`, etc.).
- Comment style: Chinese comments throughout. Annotate every `interface`/`type` and exported function; when using `as` / `any` escape hatches, add a comment explaining why.
- Run `pnpm type-check` after changes; it must report zero errors.

## Formatting

- Formatter: **oxfmt** (not prettier/eslint)
- Config: `.oxfmtrc.json` — `semi: false`, `singleQuote: true`
- VSCode auto-format on save via `oxc.oxc-vscode`

## Path alias

`@` → `./src/*` (configured in `vite.config.ts` and `tsconfig.json`).

## Architecture

```
src/
├── main.ts              # Entry: creates app, installs Pinia + Router, inits i18n
├── App.vue              # Shell: NavBar + RouterView
├── router/index.ts      # All routes defined (lazy-loaded via dynamic import)
├── types/index.ts       # Shared domain types (Post, Profile, Language, ...)
├── components/          # Shared components (NavBar.vue) + panels/ + music/
├── composables/         # Reusable logic (useTypewriter.ts, useMusic.ts)
├── data/                # Static data layer (posts.ts, calendar.ts, profile.ts, books.ts, albums.ts, friends.ts)
├── stores/              # Pinia stores (ui.ts)
├── i18n/                # Language list + translate.js helpers
├── views/<name>/        # One folder per route, matching .vue filename
├── assets/              # CSS (Tailwind v4 via @import 'tailwindcss') + images + md/
├── utils/               # Utility helpers
└── env.d.ts             # Global type declarations / module shims
```

Routes: `/` (index), `/archive`, `/archive/tree`, `/archive/post/:slug`, `/books`, `/books/read/:slug`, `/blog`, `/images`, `/gallery`, `/gallery/project/:slug`, `/friends`, `/treasure`, `/midnight-tavern`, `/about`, `/post/:slug`, `/moments`, `/study-room`.

## Deployment quirks

- Router uses **hash history** (`createWebHashHistory`), not HTML5 history mode — all URLs use `#` (e.g. `/index.html#/post/my-slug`).
- Vite `base: './'` — assets use relative paths so the built output works from any subdirectory.
- Route `/midnight-tavern` has `meta: { hideChrome: true }` — NavBar and other chrome components check this to hide themselves.
- Build auto-splits `vue`/`vue-router`/`pinia` into `vue-vendor` chunk and `marked` into its own chunk (see `vite.config.ts` `manualChunks`).

## Testing

- Framework: Vitest + jsdom
- Config merges viteConfig (preserves `@` alias and plugins)
- No test files exist yet; place tests under `src/` as `*.test.ts` or `*.spec.ts`

## Key dependencies

- `tailwindcss` v4 via `@tailwindcss/vite` plugin (CSS-first config, no `tailwind.config.js`)
- Vue 3.5, Vue Router 5, Pinia 3
- Vite 8 with `@vitejs/plugin-vue`, `@vitejs/plugin-vue-jsx`, `vite-plugin-vue-devtools`
- `marked` — Markdown → HTML rendering
- `epubjs` — EPUB reader (book viewer feature)
- `lunar-typescript` — Chinese lunar calendar data
- `i18n-jsautotranslate` — client-side i18n via `window.translate` (Edge translation service)
- Node: `^20.19.0 || >=22.12.0`

## Git 工作流规范

### 仓库结构

Monorepo，`.git` 位于项目根目录 `My_blog/`，前后端并列：

```
My_blog/
├── blog-frontend/
└── blog-backend/
```

### 分支策略

| 分支 | 用途 | 说明 |
|------|------|------|
| `main` | 稳定版 | 只接受合并，不直接提交 |
| `dev` | 日常集成 | 前后端开发完成后合并到这里，测试通过后再合入 main |
| `feat/frontend-*` | 前端功能 | 如 `feat/frontend-music-player` |
| `feat/backend-*` | 后端功能 | 如 `feat/backend-post-api` |
| `fix/*` | Bug 修复 | 如 `fix/router-scroll-restore` |
| `chore/*` | 杂务 | 如 `chore/upgrade-deps` |

### 提交规范（Conventional Commits）

格式：`<type>(<scope>): <简要描述>`

```
feat(frontend): 完成说说页评论功能
feat(backend): 新增文章列表 API
fix(backend): 修复分页越界问题
fix(frontend): 修复暗色模式切换闪白
chore: 升级依赖版本
docs: 补充接口文档
refactor(frontend): 重构液态玻璃渲染逻辑
style(frontend): 调整归档页间距
```

**type 列表：**

- `feat` — 新功能
- `fix` — Bug 修复
- `docs` — 文档变更
- `style` — 样式调整（不影响逻辑）
- `refactor` — 重构（不改变外部行为）
- `perf` — 性能优化
- `chore` — 构建/依赖/配置等杂务
- `test` — 测试相关

**scope（可选）：** `frontend` / `backend` / 省略（影响全局时）

### 日常开发流程

```bash
# 1. 从 dev 创建功能分支
git checkout dev
git pull origin dev
git checkout -b feat/backend-post-api

# 2. 开发，提交（多次小提交）
git add blog-backend/...
git commit -m "feat(backend): 新增文章 CRUD 接口"

# 3. 开发完成，合并回 dev
git checkout dev
git merge feat/backend-post-api

# 4. 测试通过后，合并 dev 到 main
git checkout main
git merge dev
git push origin main

# 5. 清理功能分支
git branch -d feat/backend-post-api
```

### 注意事项

- 不要在 `main` 上直接开发
- 提交前确保 `pnpm type-check` 通过（前端）
- 单次提交尽量原子化：一个提交解决一个问题
- 避免提交 `debug`、`test`、`wip` 等无意义信息（如确需临时提交，合并前 squash）

## Skill awareness

- The `cc-frontend-dev` skill (at `.agents/skills/cc-frontend-dev/SKILL.md`) provides Vue 3 / TS conventions. Its UI prohibitions (no glass morphism, no emoji, no neon gradients) are for admin dashboard projects and do **not** apply to this blog — this project deliberately uses liquid-glass effects, Chinese + emoji comments, and decorative visuals.
