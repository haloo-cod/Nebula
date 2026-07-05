# 首页 & 图书页液态玻璃开关机制

## 概述

首页和图书页使用同一套模式：根据 `ui.liquidGlassEnabled` 的值，在 **WebGL 液态玻璃** 和 **CSS 毛玻璃** 之间切换。归档页现在也遵循这套语义。

---

## 开关判断

全站统一从 Pinia store 读取：

```ts
// src/stores/ui.ts
const liquidGlassEnabled = ref(readStoredBoolean(LIQUID_GLASS_ENABLED_KEY, false))
```

- `true`：走 WebGL `LiquidGlass` 增强
- `false`：走 CSS 毛玻璃 fallback
- 用户通过 NavBar 切换，值持久化到 `localStorage`

---

## 首页 (index.vue)

### 模板模式

```html
<LiquidGlass v-if="ui.liquidGlassEnabled" ...>
  <ContentPanel />              <!-- 内容组件 -->
</LiquidGlass>

<PanelFallbackGlass v-else>    <!-- 共享毛玻璃壳组件 -->
  <ContentPanel />
</PanelFallbackGlass>
```

首页有 **7 个面板** 使用这套模式：

| 位置 | 内容组件 | CSS 容器 |
|------|----------|----------|
| 左上 | `HomeProfilePanel` | `left-panel-glass` |
| 右上 | `DataDashboard` | `right-panel-glass` |
| 左下 | `Carousel` | `bottom-left` |
| 右下上 | `CalendarPanel` | `bottom-right-top` |
| 右下中 | `DigitalClockPanel` | `bottom-right-middle` |
| 右下下 ×2 | 空占位 | `bottom-right-bottom-inner` |

### 关键点

- **首页用 `LiquidGlass`（非懒加载）**，因为它渲染的面板数量有限且始终可见
- 开态时不依赖任何过渡组件，`LiquidGlass` 直接画 WebGL 效果
- 关态统一的 `PanelFallbackGlass` 组件提供 CSS 毛玻璃表面

### CSS 容器层

```html
<div class="bottom-left">           <!-- 尺寸 + 定位 -->
  <LiquidGlass class="panel-liquid-glass">  <!-- flex:1 填满 -->
    <Carousel />
  </LiquidGlass>
  <PanelFallbackGlass v-else>      <!-- flex:1 填满 -->
    <Carousel />
  </PanelFallbackGlass>
</div>
```

外层容器（如 `bottom-left`）负责尺寸和定位，内层 `LiquidGlass` / `PanelFallbackGlass` 通过 `flex:1` 填满。

### PanelFallbackGlass 参数

```css
.panel-fallback-glass {
  flex: 1;
  width: 100%;
  height: 100%;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.24),
    inset 0 0 20px rgba(255, 255, 255, 0.06),
    0 8px 28px rgba(0, 0, 0, 0.18);
  overflow: hidden;
}
```

---

## 图书页 (books.vue)

### 模板模式

```html
<RouterLink class="book-link">
  <LiquidGlass v-if="ui.liquidGlassEnabled" class="book-glass" ...>
    <article class="book-card book-card--liquid">    <!-- 开态：透明内容 -->
      <div class="book-cover" ... />
      <div class="book-info" ... />
    </article>
  </LiquidGlass>

  <PanelFallbackGlass v-else tag="article" class="book-card book-card-fallback">
    <div class="book-cover" ... />                   <!-- 关态：直接内容 -->
    <div class="book-info" ... />
  </PanelFallbackGlass>
</RouterLink>
```

### 关键点

- **图书页用非懒加载 `LiquidGlass`**，因为每页最多 16 本书，无明显性能压力
- `PanelFallbackGlass` 通过 `tag="article"` 直接变成 `<article>` 根元素，外层类 `book-card` 提供布局
- `book-card` 负责 `display:flex`、`padding`、`border-radius` 等卡片容器语义
- `PanelFallbackGlass` 负责毛玻璃表面（`background`、`backdrop-filter`、`border`、`box-shadow`）

### 开态透明处理

```css
.book-card--liquid {
  border: none;
  background: transparent;
  backdrop-filter: none;
  box-shadow: none;
}
```

开态时 `.book-card--liquid` 清空所有背景/边框/阴影，
让外层 `LiquidGlass` 的 WebGL 效果完整接管视觉。

### PanelFallbackGlass 作为卡片根

```html
<!-- 编译后的 DOM -->
<article class="panel-fallback-glass book-card book-card-fallback">
  <!-- 内容 -->
</article>
```

`panel-fallback-glass` 提供毛玻璃表面，
`book-card` 提供 flex 布局 + 内边距，
`book-card-fallback` 提供 hover 过渡。

这是首页和图书页关态视觉一致的根本原因：**同一个组件、同一套表面参数**。

---

## 首页 vs 图书页 vs 归档页 对比

| | 首页 | 图书页 | 归档页 |
|---|---|---|---|
| 开态组件 | `LiquidGlass` | `LiquidGlass` | `LazyLiquidGlass` |
| 关态组件 | `PanelFallbackGlass` | `PanelFallbackGlass` | 本地 `.archive-panel` |
| 懒加载 | 否 | 否 | 是（最多 6 个 WebGL） |
| 卡片容器 | 外层容器 | `book-card` 类 | `.archive-panel` 类 |
| 毛玻璃参数 | 共享组件 | 共享组件 | 本地 CSS（与共享组件参数一致） |
| 内容组件 | `HomeProfilePanel` 等 | 内联 | `ArchivePostCard` |

---

## 为什么归档页不用 PanelFallbackGlass

归档页的卡片是 **280×310px 的绝对定位元素**，放在横向滚动的时间轴舞台上。
与首页/图书页的静态 grid/flex 布局不同，归档卡片需要：

1. **`display: flex; flex-direction: column`** 作为卡片根容器
2. **`padding: 0.45rem`** 匹配卡片内容布局
3. **`position: relative`** 为 `backdrop-filter` 创建渲染层
4. **`z-index: 5`** 提层超越 SVG 河流过滤层

这些布局语义是归档页特有的，不应塞进共享组件 `PanelFallbackGlass`。
归档页的 `.archive-panel` 毛玻璃参数与 `PanelFallbackGlass` **完全一致**，
只是额外叠加了归档特有的布局属性。
