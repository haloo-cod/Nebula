# 背景媒体

背景支持图片和视频，并按主题（`dark`/`light`）、设备（`desktop`/`mobile`）和排序统一管理。

## 视频格式

管理员可调用 `POST /api/v1/backgrounds/video-upload` 上传视频，字段为
`multipart/form-data` 的 `file`。MIME 与扩展名必须匹配：

| MIME | 扩展名 |
|---|---|
| `video/mp4` | `.mp4` |
| `video/webm` | `.webm` |
| `video/quicktime` | `.mov` |

上传接口返回的 URL 可用于创建 `media_type=video` 的背景。后台也支持从文件管理中选择视频，
对应 URL 为 `/api/v1/files/{file_id}/media`，无需重复上传。

## 公开媒体安全规则

`GET /api/v1/files/{file_id}/media` 为浏览器背景播放提供公开内联访问，但只允许：

- 文件 MIME 以 `video/` 开头；
- 文件当前被 `Background` 的视频记录引用。

未被引用返回 `404`，非视频返回 `415`。删除仍被背景引用的文件返回 `409`，必须先解除背景引用，避免背景变成失效链接。

## R2 存储与前端加载策略

媒体已迁移至 Cloudflare R2（自定义域 `r2.starlitn.top`）。`/api/v1/files/{file_id}/media`
不再直接 `FileResponse` 出文件，而是返回 **307 重定向**到 R2 地址——同源入口保持稳定，
未来更换存储只改后端重定向目标。重定向响应不缓存（`Cache-Control: no-cache`），
浏览器会转发原始 `Origin` 头到 R2，CORS 校验发生在 R2 一跳（R2 已配置允许站点域名）。

前端两条配套规则（详见 [r2-video-cors-cache.md](./r2-video-cors-cache.md)）：

- **`_cors=2` 缓存键隔离**：R2 对不带 `Origin` 的请求返回无 ACAO、无 `Vary` 的响应；
  若 no-cors 与 cors 请求共用 URL，先缓存的 no-cors 响应会毒化后续 CORS 校验。
  所有 CORS 模式加载（渲染器纹理、可见 `<video>`、选择器预览）统一经
  `withCorsCacheKey()` 追加 `_cors=2` 参数，两类请求缓存键永不相交。
- **视频经 blob: 内存播放**：`<video>` 的 Range 请求拿到 206 分段响应，浏览器
  磁盘缓存只存 200 完整响应，因此切换背景会反复走网络。前端用
  `resolveVideoSource(url)` 一次性 fetch 完整文件并转为 `blob:` URL，各消费点
  （纹理预加载、PageBackground、BackgroundPicker）共享同一次下载。
  渲染器纹理键始终用原始 URL，`_cors=2` / blob: 不进入纹理键。

## 数据字段

`Background` 保留图片 `image_id`，并增加：

- `media_type`：`image` 或 `video`；
- `media_url`：视频本地接口或外部 URL；
- `poster_url`：可选封面图；
- `mime_type`、`file_size`：媒体元数据。

旧图片记录会在后端启动时自动补充字段并标记为 `media_type=image`，无需重新上传。
