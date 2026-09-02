# 主题与液态玻璃切换流程

## 当前数据来源

主题和背景不再由页面组件分别硬编码。统一数据流如下：

```text
NavBar
  → useUIStore.toggleTheme()
  → theme
  → currentBackground / currentBgUrl
  → PageBackground + LiquidGlass
```

`src/stores/ui.ts` 按以下维度选择背景：

- 主题：`dark` / `light`
- 设备：`desktop` / `mobile`
- 当前分组中的背景索引

背景列表初始来自 `src/data/backgrounds.ts` 的本地静态资源；`App.vue` 挂载后会从后端加载背景列表并替换对应分组。每个背景项保留 `mediaType`、`posterUrl`、`mimeType` 和 `fileSize` 等媒体元数据。

## 主题切换链路

1. 用户点击 `NavBar.vue` 的主题按钮，或完成主题开关的拖拽操作。

2. `NavBar.vue` 调用 `ui.toggleTheme()`。

3. `useUIStore.toggleTheme()` 设置：

   ```ts
   themeTransitioning = true
   themeTransitionRevealStarted = false
   ```

4. `App.vue` 显示全屏 `.theme-overlay`。遮罩使用半透明底色和 `backdrop-filter`，暂时遮住背景、CSS 变量切换和 WebGL 更新。

5. store 等待一帧，确保遮罩已经被浏览器绘制。

6. store 修改 `theme`。主题 watcher 同步：

   - `document.documentElement[data-theme]`
   - 普通 CSS 毛玻璃变量
   - `PageBackground` 的背景资源
   - 所有 `LiquidGlass` 的主题预设

7. `PageBackground.vue` 通过 `currentBackground` 切换显示资源。图片和视频都会先预热，资源准备完成前继续显示旧背景，避免切换瞬间黑屏。

8. 每个 `LiquidGlass.vue` 监听到主题或背景 URL 变化后：

   - 选择桌面端或移动端主题预设。
   - 检查共享纹理缓存。
   - 缓存未命中时加载图片或预加载视频纹理。
   - 更新纹理宽高比和实例背景 URL。
   - 将实例重新标记为可渲染。

9. 如果需要重新 reveal，组件会先设置 `visible = false`，并注册首帧回调。

10. 共享渲染器完成纹理准备和首帧绘制后，执行顺序必须是：

    ```text
    上传新纹理
      → drawFrame()
      → visible = true
    ```

    先绘制再显示，避免 canvas 中残留上一主题的像素导致闪烁。

11. 第一个新的纹理上传完成后，store 设置 `themeTransitionRevealStarted = true`，全屏遮罩开始淡出。

12. 其他玻璃实例继续由共享渲染器处理并逐步显示。等待纹理上传阶段结束后再等待两帧，给背景层重合成和最后一帧渲染留出缓冲。

13. store 清理：

    ```ts
    themeTransitioning = false
    themeTransitionRevealStarted = false
    ```

## 没有液态玻璃实例时

液态玻璃开关开启并不代表当前页面一定存在正在渲染的 `LiquidGlass`。例如：

- 当前页面只有 CSS 面板。
- `LazyLiquidGlass` 卡片还没有接近视口。
- 当前页面没有任何玻璃组件。

因此主题切换等待纹理就绪时必须有超时兜底。`liquidGlassQueue.ts` 的 `waitForNextTextureUploadSettled()` 用于兼容这个流程：没有新的纹理批次时，超时后正常放行，不能让主题遮罩永久停留。

## 背景纹理与页面背景的一致性

页面背景和 WebGL 纹理都从 `useUIStore.currentBackground` 读取，不要在 `PageBackground.vue` 或 `LiquidGlass.vue` 中重新维护主题背景 URL 映射。

新增或替换背景时应检查：

1. `src/data/backgrounds.ts` 的本地 fallback 分组。
2. 后端背景列表接口返回的 `theme`、`device` 和媒体元数据。
3. `PageBackground.vue` 对图片、视频、poster 和 reduced-motion 的处理。
4. `LiquidGlass.vue` 对 `isVideoBackground()` 的判断。
5. 必要时调整 `src/assets/base.css` 的普通 CSS 毛玻璃变量。
6. 必要时调整 `LiquidGlass.vue` 中的 `glassPresets` 和 `mobileGlassPresets`。

视频背景尤其不能丢失 `mediaType` 或 MIME 信息，否则液态玻璃可能把视频当成图片加载。页面上真实显示的 video 会通过 `bindVideoElement()` 复用给 WebGL 渲染器，避免隐藏 video 和页面背景播放进度不一致。

## LiquidGlass 参数入口

`src/components/liquid-glass/LiquidGlass.vue` 的 props 可以覆盖部分默认参数：

- `cornerRadius`
- `blurRadius`
- `glassThickness`
- `ior`
- `highlightWidth`
- `overlayColor`
- `allowReveal`
- `realtimeOffset`
- `theme`
- `rippleTrail`
- `rippleStrength`
- `rippleRadius`
- `rippleDuration`

默认情况下 `realtimeOffset` 必须保持 `false`。只有需要在横向滚动时实时跟随位置的归档卡片才显式开启它，否则会让每帧布局读取扩大。

## 修改时必须保留的约束

- 不要在页面组件中重新硬编码 dark/light 背景 URL。
- 不要把所有归档卡片改成直接挂载 `LiquidGlass`。
- 不要移除 `LazyLiquidGlass` 的最多 6 个激活实例限制。
- 不要把 `drawFrame()` 放到 `visible = true` 之后。
- 不要绕过共享纹理缓存批量上传大量背景。
- 不要让主题切换无限等待不存在的纹理批次。
- 不要把 `realtimeOffset` 默认改成 `true`。
- 修改 shader、纹理、实例注册或 context 恢复逻辑后，应检查 `PerfMonitor.vue` 的指标。
