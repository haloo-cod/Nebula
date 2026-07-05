# 归档页（Archive）架构文档

## 概述

归档页是一个横向时间轴风格的博客文章列表。核心交互是滚动查看 timeline 上按时间排列的文章卡片，点击进入详情。

---

## 文件结构

```
src/views/archive/
├── archive.vue              # 主页面：时间轴 + 卡片容器
├── ArchivePostCard.vue      # 文章卡片内容组件（纯内容片段）
└── ArchiveTreePoster.vue    # 备选树状海报视图（独立页面）

src/components/
├── LazyLiquidGlass.vue      # 液态玻璃懒加载包装（开态使用）
└── LiquidGlass.vue          # WebGL 液态玻璃本体
```

---

## 架构分层

```
PageBackground (全屏背景图)
  └── .page-wrap (z-index:10 的定位容器)
        └── .timeline-wrap / .post-rise-inner (入场动画容器)
              └── .timeline-viewport (overflow-x:auto 横向滚动)
                    └── .timeline-stage (position:relative 舞台)
                          ├── SVG 河流 (.river-svg, position:absolute)
                          │     ├── 河流路径 + 渐变发光
                          │     ├── 节点圆点 + 连接线
                          │     └── 流动粒子动画
                          │
                          └── RouterLink × N (.archive-link, position:absolute)
                                └── 关态: .archive-panel (毛玻璃)
                                    开态: LazyLiquidGlass → LiquidGlass
```

**关键点：** SVG 河流和文章卡片是兄弟节点，都在 `.timeline-stage` 内。卡片通过 `z-index:5` 确保在河流之上。

---

## 河流系统（SVG Timeline）

### 布局参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `cardW` | 280px | 卡片宽度 |
| `cardH` | 310px | 卡片高度 |
| `cardGap` | 40px | 卡片间距 |
| `connLen` | 18px | 节点到卡片的连线长度 |
| `riverAmplitude` | 46px | 河流振幅 |

### 河流波形

```ts
function waveY(t: number): number {
  return (
    Math.sin(t * Math.PI * 1.5) * riverAmplitude * 0.6 +
    Math.sin(t * Math.PI * 3.7 + 0.8) * riverAmplitude * 0.3 +
    Math.sin(t * Math.PI * 6.1 + 2.3) * riverAmplitude * 0.15
  )
}
```

三个正弦波叠加，分别产生主导波纹、中频扰动和高频细节。
**此函数被 `riverPath` 和 `nodes` 共用，避免重复计算。**

### 河流渲染层

| 层 | 元素 | 视觉效果 |
|----|------|----------|
| 外层大发光 | `.river-glow-outer` | 36px 宽，`blur(20px)` |
| 中层发光 | `.river-glow-mid` | 20px 宽，`blur(10px)` |
| 内层发光 | `.river-glow-inner` | 10px 宽，`blur(5px)` |
| 主曲线 | `.river-path` | 6px 宽，`url(#river-grad)` 渐变 + `drop-shadow` |

### 节点与连接线

- 每个文章对应一个节点（圆点 + 光晕）
- 节点通过虚线（`.conn-line`）连接到卡片
- 单数卡片在上，双数在下

### 流动粒子

三个圆形粒子使用 `<animateMotion>` 沿河流路径以不同速度循环移动。

---

## 卡片系统

### 关态结构

```html
<RouterLink class="archive-link" style="position:absolute; ...">
  <div class="archive-panel">      <!-- 毛玻璃表面 + 卡片容器 -->
    <ArchivePostCard :post="post" />
  </div>
</RouterLink>
```

归档页关态**不依赖** `PanelFallbackGlass`，因为 `.archive-panel` 需要独立的 `display:flex`、`padding`、`position:relative` 语义来充当卡片根容器。

### 开态结构

```html
<RouterLink class="archive-link">
  <LazyLiquidGlass>                <!-- 懒加载：最多 6 个并发 WebGL -->
    <LiquidGlass>                  <!-- WebGL 液态玻璃着色器 -->
      <ArchivePostCard :post="post" />
    </LiquidGlass>
  </LazyLiquidGlass>
</RouterLink>
```

### ArchivePostCard 组件

纯内容片段，多根节点模板：

```html
<template>
  <div class="archive-card__media">   <!-- 封面图 + 日期 -->
  <div class="archive-card__body">    <!-- 标题 + 摘要 + 分类标签 -->
</template>
```

- 独立管理 `categoryColors` 映射和 `formatDate`、`catColorKey` 工具函数
- 不承担任何表面玻璃样式

### 状态切换逻辑

```html
<div v-if="!ui.liquidGlassEnabled" class="archive-panel">   <!-- 关态毛玻璃 -->
<LazyLiquidGlass v-else>                                      <!-- 开态液态玻璃 -->
```

`liquidGlassEnabled` 默认 `false`（store: `readStoredBoolean(LIQUID_GLASS_ENABLED_KEY, false)`），
用户可通过 NavBar 切换并持久化到 localStorage。

---

## CSS 关键修复点

### 1. 动画不创建持久 stacking context

**问题：** `post-rise-inner` 动画使用 `transform: translateY(0)` 作为终点，
CSS 规范中**任何非 `none` 的 `transform` 都会创建独立 GPU 渲染层（stacking context）**，
导致卡片内的 `backdrop-filter` 无法访问背景图。

**修复：**
```css
@keyframes contentRise {
  from { transform: translateY(40px); }
  to   { transform: none; }          /* 不是 translateY(0) */
}
```

`transform: none` 明确移除 transform，不创建持续性 stacking context。

### 2. 卡片 z-index 提层

SVG 河流元素的 `filter: blur()` 也会创建 stacking context。
给 `.archive-link` 加 `z-index: 5` 确保卡片始终在河流过滤层之上。

### 3. 面板独立渲染层

`.archive-panel` 设置 `position: relative`，为 `backdrop-filter` 创建明确的渲染上下文。

---

## 已知注意事项

- `LazyLiquidGlass` 的透明 fallback 是**硬编码的 `background: transparent`**。
  即使 `liquidGlassEnabled=true`，如果卡片不在视口内或未拿到 WebGL 槽位，
  fallback 不会提供任何毛玻璃效果。这正是关态走独立 `.archive-panel` 的原因。
- 动画已移除 `opacity` 关键帧，避免 HMR 或 re-mount 时出现透明闪烁。
- `liquidGlassEnabled` 通过 `readStoredBoolean` 读取 localStorage，刷新后保持用户设置。

---

## 依赖关系

```
archive.vue
  ├── @/components/PageBackground.vue
  ├── @/components/LazyLiquidGlass.vue
  │     └── @/components/LiquidGlass.vue
  ├── @/stores/ui (useUIStore)
  ├── @/data/posts (getPosts)
  └── ./ArchivePostCard.vue
        └── @/types (Post)
```
