# 液态玻璃圆角抗锯齿

## 背景

液态玻璃的视觉内容由共享 WebGL 渲染器绘制。每个 `LiquidGlass` 组件拥有一个可见 canvas，渲染器使用 fragment shader 在矩形 quad 内通过圆角 SDF 计算玻璃形状。

相关文件：

- `src/components/liquid-glass/liquidGlassRenderer.ts`
- `src/components/liquid-glass/LiquidGlass.vue`

## 原始问题

圆角边界最初使用二值裁剪：

```glsl
float distance = sdRoundedBoxSmooth(...);
if (distance > 0.001) {
    discard;
}
```

这种做法只判断 fragment 在边界内还是边界外，不计算边界覆盖率。圆角曲线落在像素之间时，像素只能完整显示或完整丢弃，因此会出现台阶状锯齿。

桌面端的低渲染缩放会进一步放大这个问题。渲染器会根据 GPU 能力将部分集成显卡的 `renderScale` 设置为 `0.65`，canvas 以较低的实际像素尺寸绘制后再放大到 CSS 尺寸，圆角边缘因此更容易变粗糙。

## 当前抗锯齿方案

### 1. 使用 SDF 距离生成边缘覆盖率

shader 仍然使用 `sdRoundedBoxSmooth()` 计算圆角 SDF 距离，但不再只依赖二值 `discard`。当前边缘处理为：

```glsl
float distance = sdRoundedBoxSmooth(...);
float edgeWidth = max(fwidth(distance), 0.75);
float shapeAlpha = 1.0 - smoothstep(0.0, edgeWidth, distance);
if (shapeAlpha <= 0.0) {
    discard;
}
```

含义如下：

- `distance < 0`：fragment 在圆角形状内部，覆盖率接近 `1`。
- `distance = 0`：fragment 位于形状边界。
- `distance > 0`：fragment 位于外部，覆盖率逐渐降低到 `0`。
- `fwidth(distance)`：估算当前屏幕像素范围内 SDF 距离的变化量，作为自适应边缘宽度。
- `smoothstep()`：在边界附近生成平滑 alpha，而不是突然丢弃 fragment。

最终颜色会乘以形状覆盖率：

```glsl
vec4 shadedColor = mix(...);
gl_FragColor = vec4(shadedColor.rgb, shadedColor.a * shapeAlpha);
```

这样 GPU 可以对边缘像素进行混合，圆角轮廓会比硬裁剪平滑得多。

### 2. 兼容 WebGL 1

项目使用 WebGL 1。`fwidth()` 不属于 GLSL ES 1.00 的基础函数，需要使用可选扩展：

```glsl
#extension GL_OES_standard_derivatives : enable
```

渲染器初始化时会检查：

```ts
const supportsDerivatives = Boolean(gl.getExtension('OES_standard_derivatives'))
```

支持扩展时，编译包含 `fwidth()` 的 shader；不支持时，初始化代码会移除扩展声明，并将边缘宽度表达式替换成固定的 `1.25` 物理像素：

```glsl
float edgeWidth = 1.25;
```

这套降级很重要：抗锯齿能力不足时只牺牲边缘质量，不应因为 shader 编译失败而让整个液态玻璃消失。

不要直接在 shader 中无条件使用 `fwidth()`，否则在未启用扩展的 WebGL 1 浏览器中会出现：

```text
'fwidth' : no matching overloaded function found
```

随后 fragment shader 编译失败，渲染器无法初始化，所有 LiquidGlass 实例都会没有绘制结果。

## 物理像素单位

canvas 的实际尺寸不是 CSS 尺寸，而是：

```text
CSS 尺寸 × devicePixelRatio × renderScale
```

`LiquidGlass.vue` 使用 `toCanvasPixels()` 将与画布几何相关的参数转换到同一单位：

```ts
function toCanvasPixels(value: number): number {
  return value * (window.devicePixelRatio || 1) * getRenderScale()
}
```

目前需要转换的参数包括：

- `cornerRadius`
- `highlightWidth`

转换后的值分别写入 `u_cornerRadius` 和 `u_highlightWidth` 对应的 uniform。这样 shader 中的 `u_glassSize`、圆角半径和高光宽度都使用 canvas 物理像素，避免 DPR 不同导致边缘比例不一致。

涟漪半径也需要使用物理像素，目前由 `updateTrailUniforms()` 按同样的 DPR 和 `renderScale` 进行换算。

## 初始化顺序

`registerInstance()` 会触发共享 WebGL 渲染器初始化，而 `renderScale` 也是在 WebGL 初始化时检测的。因此组件必须按照以下顺序执行：

```text
获取 2D context
  → registerInstance()
  → initUniforms()
  → syncCanvasSize()
```

不能在 `registerInstance()` 之前计算依赖 `getRenderScale()` 的 canvas 参数，否则首次挂载时可能仍使用默认的 `renderScale = 1`，导致集成显卡设备上的尺寸和圆角单位不一致。

## CSS 圆角同步

WebGL shader 负责实际玻璃形状，CSS 容器负责裁剪和合成。两者使用同一个 `cornerRadius`：

```vue
:style="{ '--liquid-glass-corner-radius': `${props.cornerRadius}px` }"
```

```css
.liquid-glass {
  border-radius: var(--liquid-glass-corner-radius, 16px);
  overflow: hidden;
}

.liquid-glass-canvas {
  border-radius: inherit;
}
```

这样可以避免 shader 圆角和 CSS 外层裁剪使用不同半径。CSS 半径使用 CSS 像素即可，因为它由浏览器负责处理；shader 半径则必须使用 canvas 物理像素。

## 排查方法

出现桌面端圆角锯齿时，按以下顺序检查：

1. 打开 `PerfMonitor.vue`，查看当前 `renderScale`。
2. 确认浏览器控制台没有 shader compile error。
3. 检查 `devicePixelRatio`、canvas 实际宽高和 CSS 显示宽高。
4. 暂时固定 `renderScale = 1`，确认问题是否因低分辨率放大而加重。
5. 对比 CSS fallback 和 WebGL 版本的圆角。
6. 检查 `cornerRadius` 是否同时作用于 CSS 容器和 shader uniform。
7. 如果修改了 shader，确认 WebGL 1 扩展声明和不支持扩展时的降级逻辑仍然存在。

## 修改约束

- 不要删除 `GL_OES_standard_derivatives` 的兼容处理。
- 不要在 WebGL 1 中无条件调用 `fwidth()`。
- 不要恢复只使用硬 `discard` 的圆角裁剪。
- 不要把 CSS 像素参数和 canvas 物理像素参数混用。
- 不要在 `registerInstance()` 之前读取依赖 `renderScale` 的尺寸参数。
- 不要为了修圆角而取消共享 WebGL context 或实例限流。
- 修改后至少运行 `pnpm type-check`、`pnpm test:unit --run` 和 `pnpm build`。

## 当前验证

当前实现已验证：

- WebGL 1 shader 可以通过 `OES_standard_derivatives` 使用 `fwidth()`。
- 不支持该扩展时使用固定物理像素边缘宽度继续渲染。
- 圆角和高光宽度会按 DPR、`renderScale` 转换。
- CSS 容器和 canvas 使用相同的 CSS 圆角。
- `pnpm type-check` 通过。
- `pnpm test:unit --run` 通过。
- `pnpm build` 通过。
