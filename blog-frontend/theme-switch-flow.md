主题切换完整链路
================

1. 用户点击或拉动 NavBar 里的主题开关。

2. NavBar.vue 调用 ui.toggleTheme()。

3. ui.ts 先设置主题切换遮罩状态:
   themeTransitioning = true
   themeTransitionRevealStarted = false

4. App.vue 顶层显示 .theme-overlay 全屏毛玻璃遮罩。

5. ui.ts 等待 1 帧:
   await waitForNextFrames(1)

   这一步确保遮罩已经真正被浏览器 paint 到屏幕上。
   后续背景切换、CSS 变量切换、WebGL 纹理上传都会发生在遮罩之下。

6. ui.ts 切换 theme:
   theme = light / dark

7. theme 变化触发以下同步更新:
   - document.documentElement[data-theme] 更新
   - PageBackground 背景图切换
   - 普通毛玻璃 CSS 变量切换
   - 首页 6 个 LiquidGlass 的 props.theme 更新

8. 每个 LiquidGlass watcher 执行:
   applyThemePreset(theme)
   syncBackgroundWithTheme(theme)

9. syncBackgroundWithTheme() 先设置:
   visible = false

   这一步复用首次进入页面时 LiquidGlass 的透明起始状态。

10. LiquidGlass 从模块级图片缓存里拿当前主题对应背景图:
    dark  -> test3.jpg
    light -> test6.png

11. 每个 LiquidGlass 把自己的 WebGL 纹理上传任务塞入共享队列:
    enqueueTextureUpload(...)

12. liquidGlassQueue.ts 每帧只执行一个纹理上传任务。

    这样可以避免 6 个 LiquidGlass 面板在同一帧集中执行 gl.texImage2D(),
    降低主题切换时的主线程/GPU 同步压力。

13. 某个面板的上传任务执行时:
    - gl.texImage2D(...) 上传新背景纹理
    - bgLoaded = true
    - drawFrame()
    - visible = true

14. drawFrame() 必须在 visible=true 之前执行。

    原因: texImage2D 上传新纹理后,canvas 里仍然保留上一帧旧像素。
    如果立刻 visible=true,opacity 淡入最开始会闪一下旧纹理。
    先 drawFrame() 可以把新纹理真正画进 canvas,再开始淡入。

15. 当前面板获得 .liquid-glass-canvas--visible,class 后从 opacity:0 淡入到 opacity:1。

16. 共享队列里的第一个纹理任务完成后,waitForFirstTextureUploadSettled() resolve。

17. ui.ts 设置:
    themeTransitionRevealStarted = true

18. App.vue 的 .theme-overlay 开始淡出。

19. 剩余 LiquidGlass 面板继续按队列逐个上传纹理、逐个淡入。

20. 队列全部排空后,waitForTextureUploadQueueIdle() resolve。

21. ui.ts 再等待 2 帧:
    await waitForNextFrames(2)

    这一步给最后一帧 LiquidGlass 渲染和背景层 recomposite 留缓冲。

22. ui.ts 关闭主题切换状态:
    themeTransitioning = false
    themeTransitionRevealStarted = false

23. 主题切换流程结束。


当前效果设计
============

- 全屏毛玻璃遮罩一定先出现。
- 第一个 LiquidGlass 面板 ready 后遮罩开始退场。
- 剩余 LiquidGlass 面板继续逐个上传、逐个淡入。
- 每个 LiquidGlass 都复用首次进入页面的流程:
  visible=false -> 纹理上传 -> drawFrame -> visible=true
- 每个 LiquidGlass 面板的 WebGL 背景纹理会跟随主题切换。


如果要改背景图,需要改哪里
========================

当前背景图有两套用途,必须保持一致:

1. 页面真实背景图

   文件: src/components/PageBackground.vue

   当前导入:
   import darkBg from '@/assets/img/test3.jpg'
   import lightBg from '@/assets/img/test6.png'

   当前映射:
   light -> test6.png
   dark  -> test3.jpg

   如果要更换页面背景图,先改这里。

2. LiquidGlass WebGL 采样用背景图

   文件: src/components/LiquidGlass.vue

   当前导入:
   import darkBgUrl from '@/assets/img/test3.jpg'
   import lightBgUrl from '@/assets/img/test6.png'

   当前映射:
   const backgroundUrls = {
     dark: darkBgUrl,
     light: lightBgUrl,
   }

   如果只改 PageBackground.vue,页面背景会变,但 LiquidGlass 折射采样仍然用旧图。
   所以改主题背景时,PageBackground.vue 和 LiquidGlass.vue 这两处必须同步改。

3. 主题参数本身

   文件: src/assets/base.css

   用途: 普通毛玻璃变量,例如 --glass-bg、--glass-border、--glass-blur。

   如果背景图变亮/变暗很多,可能还要同步调整 :root[data-theme='light'] 里的 --glass-* 变量。

4. LiquidGlass 物理参数

   文件: src/components/LiquidGlass.vue

   位置: glassPresets.dark / glassPresets.light

   用途: 控制 WebGL 液态玻璃的厚度、折射率、边缘高光、覆盖色等。

如果换图后 LiquidGlass 太重、太亮或太暗,改这里。


迭代版本 v2: LazyLiquidGlass 与安全等待
=========================================

本节只记录 v1 之后新增的约束和修正,不覆盖前面的原始链路。

1. 归档页引入 LazyLiquidGlass。

   文件: src/components/LazyLiquidGlass.vue

   用途:
   - 只在卡片接近视口时挂载真实 LiquidGlass。
   - 不接近视口或等待名额时使用 fallback 玻璃样式。
   - 全局最多同时激活 6 个真实 LiquidGlass 实例。

2. LazyLiquidGlass 的限制是性能边界。

   归档页可能有大量文章卡片,不能让每张卡片都同时创建 WebGL canvas。
   因此 MAX_ACTIVE_LIQUID_GLASS 当前保持为 6。

   如果未来要调整这个数字,需要同时观察:
   - 主题切换时 gl.texImage2D 上传是否集中卡顿。
   - 横向滚动时主线程是否被多个 RAF 占满。
   - 低配设备是否出现 WebGL context 丢失。

3. LiquidGlass 新增 realtimeOffset。

   文件: src/components/LiquidGlass.vue

   默认值:
   realtimeOffset = false

   旧页面必须继续走默认值,避免每帧读取 getBoundingClientRect()。
   只有归档页横向滚动卡片需要显式开启 realtime-offset。

4. realtimeOffset 的工作方式。

   - 普通模式:滚动事件直接同步 canvasOffset,保持旧逻辑。
   - 实时模式:滚动事件只标记 dirty。
   - RAF render() 中仅当 realtimeOffset=true 且 dirty 时才同步 canvasOffset。

   这样归档页横向滚动时折射采样坐标能跟上位置变化,
   但不会在没有滚动/尺寸变化时每帧强制读取布局。

5. 主题切换等待逻辑更新。

   文件:
   - src/components/liquidGlassQueue.ts
   - src/stores/ui.ts

   v1 中 ui.ts 等待 waitForFirstTextureUploadSettled()。
   v2 改为等待 waitForNextTextureUploadSettled()。

6. 为什么要改等待逻辑。

   引入 LazyLiquidGlass 后,"液态玻璃开关开启" 不再等于
   "当前页面一定有真实 LiquidGlass 实例会立刻入队上传纹理"。

   例如:
   - 当前页面没有 LiquidGlass。
   - 当前页面只有 LazyLiquidGlass fallback。
   - 卡片还没进入 IntersectionObserver 范围。

   如果继续无条件等待旧的首个纹理完成信号,主题遮罩可能一直卡住。

7. waitForNextTextureUploadSettled() 的语义。

   - 记录调用时的 textureUploadGeneration。
   - 只等待调用之后产生的新批次首个纹理上传完成。
   - 如果没有新批次产生,超时后自动放行。

   这只是主题切换期间的安全兜底,平时不会运行。

8. v2 后的主题切换顺序。

   1. ui.toggleTheme() 拉起全屏遮罩。
   2. 等 1 帧,确保遮罩先 paint。
   3. 创建 firstTextureReady = waitForNextTextureUploadSettled()。
   4. 切换 theme。
   5. 已挂载的真实 LiquidGlass watcher 执行:
      applyThemePreset(theme)
      syncBackgroundWithTheme(theme)
   6. syncBackgroundWithTheme() 仍然执行:
      visible=false -> loadBgImage -> enqueueTextureUpload
   7. 队列仍然每帧只执行一个 gl.texImage2D。
   8. 上传任务内仍然必须保持:
      gl.texImage2D(...) -> bgLoaded=true -> drawFrame() -> visible=true
   9. firstTextureReady resolve 后遮罩开始退场。
   10. waitForTextureUploadQueueIdle() 等待队列排空。
   11. 再等 2 帧后关闭 themeTransitioning。

9. 如果没有真实 LiquidGlass 入队。

   firstTextureReady 会在超时后放行。
   主题遮罩正常退场,避免页面进入永久 transitioning 状态。

   这不会破坏已有 LiquidGlass 的防闪逻辑:
   只要真实 LiquidGlass 后续入队,它自己的上传任务仍会先 drawFrame(),再 visible=true。

10. 后续修改注意事项。

   - 不要把 realtimeOffset 默认值改成 true。
   - 不要移除 LazyLiquidGlass 的并发上限。
   - 不要让归档页每张卡片都直接挂载 LiquidGlass。
   - 不要把 drawFrame() 移到 visible=true 后面。
   - 不要绕过 enqueueTextureUpload() 直接批量上传纹理。
   - 不要让 ui.ts 无超时地等待一个可能不存在的纹理批次。
