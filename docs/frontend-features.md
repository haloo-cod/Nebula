# 前端特色功能实现

本文介绍项目中最具代表性的两个前端模块：基于 WebGL 的 Liquid Glass，以及基于 `epubjs` 的 EPUB 阅读器。

## 一、Liquid Glass

### 1. 它和普通毛玻璃的区别

项目同时保留两种视觉实现：

- CSS 毛玻璃：使用半透明背景、`backdrop-filter` 和边框阴影，作为低成本默认 fallback。
- Liquid Glass：使用 WebGL shader 对背景纹理进行采样、模糊、折射、边缘高光和交互形变。

Liquid Glass 的目标不是只让面板变模糊，而是模拟一块有厚度的透明介质。背景会根据玻璃形状产生位移，圆角边缘会出现高光，鼠标移动时还可以产生短暂的 ripple trail。

### 2. 核心架构：一个共享 WebGL 实例

项目不会为每个面板单独创建 WebGL context。所有玻璃面板都注册到同一个模块级 renderer singleton：

```text
多个 LiquidGlass 组件
        │
        │ registerInstance()
        ▼
liquidGlassRenderer.ts
        │
        ├── 一个共享 WebGL context
        ├── 一个共享 shader program
        ├── 一个共享离屏 canvas
        ├── 一个共享 requestAnimationFrame 循环
        ├── 按 URL 缓存背景纹理
        └── 统一调度多个可见实例
```

这里的“单一实例”容易被误解：它不是限制页面只能渲染一个玻璃面板，而是限制底层 GPU 渲染资源只初始化一份。每个面板仍然有自己的状态：

- 独立的可见 canvas 和 2D context；
- 独立的 `GlassUniforms`，包括尺寸、圆角、折射率和交互轨迹；
- 独立的背景纹理 URL；
- 独立的首次渲染回调和生命周期；
- 独立的 canvas 尺寸与页面位置偏移。

渲染器会在共享的离屏 canvas 上执行 WebGL 绘制，再把当前实例的结果复制到对应的可见 canvas。这样既能让每个组件显示自己的玻璃区域，又避免重复创建 context、shader program 和纹理资源。

### 3. 实例生命周期

`LiquidGlass.vue` 在挂载时完成以下工作：

1. 创建并同步可见 canvas 尺寸；
2. 根据桌面端或移动端预设初始化 uniforms；
3. 调用 `registerInstance()` 将 canvas、2D context、uniforms 和背景 URL 注册到共享 renderer；
4. 请求当前背景纹理；
5. 通过 `ResizeObserver` 响应面板尺寸变化；
6. 通过 pointer 事件维护鼠标轨迹和 ripple 状态。

卸载时调用 `unregisterInstance()`，并移除 resize、context lost/restored 等回调，避免组件销毁后仍被 renderer 调度。

主题或背景变化时，组件只更新实例参数并通知 renderer 重新绑定纹理，不会重新创建整套 WebGL 管线。

### 4. Shader 效果

fragment shader 主要由以下几个阶段组成：

- 使用 SDF 描述圆角矩形，并通过平滑最小值处理圆角和边界过渡；
- 根据 SDF 生成玻璃表面的高度信息和法线；
- 按玻璃厚度、IOR（折射率）和法线强度计算背景位移；
- 对采样结果执行多点 blur，形成玻璃内部的柔化效果；
- 混合主题 overlay color，分别适配暗色和亮色界面；
- 根据边缘距离生成方向性高光；
- 将鼠标轨迹作为临时的局部凹陷，形成 ripple trail。

背景纹理采用 cover 模式进行 UV 校正，保证不同宽高比的背景图不会因为面板尺寸变化产生明显拉伸。纹理按 URL 缓存，同一个背景不会被每个组件重复上传到 GPU。

### 5. 统一帧循环与性能控制

共享 renderer 统一维护 `requestAnimationFrame`，而不是让每个组件各自启动一条 RAF。这样可以集中处理：

- 当前已注册实例的遍历；
- 纹理是否准备完成；
- 实例 canvas 尺寸是否有效；
- 滚动和交互状态；
- 首次渲染回调；
- WebGL context 状态。

空闲时渲染器会降低更新频率；滚动或 ripple trail 活跃时再提高到更高帧率。设备检测还会针对集成显卡降低 `renderScale`。

`renderScale` 的含义是降低 WebGL canvas 的实际渲染分辨率，也就是减少采样和片元计算量。它不是关闭 WebGL，也不是把液态玻璃变成 CSS 毛玻璃。因此项目不会只依赖降采样来解决移动端性能问题：

- 桌面端默认启用 Liquid Glass；
- 移动端默认使用 CSS 毛玻璃；
- 用户仍然可以通过设置显式开启 Liquid Glass；
- WebGL 不可用或初始化失败时自动显示 CSS fallback。

### 6. 延迟激活与实例上限

`LazyLiquidGlass.vue` 在组件外层增加了可见性和资源槽位管理：

```text
IntersectionObserver 判断是否接近视口
        │
        ▼
请求共享 Liquid Glass 槽位
        │
        ├── 有空闲槽位：挂载 LiquidGlass
        └── 没有槽位：进入等待队列
```

当前最多同时激活 6 个液态玻璃实例。离开视口的组件会释放槽位，等待队列中的组件再获得激活机会。未激活时仍然渲染内容，只是使用 CSS fallback 容器，不会阻塞页面内容。

### 7. 降级和 context 恢复

浏览器可能因为驱动、系统资源或浏览器限制触发 WebGL context lost。renderer 监听 context lost/restored 事件：

- context lost 时暂停绘制并通知组件；
- context restored 后重新创建 program、buffer 和 uniform location；
- 清理失效的 GPU 纹理引用；
- 通知实例重新上传当前背景纹理；
- 组件在 renderer 不可用时保留 CSS 毛玻璃表现。

这保证了 WebGL 只是增强层，不会成为页面内容无法显示的单点故障。

## 二、EPUB 图书阅读器

### 1. 资源来源

生产模式下，图书由后端管理：

```text
管理员上传 EPUB
        │
        ▼
后端保存文件和图书元数据
        │
        ▼
前端请求 /api/v1/books
        │
        ▼
/books 展示分页书库
        │
        ▼
/books/read/:slug 加载对应 EPUB
```

图书封面通过 API 返回的 `cover_url` 加载，EPUB 文件通过后端提供的受保护资源地址访问。仓库不包含真实图书文件，避免把运行时大文件和可能受版权保护的内容提交到 Git。

前端 `src/data/books.ts` 中仍保留 `import.meta.glob('../assets/testepub/*.epub')` 和本地封面读取逻辑。这些目录只是开发阶段的 UI 预览 fallback；当 API 正常返回数据时，书库和阅读器优先使用后端资源。

### 2. epubjs 阅读流程

阅读器页面使用 `epubjs` 完成 EPUB 解析和渲染：

1. 从路由参数获取图书 slug；
2. 请求图书详情并取得 EPUB 地址；
3. 创建 `ePub(file)` 实例；
4. 读取 metadata、目录和 spine；
5. 在 viewer 容器中创建 rendition；
6. 应用阅读模式、主题和字体缩放；
7. 显示当前章节或恢复到上次阅读位置。

EPUB 内部的章节、资源和样式由 epubjs 管理，Vue 页面主要负责工具栏、目录、模式切换、错误状态和生命周期协调。

### 3. 分页与滚动模式

阅读器支持两种模式：

- 分页模式：通过 `rendition.next()` 和 `rendition.prev()` 在章节内容中前进或后退；
- 滚动模式：内容连续排列，监听阅读容器滚动位置，到达章节底部时自动加载下一章。

模式切换不会简单地从第一章重新开始。切换前会读取当前 CFI 或章节 href，切换 rendition 后优先使用 CFI 定位，CFI 无法恢复时再回退到 href 定位。

### 4. 阅读位置恢复

EPUB 使用 CFI（Canonical Fragment Identifier）表示内容位置。阅读器在翻页、章节跳转和模式切换前记录当前位置，并在重新创建 rendition 后恢复：

```text
当前 rendition
    │
    ├── location.start.cfi
    └── location.start.href
            │
            ▼
      ReaderAnchor
            │
            ▼
rendition.display(cfi)
            │
            └── 失败时 fallback 到 rendition.display(href)
```

CFI 优先保证精确位置，href 则作为跨 rendition 或 EPUB 兼容性不足时的章节级回退。

### 5. 目录、主题和字体

阅读器会读取 EPUB navigation 目录，并将条目转换为带层级的 `TocEntry`，用于目录面板展示和章节跳转。目录为空或解析失败时，目录按钮会保持不可用，不影响正文阅读。

阅读设置包括：

- 亮色 / 夜间主题；
- 字体缩放，当前使用 85% 到 130% 的范围；
- 分页 / 滚动模式；
- 工具栏和目录面板显示状态。

阅读偏好写入 localStorage，下次进入阅读器时可以继续使用上一次的阅读模式、主题和字体大小。

### 6. 生命周期和错误处理

EPUB 加载、metadata 读取、目录读取和章节显示都是异步操作。页面会区分加载、忙碌、错误和正常阅读状态，避免用户在模式切换或章节跳转期间重复操作。

当 CFI 定位、章节跳转或 EPUB 解析失败时，阅读器会尝试较弱的定位方式或显示可恢复的错误状态，而不是让整个 Vue 路由崩溃。组件卸载时会移除滚动监听、清空 viewer 容器并销毁 epubjs 实例，避免保留 iframe、事件监听器和 blob 封面 URL。

### 7. 开源部署注意事项

- 不要把真实 EPUB、用户上传图片、SQLite 数据库或生成的 ZIP 归档提交到仓库；
- `/uploads/images/` 可以作为公开图片代理；
- EPUB、普通文件和 ZIP 应继续通过后端鉴权下载，不要在 Nginx 中直接暴露整个 `uploads/` 目录；
- 生产环境需要配置正确的 `VITE_API_BASE_URL`、CORS 和后端文件目录；
- 如果使用外部对象存储，只需让后端返回可访问的文件 URL，阅读器的 epubjs 流程无需改变。
