<template>
  <div
    class="liquid-glass"
    ref="containerRef"
    :style="{ '--liquid-glass-corner-radius': `${props.cornerRadius}px` }"
    :class="{ 'liquid-glass--css-fallback': rendererFailed }"
  >
    <canvas
      ref="canvasRef"
      class="liquid-glass-canvas"
      :class="{ 'liquid-glass-canvas--visible': visible }"
    ></canvas>
    <div class="liquid-glass-content">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 液态玻璃组件 — 使用共享 WebGL 渲染器
 *
 * 组件自身不创建 WebGL 上下文,而是向全局共享渲染器注册自己。
 * 渲染器在单一 RAF 循环中为所有实例渲染,结果通过 drawImage 拷贝到每个实例的 2D canvas。
 * 这样全站只有 1 个 WebGL 上下文,永远不会触发浏览器的上下文数量限制。
 */
import { ref, watch, onMounted, onBeforeUnmount, onUnmounted, computed } from 'vue'
import { useUIStore } from '@/stores/ui'
import {
  registerInstance,
  unregisterInstance,
  markInstanceReady,
  setInstanceBackground,
  setInstanceFirstRenderCallback,
  onContextLost,
  onContextRestored,
  offContextCallbacks,
  loadImage,
  uploadTexture,
  preloadVideoTexture,
  hasTexture,
  getTextureAspect,
  getRenderScale,
  MAX_TRAIL_POINTS,
  type GlassUniforms,
} from '@/components/liquid-glass/liquidGlassRenderer'
import { isVideoBackground } from '@/data/backgrounds'

const containerRef = ref<HTMLElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)
const visible = ref(false)
const rendererFailed = ref(false)
const ui = useUIStore()

const emit = defineEmits<{
  /** 液态玻璃已完成当前背景下的首帧绘制。 */
  'render-ready': []
}>()

const props = withDefaults(
  defineProps<{
    cornerRadius?: number
    blurRadius?: number
    glassThickness?: number
    ior?: number
    highlightWidth?: number
    overlayColor?: [number, number, number]
    allowReveal?: boolean
    realtimeOffset?: boolean
    theme?: 'light' | 'dark'
    rippleTrail?: boolean
    rippleStrength?: number
    rippleRadius?: number
    rippleDuration?: number
  }>(),
  {
    allowReveal: true,
    cornerRadius: 32,
    blurRadius: 0.0,
    glassThickness: 41,
    ior: 1.1,
    highlightWidth: 3.5,
    overlayColor: () => [0.85, 0.9, 1.0] as [number, number, number],
    theme: 'dark',
    realtimeOffset: false,
    rippleTrail: false,
    rippleStrength: 0.34,
    rippleRadius: 66,
    rippleDuration: 1100,
  },
)

type LiquidGlassTheme = 'light' | 'dark'

/** 当前主题对应的背景图 URL（从 store 读取用户选择） */
const currentBgUl = computed(() => ui.currentBgUrl)
const currentBackground = computed(() => ui.currentBackground)

// 两套液态玻璃参数预设
const glassPresets = {
  dark: {
    // 玻璃厚度：越大折射位移越明显；暗色桌面端适当降低，避免背景被拉扯过度。
    glassThickness: 38,
    // 折射率：1.0 接近无折射，数值越高边缘弯曲越强。
    ior: 1.2,
    // 高光边缘宽度（像素）：控制玻璃边缘亮边的宽窄。
    highlightWidth: 4.0,
    // 额外背景模糊半径；0 表示不增加模糊。
    blurRadius: 0.0,
    // 叠加色（RGB 0~1）：控制玻璃本身的染色，过高会让面板发灰发白。
    overlayColor: [0.2, 0.26, 0.32] as [number, number, number],
    // 法线强度：越大立体高光越强，也会放大折射变化。
    normalStrength: 6.5,
    // 折射位移缩放：控制法线造成的 UV 偏移，暗色主题先收敛到 0.75。
    displacementScale: 0.68,
    // 边缘高度过渡宽度：越大边缘过渡越柔和。
    heightTransitionWidth: 10.0,
    // 圆角 SDF 平滑度：越大边缘越平滑，但细节会减少。
    sminSmoothing: 20.0,
  },
  light: {
    // 亮色背景本身更容易把材质“冲白”，因此减少白色边缘和叠加色，
    // 同时提高折射/法线强度，让面板仍然保留清晰的体积感。
    // 玻璃厚度：控制整体折射深度。
    glassThickness: 40,
    // 折射率：亮色背景使用较低值，减少泛白和边缘变形。
    ior: 1.1,
    // 高光边缘宽度（像素）。
    highlightWidth: 3.0,
    // 额外背景模糊半径。
    blurRadius: 0.5,
    // 叠加色（RGB 0~1）：亮色主题建议保持低饱和，避免白底泛白。
    overlayColor: [0.42, 0.5, 0.62] as [number, number, number],
    // 法线强度：决定高光和立体感。
    normalStrength: 8.0,
    // 折射位移缩放：决定背景纹理偏移量。
    displacementScale: 1.0,
    // 边缘高度过渡宽度。
    heightTransitionWidth: 8.0,
    // 圆角 SDF 平滑度。
    sminSmoothing: 20.0,
  },
}

// 移动端专属预设:小面板上折射/叠加色/法线强度增大,补偿面积缩小带来的"薄感"
const mobileGlassPresets = {
  dark: {
    // 移动端面板较小，需要保留一定厚度，但比原值降低折射强度。
    glassThickness: 60,
    // 移动端暗色主题折射率。
    ior: 1.16,
    // 移动端边缘高光宽度（像素）。
    highlightWidth: 5.0,
    // 额外背景模糊半径。
    blurRadius: 0.0,
    // 叠加色（RGB 0~1）：移动端暗色面板的基础染色。
    overlayColor: [0.25, 0.32, 0.4] as [number, number, number],
    // 移动端法线强度：保留小面板的体积感。
    normalStrength: 8.5,
    // 移动端折射位移缩放。
    displacementScale: 0.95,
    // 边缘高度过渡宽度。
    heightTransitionWidth: 10.0,
    // 圆角 SDF 平滑度。
    sminSmoothing: 20.0,
  },
  light: {
    // 移动端亮色主题玻璃厚度。
    glassThickness: 38,
    // 移动端亮色主题折射率。
    ior: 1.1,
    // 移动端边缘高光宽度（像素）。
    highlightWidth: 3.5,
    // 额外背景模糊半径。
    blurRadius: 0.5,
    // 叠加色（RGB 0~1）：移动端亮色面板的基础染色。
    overlayColor: [0.65, 0.7, 0.8] as [number, number, number],
    // 法线强度。
    normalStrength: 7.0,
    // 折射位移缩放。
    displacementScale: 1.0,
    // 边缘高度过渡宽度。
    heightTransitionWidth: 6.0,
    // 圆角 SDF 平滑度。
    sminSmoothing: 15.0,
  },
}

/** 判断当前是否为移动端视口 */
function isMobileViewport(): boolean {
  return typeof window !== 'undefined' && window.innerWidth <= 768
}

// ============================================================================
// 实例状态
// ============================================================================

let instanceId = 0
let ctx2d: CanvasRenderingContext2D | null = null
let resizeObserver: ResizeObserver | null = null
let renderedBackgroundUrl = ''
// 抽屉等组件可能先以 v-show 隐藏挂载，此时首次测量尺寸为 0。
// 记录尺寸有效状态，首次变为可见时重新触发纹理就绪流程。
let hasValidLayout = false

// Trail points（鼠标涟漪轨迹）
const TRAIL_MIN_DISTANCE = 14
interface TrailPoint {
  x: number
  y: number
  startedAt: number
  strength: number
}
let trailPoints: TrailPoint[] = []
let lastTrailPoint: [number, number] | null = null

// Uniforms 状态（每帧由渲染器读取）
const uniforms: GlassUniforms = {
  resolution: [0, 0],
  mousePos: [0, 0],
  glassSize: [0, 0],
  canvasOffset: [0, 0],
  texAspect: 1,
  cornerRadius: 0,
  ior: 0,
  glassThickness: 0,
  normalStrength: 0,
  displacementScale: 0,
  heightTransitionWidth: 0,
  sminSmoothing: 0,
  showNormals: 0,
  blurRadius: 0,
  overlayColor: [0, 0, 0, 1],
  highlightWidth: 0,
  trailPoints: Array.from(
    { length: MAX_TRAIL_POINTS },
    () => [0, 0, 1, 0] as [number, number, number, number],
  ),
  trailRadius: 0,
  trailStrength: 0,
}

// ============================================================================
// Uniform 更新逻辑
// ============================================================================

function getEffectiveBlurRadius(theme: 'light' | 'dark') {
  if (typeof props.blurRadius === 'number') return props.blurRadius
  return glassPresets[theme].blurRadius
}

/** 应用主题预设到 uniforms(移动端自动选用更厚重的参数) */
function applyThemePreset(theme: 'light' | 'dark') {
  const presets = isMobileViewport() ? mobileGlassPresets : glassPresets
  const p = presets[theme]
  uniforms.ior = p.ior
  uniforms.glassThickness = p.glassThickness
  uniforms.normalStrength = p.normalStrength
  uniforms.displacementScale = p.displacementScale
  uniforms.heightTransitionWidth = p.heightTransitionWidth
  uniforms.sminSmoothing = p.sminSmoothing
  uniforms.blurRadius = getEffectiveBlurRadius(theme)
  uniforms.highlightWidth = toCanvasPixels(p.highlightWidth)
  uniforms.overlayColor = [...p.overlayColor, 1.0] as [number, number, number, number]
}

/** 初始化所有 uniform 值 */
function initUniforms() {
  uniforms.cornerRadius = toCanvasPixels(props.cornerRadius)
  uniforms.trailRadius = props.rippleRadius
  uniforms.trailStrength = props.rippleTrail ? props.rippleStrength : 0
  applyThemePreset(props.theme)
}

/** 将 CSS 像素参数转换为当前 canvas 使用的物理像素。 */
function toCanvasPixels(value: number): number {
  return value * (window.devicePixelRatio || 1) * getRenderScale()
}

// ============================================================================
// Canvas 尺寸 / 偏移同步
// ============================================================================

function syncCanvasSize() {
  const container = containerRef.value
  const canvas = canvasRef.value
  if (!container || !canvas) return

  // 用 offsetWidth/offsetHeight 获取布局尺寸(不受 CSS transform 影响)
  // getBoundingClientRect 在 Transition 动画期间返回动画中的视觉尺寸,
  // 导致 canvas 在动画结束后尺寸不正确
  const w = container.offsetWidth
  const h = container.offsetHeight
  if (w < 1 || h < 1) return

  const dpr = window.devicePixelRatio || 1
  const scale = getRenderScale()
  const pw = Math.max(1, Math.round(w * dpr * scale))
  const ph = Math.max(1, Math.round(h * dpr * scale))

  // 圆角和边缘高光必须与 canvas 尺寸使用同一套物理像素单位。
  uniforms.cornerRadius = toCanvasPixels(props.cornerRadius)
  const presets = isMobileViewport() ? mobileGlassPresets : glassPresets
  uniforms.highlightWidth = toCanvasPixels(presets[props.theme].highlightWidth)

  canvas.width = pw
  canvas.height = ph
  canvas.style.width = w + 'px'
  canvas.style.height = h + 'px'

  // 更新 uniforms
  uniforms.resolution = [window.innerWidth * dpr * scale, window.innerHeight * dpr * scale]
  uniforms.glassSize = [pw, ph]
  uniforms.mousePos = [pw / 2, ph / 2]

  // canvasOffset 仍需要 getBoundingClientRect(计算视口相对位置)
  const rect = container.getBoundingClientRect()
  uniforms.canvasOffset = [rect.left * dpr * scale, rect.top * dpr * scale]

  // 清除 trail
  trailPoints = []
  lastTrailPoint = null
}

function syncCanvasOffset() {
  const container = containerRef.value
  if (!container) return
  const rect = container.getBoundingClientRect()
  const dpr = window.devicePixelRatio || 1
  const scale = getRenderScale()
  uniforms.resolution = [window.innerWidth * dpr * scale, window.innerHeight * dpr * scale]
  uniforms.canvasOffset = [rect.left * dpr * scale, rect.top * dpr * scale]
}

function refreshRenderer() {
  syncCanvasSize()
  const [gw, gh] = uniforms.glassSize
  if (gw >= 1 && gh >= 1) {
    hasValidLayout = true
    void syncBackgroundWithTheme(props.theme)
  }
}

// ============================================================================
// Trail Points（鼠标涟漪）
// ============================================================================

function getPointerCanvasPoint(event: PointerEvent): [number, number] | null {
  const container = containerRef.value
  if (!container) return null
  const rect = container.getBoundingClientRect()
  const dpr = window.devicePixelRatio || 1
  const scale = getRenderScale()
  const [width, height] = uniforms.glassSize
  return [
    (event.clientX - rect.left) * dpr * scale - width / 2,
    (event.clientY - rect.top) * dpr * scale - height / 2,
  ]
}

function addTrailPoint(event: PointerEvent) {
  if (!props.rippleTrail) return
  const point = getPointerCanvasPoint(event)
  if (!point) return
  if (lastTrailPoint) {
    const dx = point[0] - lastTrailPoint[0]
    const dy = point[1] - lastTrailPoint[1]
    const dpr = window.devicePixelRatio || 1
    const scale = getRenderScale()
    if (Math.hypot(dx, dy) < TRAIL_MIN_DISTANCE * dpr * scale) return
  }
  lastTrailPoint = point
  trailPoints.push({ x: point[0], y: point[1], startedAt: performance.now(), strength: 1 })
  if (trailPoints.length > MAX_TRAIL_POINTS) trailPoints.shift()
}

function resetTrailPoint() {
  lastTrailPoint = null
}

/** 每帧更新 trail uniforms（由 ResizeObserver 触发的渲染器轮询周期内自动调用） */
function updateTrailUniforms() {
  const now = performance.now()
  const duration = Math.max(1, props.rippleDuration)
  trailPoints = trailPoints.filter((p) => now - p.startedAt < duration)
  for (let i = 0; i < MAX_TRAIL_POINTS; i++) {
    const p = trailPoints[i]
    uniforms.trailPoints[i] = p
      ? [p.x, p.y, (now - p.startedAt) / duration, p.strength]
      : [0, 0, 1, 0]
  }
  uniforms.trailRadius = props.rippleRadius * (window.devicePixelRatio || 1) * getRenderScale()
  uniforms.trailStrength = props.rippleTrail ? props.rippleStrength : 0
}

// ============================================================================
// 背景纹理切换
// ============================================================================

async function syncBackgroundWithTheme(_theme: LiquidGlassTheme, forceReveal = false) {
  const url = currentBgUl.value
  if (!url || !instanceId) return
  const syncToken = ++backgroundSyncToken

  // 先隐藏 canvas（允许 reveal 时）
  const keepVisible =
    visible.value && Boolean(renderedBackgroundUrl) && hasTexture(renderedBackgroundUrl)
  if ((forceReveal || ui.themeTransitioning) && !keepVisible) {
    visible.value = false
    if (instanceId) {
      setInstanceFirstRenderCallback(instanceId, () => {
        visible.value = true
        emit('render-ready')
      })
    }
  }

  // 确保纹理已上传
  let textureReady = hasTexture(url)
  if (ui.themeTransitioning && !keepVisible) markInstanceReady(instanceId, false)
  if (!textureReady) {
    try {
      if (isVideoBackground(currentBackground.value)) {
        textureReady = await preloadVideoTexture(url)
      } else if (!isVideoBackground(currentBackground.value)) {
        const image = await loadImage(url)
        textureReady = uploadTexture(url, image)
      }
    } catch (e) {
      console.warn('[LiquidGlass] Failed to load background:', e, {
        url,
        mediaType: currentBackground.value.mediaType,
      })
    }
  }

  if (syncToken !== backgroundSyncToken || currentBgUl.value !== url) return

  // 更新纹理宽高比(cover 模式 UV 校正用)
  uniforms.texAspect = getTextureAspect(url)

  // 更新实例的背景 URL
  if (instanceId) {
    // 如果不需要 reveal 动画（纹理已就绪），直接标记 ready
    if (textureReady && uniforms.glassSize[0] >= 1 && uniforms.glassSize[1] >= 1) {
      setInstanceBackground(instanceId, url)
      renderedBackgroundUrl = url
      markInstanceReady(instanceId, true)
    } else {
      console.warn('[LiquidGlass] Background texture is not ready', {
        url,
        mediaType: currentBackground.value.mediaType,
      })
    }
  }
}

// ============================================================================
// 生命周期
// ============================================================================

// 每帧更新 offset 和 trail（通过 RAF 轮询,渲染器内部每帧读取 uniforms）
let frameId = 0
let backgroundSyncToken = 0
function frameUpdate() {
  syncCanvasOffset()
  updateTrailUniforms()
  frameId = requestAnimationFrame(frameUpdate)
}

// Context lost/restored 回调
function handleContextLost() {
  visible.value = false
}

function handleContextRestored() {
  // 重新上传纹理并恢复渲染
  void syncBackgroundWithTheme(props.theme)
}

/** 在父组件重新显示面板前，重置首帧状态并等待新的有效绘制。 */
function prepareReveal() {
  if (!instanceId) return
  visible.value = false
  markInstanceReady(instanceId, false)
  setInstanceFirstRenderCallback(instanceId, () => {
    visible.value = true
    emit('render-ready')
  })
  refreshRenderer()
  void syncBackgroundWithTheme(props.theme, true)
}

onMounted(() => {
  const canvas = canvasRef.value
  const container = containerRef.value
  if (!canvas || !container) return

  // 获取 2D context（用于接收渲染器的 drawImage）
  ctx2d = canvas.getContext('2d')
  if (!ctx2d) {
    rendererFailed.value = true
    return
  }

  // 注册到共享渲染器
  const bgUrl = currentBgUl.value
  renderedBackgroundUrl = bgUrl
  instanceId = registerInstance(canvas, ctx2d, uniforms, bgUrl, () => {
    visible.value = true
    emit('render-ready')
  })

  // registerInstance 会初始化 WebGL 并检测 renderScale,因此尺寸和物理像素参数必须在注册后计算。
  initUniforms()
  syncCanvasSize()

  // 注册 context lost/restored 回调
  onContextLost(handleContextLost)
  onContextRestored(handleContextRestored)

  // 加载纹理并标记实例为就绪
  void (async () => {
    const initialSyncToken = ++backgroundSyncToken
    let textureReady = hasTexture(bgUrl)
    markInstanceReady(instanceId, false)
    if (!textureReady) {
      try {
        if (isVideoBackground(currentBackground.value)) {
          textureReady = await preloadVideoTexture(bgUrl)
        } else if (!isVideoBackground(currentBackground.value)) {
          const image = await loadImage(bgUrl)
          textureReady = uploadTexture(bgUrl, image)
        }
      } catch (e) {
        console.warn('[LiquidGlass] Failed to load background:', e, {
          url: bgUrl,
          mediaType: currentBackground.value.mediaType,
        })
      }
    }
    // 更新纹理宽高比(cover 模式 UV 校正用)
    if (initialSyncToken !== backgroundSyncToken || currentBgUl.value !== bgUrl) return
    uniforms.texAspect = getTextureAspect(bgUrl)
    // 确保 canvas 尺寸有效后标记为就绪
    const [gw, gh] = uniforms.glassSize
    if (textureReady && gw >= 1 && gh >= 1) {
      markInstanceReady(instanceId, true)
    }
  })()

  // ResizeObserver：监听容器尺寸变化
  resizeObserver = new ResizeObserver(() => {
    syncCanvasSize()
    const [gw, gh] = uniforms.glassSize
    const valid = gw >= 1 && gh >= 1
    if (!valid) {
      hasValidLayout = false
      markInstanceReady(instanceId, false)
      return
    }

    // v-show 从隐藏切换为显示后，补跑一次背景纹理同步；否则实例会
    // 永远停留在“尺寸为 0 时未 ready”的状态，canvas 也就不会 reveal。
    if (!hasValidLayout) {
      hasValidLayout = true
      void syncBackgroundWithTheme(props.theme)
    }
  })
  resizeObserver.observe(container)

  // 启动每帧更新（offset + trail）
  frameId = requestAnimationFrame(frameUpdate)

  // Pointer events（涟漪效果）
  container.addEventListener('pointerenter', addTrailPoint)
  container.addEventListener('pointermove', addTrailPoint)
  container.addEventListener('pointerleave', resetTrailPoint)

  // 如果不需要 reveal 动画,且纹理已就绪,直接 skip firstRender 回调
})

// 背景图切换时重新加载纹理
watch([currentBgUl, () => currentBackground.value.mediaType], ([newUrl]) => {
  if (newUrl && instanceId) {
    void syncBackgroundWithTheme(props.theme)
  }
})

onBeforeUnmount(() => {
  // 在组件卸载前立即隐藏 canvas,杜绝卸载期间的白闪
  visible.value = false
})

onUnmounted(() => {
  // 注销实例
  if (instanceId) {
    unregisterInstance(instanceId)
    instanceId = 0
  }

  // 停止每帧更新
  if (frameId) {
    cancelAnimationFrame(frameId)
    frameId = 0
  }

  // 移除 context 回调
  offContextCallbacks(handleContextLost, handleContextRestored)

  // 清理 ResizeObserver
  resizeObserver?.disconnect()
  resizeObserver = null

  // 清理 pointer events
  const container = containerRef.value
  container?.removeEventListener('pointerenter', addTrailPoint)
  container?.removeEventListener('pointermove', addTrailPoint)
  container?.removeEventListener('pointerleave', resetTrailPoint)

  ctx2d = null
})

// ============================================================================
// Watchers
// ============================================================================

// 主题切换:重新应用玻璃参数预设,并切换纹理
watch(
  () => props.theme,
  (theme) => {
    applyThemePreset(theme)
    void syncBackgroundWithTheme(theme)
  },
)

// blurRadius prop 变化
watch(
  () => props.blurRadius,
  () => {
    uniforms.blurRadius = getEffectiveBlurRadius(props.theme)
  },
)

// 暴露 syncCanvasSize 供父组件在需要时手动触发(如 Transition 动画结束后)
defineExpose({ syncCanvasSize, refreshRenderer, prepareReveal })
</script>

<style scoped>
.liquid-glass {
  position: relative;
  width: 100%;
  height: 100%;
  border-radius: var(--liquid-glass-corner-radius, 16px);
  overflow: hidden;
}

.liquid-glass-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  pointer-events: none;
  border-radius: inherit;
  opacity: 0;
  transition: opacity 0.06s ease-out;
}

.liquid-glass-canvas--visible {
  opacity: 1;
}

.liquid-glass-content {
  position: relative;
  z-index: 1;
  width: 100%;
  height: 100%;
}

.liquid-glass--css-fallback {
  backdrop-filter: blur(16px) saturate(1.1);
  -webkit-backdrop-filter: blur(16px) saturate(1.1);
  background: var(--glass-bg);
  border: 1px solid var(--glass-border-subtle);
}
</style>
