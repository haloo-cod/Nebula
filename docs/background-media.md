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

未被引用返回 `404`，非视频返回 `415`。该接口仍由 `FileResponse` 提供浏览器 Range 分段播放。
删除仍被背景引用的文件返回 `409`，必须先解除背景引用，避免背景变成失效链接。

## 数据字段

`Background` 保留图片 `image_id`，并增加：

- `media_type`：`image` 或 `video`；
- `media_url`：视频本地接口或外部 URL；
- `poster_url`：可选封面图；
- `mime_type`、`file_size`：媒体元数据。

旧图片记录会在后端启动时自动补充字段并标记为 `media_type=image`，无需重新上传。
