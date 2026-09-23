---
title: "一个 _cors=2 查询参数救了我的视频背景：R2 迁移后的缓存投毒排查记"
description: "图片好好的，视频一切换就 CORS 报错；边缘明明缓存命中，加载却比迁移前慢得多。一次由浏览器缓存键碰撞引发的事故，和它背后两条容易被忽视的 HTTP 缓存规则。"
published: 2026-09-23
tags: "前端, HTTP缓存, CORS, R2, 踩坑记录"
category: "技术"
---

上周把博客的媒体存储从服务器本地磁盘迁到了 Cloudflare R2。迁移完图片背景一切正常，我心里还挺美——直到切换视频背景的那一刻，控制台开始刷屏：

```
Access to video at 'https://r2.starlitn.top/files/xxx.mp4' from origin
'https://blog.starlitn.top' has been blocked by CORS policy:
No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

`video.readyState` 卡在 0，WebGL 纹理上传跟着失败。更诡异的是第二个症状：Network 面板里视频明明显示 `cf-cache-status: HIT`，每次切换却还是要等五六秒才播得动——迁移前，浏览器缓存的视频可是秒开的。

两个问题，两个根因，都藏在浏览器 HTTP 缓存的细节里。排查过程挺有意思，写下来备忘。

## 先交代一下架构

迁移后的媒体链路长这样：

```
浏览器
  │  GET https://blog.starlitn.top/api/v1/files/{id}/media
  ▼
Nginx/后端 —— 307 重定向（不缓存）
  │
  │  GET https://r2.starlitn.top/files/xxx.mp4（浏览器自动带上原 Origin）
  ▼
Cloudflare R2
```

同源路径 307 跳 R2 自定义域，好处是入口 URL 永远稳定，哪天再换存储只改后端重定向目标就行。R2 那边也确实配置了 CORS 允许我的域名。

那为什么会报「没有 ACAO 头」？

## 根因一：缓存键碰撞

用 curl 复现了一下，同一个 URL，两种请求：

```bash
# 带 Origin —— 有 ACAO，有 Vary: Origin，一切健康
$ curl -sI "https://r2.starlitn.top/files/xxx.mp4" \
    -H "Origin: https://blog.starlitn.top" | grep -i "access-control\|vary"
access-control-allow-origin: https://blog.starlitn.top
vary: Origin

# 不带 Origin —— ACAO 没有，Vary 也没有
$ curl -sI "https://r2.starlitn.top/files/xxx.mp4" | grep -i "access-control\|vary"
（空）
```

R2 和大多数 CDN 一样：请求带 `Origin` 才回 ACAO，同时响应带 `Vary: Origin`。

到这里，事故链条就清楚了：

1. 页面里有几个 `<video>` 元素**没写** `crossorigin` 属性。浏览器对它们发起的是 no-cors 请求——请求头里**没有 Origin**；
2. R2 对无 Origin 的请求返回一份**没有 ACAO、也没有 Vary** 的 200 响应。浏览器把它存进磁盘缓存。缓存键就是 URL 本身，因为响应里没有任何 Vary；
3. 而背景渲染器预加载视频时必须设置 `video.crossOrigin = 'anonymous'`——这是 WebGL 上传跨域纹理的硬性要求，不然 `texImage2D` 会被浏览器安全策略拒绝。于是同一个 URL 又来了一次 **cors 模式**请求；
4. 浏览器查缓存，命中了第 2 步存下的那份**没有 ACAO 的响应**，直接拿去做 CORS 校验；
5. 校验失败。`ERR_FAILED`，`readyState: 0`。

妙就妙在 `Vary: Origin` 本来就是防这种情况的，但它只会出现在「带 Origin 的响应」上——**先被缓存的是不带 Origin 的那份**，Vary 根本没机会写入。两类请求 URL 完全相同时，这个碰撞无解。

修复也就一行的事：给所有 CORS 模式的 URL 加个查询参数，把两类请求的缓存键彻底分开：

```typescript
export function withCorsCacheKey(url: string): string {
  return url + (url.includes('?') ? '&' : '?') + '_cors=2'
}
```

R2 忽略未知参数，缓存键含查询串，于是 `xxx.mp4?_cors=2`（带 Origin）和 `xxx.mp4`（不带）井水不犯河水。连 Cloudflare 的历史缓存都不用 purge——旧键和新键天然不同，新请求根本碰不到旧条目。

顺手验证了一个担心：307 跳跨域会不会把 CORS 搞坏？不会。浏览器在重定向后的请求上会**转发原始 Origin**，CORS 校验只看最终响应（R2 一跳），307 本身不需要 ACAO。Nginx 也不用改——location 匹配只看路径不看查询串。

## 根因二：206 不进浏览器缓存

CORS 修好之后，慢的问题还在。每次切换视频背景，Network 里都是一条 `206 Partial Content`，`cf-cache-status: HIT`。边缘命中了，为什么还要等好几秒？

因为 **`HIT` 只省了「边缘→源站」那一段，省不了「浏览器→边缘」那一段**。我的边缘节点落在伦敦，跨洲传输 3.3MB 的视频，该等还是要等。

那为什么迁移前很快？迁移前媒体走后端直出，那个 URL 曾经以**完整的 200 响应**被浏览器缓存过。而 `<video>` 元素默认发 `Range: bytes=0-`，拿回的是 206 分段响应——按 HTTP 缓存规范，**浏览器磁盘缓存只存完整的 200 响应，206 一律不落盘**。所以每次把视频挂到新的 `<video>` 元素上，都是一次全新的网络下载，边缘命中与否与浏览器无关。

修复思路：绕开 `<video>` 的 Range 请求，自己用 `fetch` 把整个文件拿回来（fetch 不发 Range，R2 回 200，可以被浏览器缓存），转成 `blob:` URL 再喂给 `<video>`：

```typescript
const videoSourceCache = new Map<string, Promise<string>>()

export function resolveVideoSource(url: string): Promise<string> {
  const cached = videoSourceCache.get(url)
  if (cached) return cached
  const promise = fetch(withCorsCacheKey(url), { mode: 'cors' })
    .then((res) => {
      if (!res.ok) throw new Error(`video fetch failed: ${res.status}`)
      return res.blob()
    })
    .then((blob) => URL.createObjectURL(blob))
    .catch((error) => {
      videoSourceCache.delete(url) // 失败逐出，下次可重试
      throw error
    })
  videoSourceCache.set(url, promise) // 缓存 Promise，并发去重
  return promise
}
```

三个好处：

- **一个视频只下载一次**：缓存的是 Promise，渲染器预加载、页面上可见的 `<video>`、后台选择器的预览，全都共享同一次下载和同一个 blob；
- **秒开**：`blob:` URL 是同源内存对象，播放不再走网络；
- **CORS 天然通过**：blob 同源，`crossOrigin='anonymous'` 的校验直接满足，WebGL 纹理上传也不再有麻烦。

失败时回退到 `_cors=2` 直连地址，功能不中断，只是退回慢速模式。

有个细节值得记一笔：渲染器的纹理表以**原始 URL** 为键，`_cors=2` 和 blob: 只存在于网络请求与 `<video src>` 这一层，不渗透进纹理键——所有调用方对这个修复完全无感。

## 两条值得带走的规则

这次踩坑，本质是被两条「平时感知不到、撞上才疼」的 HTTP 缓存规则打了埋伏：

1. **CDN 的 CORS 响应是按 Origin 有无变化的**。不带 Origin 的请求拿到的响应既没有 ACAO 也没有 `Vary: Origin`，它一旦进缓存，就会毒化同 URL 后续所有 CORS 请求。任何「同一 URL 既被 no-cors 用、又被 cors 用」的地方都是雷区——加个查询参数把缓存键分开，是最便宜的排雷方式。
2. **浏览器只缓存完整的 200 响应，206 一律不落盘**。`<video>` 的 Range 请求注定每次走网络；想要「下载一次、反复秒开」，就得自己 fetch 完整文件换 blob: URL。

排查这类问题的黄金姿势还是 curl：同一个 URL，带 Origin 和不带 Origin 各打一发，diff 响应头，缓存投毒立刻现形。Network 面板里那个 `HIT` 会给你一种「缓存工作了」的错觉——但它只代表边缘那一跳，浏览器那一跳才是用户体感的全部。

最后留一个已知未修的小边界：首屏视频还在下载途中就立刻切换背景的话，晚到的旧 blob 可能覆盖新背景的画面，直到下次切换才恢复。触发窗口极窄、只是短暂显示旧背景、无报错——先记在文档里，等它真的烦到我再修。
