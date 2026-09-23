# R2 迁移后视频背景：CORS 失败与 206 缓存慢的排查与修复

> 适用版本：dev 分支（`_cors=2` CORS 隔离、完整视频独立缓存键 + `resolveVideoSource` blob: 内存播放）
> 关联组件：`liquidGlassRenderer.ts` / `PageBackground.vue` / `BackgroundPicker.vue`

## 背景

站点媒体从本地磁盘迁移到 Cloudflare R2（自定义域 `r2.starlitn.top`）后，图片背景切换一切正常，视频背景切换必然失败：

- 控制台报 `Access to video at 'https://r2.starlitn.top/files/...mp4' ... has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header`，`video.readyState` 停在 0；
- 即使边缘缓存命中（`cf-cache-status: HIT`，206 响应），每次切换仍要完整走一遍网络，加载明显变慢——迁移前浏览器缓存的视频几乎秒开。

媒体链路架构：

```
浏览器（同源请求，带 Origin + sec-fetch-mode: cors）
  │
  │  GET https://blog.starlitn.top/api/v1/files/{id}/media?_cors=2
  ▼
Nginx / 后端 —— 307 重定向（不缓存，保留可迁移性）
  │
  │  GET https://r2.starlitn.top/files/xxx.mp4?_cors=2（浏览器自动带上原 Origin）
  ▼
Cloudflare R2 —— 命中则边缘直出，未命中回源存储桶
```

307 保留同源路径作为稳定入口，未来换存储只改后端重定向目标，前端 URL 永不变化。

## 根因一：浏览器缓存键碰撞导致 CORS 失败

### R2 的 CORS 响应是"按 Origin 有无"变化的

用 curl 对比同一 URL：

```bash
# 带 Origin：返回 ACAO + Vary: Origin —— 健康
curl -sI "https://r2.starlitn.top/files/xxx.mp4" -H "Origin: https://blog.starlitn.top" | grep -i "access-control\|vary"
# access-control-allow-origin: https://blog.starlitn.top
# vary: Origin

# 不带 Origin：无 ACAO、无 Vary —— 被缓存后即为"毒缓存"
curl -sI "https://r2.starlitn.top/files/xxx.mp4" | grep -i "access-control\|vary"
# （空）
```

R2（以及多数 CDN）只在请求携带 `Origin` 头时才输出 ACAO，且此时响应带 `Vary: Origin`。

### 问题链条

1. **no-cors 请求**：`<video>` / `<img>` 不带 `crossorigin` 属性时，浏览器以 no-cors 模式请求——请求头里**没有 `Origin`**；
2. R2 对无 Origin 请求返回**无 ACAO、无 Vary** 的 200 响应，浏览器把它存入 HTTP 缓存（键 = URL，因为无 Vary）；
3. **cors 请求**复用同一 URL：渲染器预加载视频设置 `video.crossOrigin = 'anonymous'`（WebGL `texImage2D` 上传跨域纹理的硬性要求），此时浏览器查缓存，命中第 2 步那条**没有 ACAO 的缓存条目**，直接拿给 CORS 校验流程；
4. 校验失败：缓存的响应没有 `Access-Control-Allow-Origin` → `ERR_FAILED`，`readyState: 0`，纹理上传失败。

关键在于 `Vary: Origin` 本应防止这种误用，但它只出现在"带 Origin 的响应"上——**先被缓存的是不带 Origin 的那份**，`Vary` 无从谈起。两个请求模式的 URL 完全相同时，碰撞无法避免。

### 修复：`_cors=2` 缓存键隔离

给所有 CORS 模式的媒体 URL 追加查询参数，让两类请求的缓存键永不相交：

```typescript
// liquidGlassRenderer.ts
export function withCorsCacheKey(url: string): string {
  return url + (url.includes('?') ? '&' : '?') + '_cors=2'
}
```

R2 忽略未知查询参数、缓存键包含查询串，因此：

- `xxx.mp4?_cors=2`（cors 模式，带 Origin）→ 永远拿到带 ACAO 的响应；
- `xxx.mp4`（no-cors 模式，无 Origin）→ 独立缓存，互不污染。

应用到的全部消费点：

| 位置 | 说明 |
|---|---|
| `loadImage`（渲染器图片纹理） | fetch 图片走 `_cors=2` |
| `preloadVideoTextureInternal`（渲染器视频纹理预加载） | `resolveVideoSource(url).catch(() => withCorsCacheKey(url))`，纹理键仍用原始 URL |
| `PageBackground.vue` 可见 `<video>` | 等待 `resolveVideoSource` 完成后设置 blob: URL；失败时才回退 `_cors=2` 直连地址 |
| `BackgroundPicker.vue` 预览/缩略 `<video>` | 补加 `crossorigin="anonymous"`，统一走 CORS 缓存键 |

历史毒缓存无需 purge：旧缓存键（无 `_cors=2`）与新键天然分离，新请求不会命中旧条目。

### 307 重定向不破坏 CORS

同源 307 跳跨域 R2 时，浏览器会在重定向后的请求上**转发原始 Origin 头**，且 CORS 校验只发生在最终响应（R2 一跳）；307 本身不需要 ACAO。因此只需保证 R2 侧对 `Origin: https://blog.starlitn.top` 返回 ACAO（已验证）。Nginx 也无需为此改动：location 匹配只看路径不看查询串，`?_cors=2` 请求照常命中媒体 location 并 307。

## 根因二：206 响应不进浏览器缓存，每次切换重复下载

### 现象

Network 面板里视频每次都是 `206 Partial Content`、`cf-cache-status: HIT`——边缘命中了，但浏览器到伦敦边缘（用户附近节点回源到 LHR）仍有约 580KB/s 的跨洲传输，一个 3.3MB 的视频 ≈ 6 秒。**`HIT` 只省了"边缘→源站"这一段，省不了"浏览器→边缘"这一段。**

### 为什么浏览器不缓存

`<video>` 元素默认发 `Range: bytes=0-` 请求拿 206 分段响应。按 HTTP 缓存规范，浏览器磁盘缓存只存储**完整的 200 响应**；206 部分响应一律不落盘。于是每次把视频挂到新的 `<video>` 元素（切换背景）都重新走网络。

迁移前"浏览器缓存的视频秒开"，是因为当时媒体走后端 `FileResponse`，同一 URL 曾以 200 完整响应被缓存过（且无上述键碰撞问题）。

### 修复：`resolveVideoSource` blob: 内存播放

一次性 `fetch` 完整文件（fetch 不带 Range），并使用独立的 `video=full` 查询参数，与 `<video>` 的 Range 请求以及 `_cors=2` CORS 缓存键隔离，避免复用已有的 206 响应。只接受状态码严格等于 200 的完整响应，再转成 `blob:` URL 交给 `<video>`：

```typescript
function withFullVideoCacheKey(url: string): string {
  return url + (url.includes('?') ? '&' : '?') + '_cors=2&video=full'
}
```

```typescript
// liquidGlassRenderer.ts
const videoSourceCache = new Map<string, Promise<string>>()

export function resolveVideoSource(url: string): Promise<string> {
  const cached = videoSourceCache.get(url)
  if (cached) return cached
  const promise = fetch(withFullVideoCacheKey(url), { mode: 'cors' })
    .then((res) => {
      if (res.status !== 200) throw new Error(`video fetch failed: ${res.status}`)
      return res.blob()
    })
    .then((blob) => URL.createObjectURL(blob))
    .catch((error) => {
      videoSourceCache.delete(url) // 失败逐出，下次可重试
      throw error
    })
  videoSourceCache.set(url, promise) // 并发去重：同 URL 只下载一次
  return promise
}
```

三个收益：

1. **只下载一次**：`videoSourceCache` 缓存 Promise，预加载纹理、PageBackground 可见视频、后续再次切换共享同一次下载与同一个 blob；
2. **秒开**：`blob:` URL 是同源内存对象，`<video>` 播放不再走网络，也不受 HTTP 缓存规则约束；
3. **CORS 天然通过**：blob: 同源，`crossOrigin='anonymous'` 校验直接满足，WebGL 纹理上传安全策略不再拦截。

降级路径：`resolveVideoSource` 失败（如网络错误）时回退 `withCorsCacheKey(url)` 直连，功能不中断，只是退回慢速模式。

### 纹理键一致性

渲染器纹理表（`textureMap`）始终以**原始 URL** 为键——`preloadVideoTextureInternal(url)` 调 `uploadVideoTexture(url, video)`，`bindVideoElement(url, video)` 查 `textureMap.get(url)`，而 `PageBackground.playVideo()` 传入 `displayedBackground.value.src`（原始 URL）。`_cors=2` / blob: 只影响网络请求和 `<video src>`，不进入纹理键，所有调用方无需感知。

## 已知边界情况

`PageBackground.vue` 的 `videoSrc` watch 使用自增 token：只有当前背景对应的 `resolveVideoSource` 请求可以更新视频源，旧请求晚到时会被忽略。

`URL.createObjectURL` 创建的 object URL 当前不会 `revoke`；数量上限为使用过的不同背景视频数，适用于目前背景视频数量较少的场景。

## 验证结论

- `pnpm type-check` 零错误；`pnpm build` 成功，当前 chunk（`index-*.js`）含 `resolveVideoSource` 定义与 3 处调用、`withCorsCacheKey` 定义与应用、3 处 `crossorigin:"anonymous"` video 绑定；
- 单测 4/4 通过；mock fetch 探针验证：并发去重为一次下载、失败后缓存逐出可重试、404 不污染缓存；
- curl 验证 R2 对 `Origin: https://blog.starlitn.top` 及 307 转发后的 Origin 均返回 ACAO；对无 Origin 请求不返回（符合上述诊断）。

## 部署后自检

1. 打开站点切换到视频背景，Network 里应出现**一次**完整 200 媒体请求（URL 带 `_cors=2`）；
2. 再次切换同一视频：不再有媒体网络请求（blob: 内存命中）；
3. 控制台无 `blocked by CORS policy`、无 `Video texture upload failed`。
