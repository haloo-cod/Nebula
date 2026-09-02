# 液态玻璃开关机制

## 概述

前端通过 Pinia 的 `useUIStore` 统一控制液态玻璃。开启时使用共享 WebGL 渲染器，关闭时使用 CSS 毛玻璃 fallback。两种状态都保留相同的内容组件和布局容器，因此开关只改变表面效果，不改变页面内容。

相关实现：

- `src/stores/ui.ts`：保存开关和模糊强度，并持久化到 `localStorage`。
- `src/components/liquid-glass/LiquidGlass.vue`：单个 WebGL 玻璃实例的组件封装。
- `src/components/liquid-glass/liquidGlassRenderer.ts`：共享 WebGL context、shader、纹理和渲染循环。
- `src/components/liquid-glass/LazyLiquidGlass.vue`：大量卡片场景的视口懒加载和实例限流。
- `src/components/panels/PanelFallbackGlass.vue`：CSS 毛玻璃 fallback。

## 开关状态

```ts
const liquidGlassEnabled = ref(readStoredBoolean(LIQUID_GLASS_ENABLED_KEY, isDesktopOnInit))
const liquidGlassBlur = ref(readStoredLiquidGlassBlur())
```

持久化键：

- `blog-liquid-glass-enabled`
- `blog-liquid-glass-blur`

默认行为：

- 桌面端默认开启。
- 移动端默认关闭，除非用户之前已经保存过开启状态。
- `liquidGlassBlur` 的有效范围是 `0` 到 `12px`，默认值为 `0`。

导航栏设置面板通过 `NavBar.vue` 调用：

```ts
ui.setLiquidGlassEnabled(enabled)
ui.setLiquidGlassBlur(value)
```

## 组件切换模式

普通面板采用以下模式：

```html
<LiquidGlass v-if="ui.liquidGlassEnabled">
  <ContentPanel />
</LiquidGlass>

<PanelFallbackGlass v-else>
  <ContentPanel />
</PanelFallbackGlass>
```

`LiquidGlass` 负责 WebGL 材质和画布，内容组件负责文字、图片和交互。`PanelFallbackGlass` 负责半透明背景、`backdrop-filter`、边框和阴影。

## 使用范围

当前开关已覆盖首页、博客、图书、归档、展览、说说、图片、友链、藏宝阁、自习室和关于页中的主要玻璃面板。

### 首页

首页位于 `src/views/index/index.vue`，使用非懒加载 `LiquidGlass`。当前首页面板数量有限，并且首屏通常可见，因此直接挂载实例：

- 个人资料面板
- 数据看板
- 图片轮播
- 日历
- 数字时钟
- 文章轮播
- 说说轮播

首页的外层 grid/flex 容器负责尺寸和定位，`LiquidGlass` 或 `PanelFallbackGlass` 负责填满容器。首页 fallback 使用 `static-blur`，用页面背景副本生成模糊层，减少动态 `backdrop-filter` 重采样。

### 图书、博客和其他列表页

图书页、博客页、友链页、图片页、展览页等列表卡片一般直接使用：

```html
<LiquidGlass v-if="ui.liquidGlassEnabled">
  <!-- 内容卡片，开态应保持透明 -->
</LiquidGlass>
<PanelFallbackGlass v-else>
  <!-- 同一份内容卡片 -->
</PanelFallbackGlass>
```

当内容卡片由 `LiquidGlass` 包裹时，卡片自身不要重复设置背景、边框、阴影或 `backdrop-filter`，否则会削弱 WebGL 材质效果。

### 归档页和说说页

这类页面可能同时存在大量卡片，使用 `LazyLiquidGlass`：

- `IntersectionObserver` 判断卡片是否接近视口。
- 只有接近视口且获得名额时才挂载 `LiquidGlass`。
- 未接近视口、未开启开关或等待名额时显示 fallback 内容。
- 全局最多同时激活 `6` 个真实液态玻璃实例。

不要将归档页的大量卡片改成直接挂载 `LiquidGlass`，否则会增加 canvas、纹理和渲染循环压力。

### 特殊布局

部分抽屉、时间轴卡片或绝对定位卡片需要自身控制根节点的布局属性。这类组件可以继续保留本地容器样式，但玻璃表面应优先复用 `LiquidGlass` 或 `PanelFallbackGlass`，不要复制出第三套公共表面参数。

## WebGL 关闭时的行为

关闭开关不会卸载页面背景，也不会影响页面内容。普通组件切换到 `PanelFallbackGlass`；`LazyLiquidGlass` 释放自己的激活名额。

CSS fallback 的公共表面定义位于 `src/components/panels/PanelFallbackGlass.vue`，全局 CSS 变量位于 `src/assets/base.css`：

- `--glass-bg`
- `--glass-bg-subtle`
- `--glass-bg-strong`
- `--glass-border`
- `--glass-highlight`
- `--glass-shadow`
- `--glass-blur`

如果只需要调整关闭状态的视觉效果，优先修改 `PanelFallbackGlass.vue` 或 `base.css`，不要修改 WebGL shader 参数。

## 性能边界

共享渲染器已经包含以下约束：

- 全站共享一个 WebGL context。
- 图片纹理按 URL 缓存并可在启动时预热。
- 无活跃涟漪时降低渲染频率。
- 滚动期间提高渲染频率。
- 归档类页面最多激活 6 个 `LiquidGlass`。
- 视频背景复用 `PageBackground.vue` 中真实显示的 video 元素。
- 处理 WebGL context lost/restored。

修改实例上限、纹理上传或首帧逻辑前，应使用 `PerfMonitor.vue` 观察真实设备上的 FPS、draw calls、纹理上传和 context 状态。
