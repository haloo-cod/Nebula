<template>
  <div class="liquid-glass" ref="containerRef" :class="{ 'liquid-glass--css-fallback': rendererFailed }">
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
import { ref, watch, onMounted, onBeforeUnmount, onUnmounted } from 'vue'
import darkBgUrl from '@/assets/img/test3.jpg'
import lightBgUrl from '@/assets/img/test6.png'
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
  isRendererAvailable,
  loadImage,
  uploadTexture,
  hasTexture,
  preloadTexture,
  MAX_TRAIL_POINTS,
  type GlassUniforms,
} from '@/components/liquidGlassRenderer'

const containerRef = ref<HTMLElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)
const visible = ref(false)
const rendererFailed = ref(false)
const ui = useUIStore()

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

const backgroundUrls: Record<LiquidGlassTheme, string> = {
  dark: darkBgUrl,
  light: lightBgUrl,
}

// 两套液态玻璃参数预设
const glassPresets = {
  dark: {
    glassThickness: 56,
    ior: 1.15,
    highlightWidth: 4.0,
    blurRadius: 0.0,
    overlayColor: [0.2, 0.26, 0.32] as [number, number, number],
    normalStrength: 8.0,
    displacementScale: 1.0,
    heightTransitionWidth: 10.0,
    sminSmoothing: 20.0,
  },
  light: {
    glassThickness: 28,
    ior: 1.05,
    highlightWidth: 2.5,
    blurRadius: 0.5,
    overlayColor: [0.6, 0.65, 0.75] as [number, number, number],
    normalStrength: 5.0,
    displacementScale: 0.8,
    heightTransitionWidth: 6.0,
    sminSmoothing: 15.0,
  },
}

// ============================================================================
// 实例状态
// ============================================================================

let instanceId = 0
let ctx2d: CanvasRenderingContext2D | null = null
let resizeObserver: ResizeObserver | null = null

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
  trailPoints: Array.from({ length: MAX_TRAIL_POINTS }, () => [0, 0, 1, 0] as [number, number, number, number]),
  trailRadius: 0,
  trailStrength: 0,
}

// 预热两张背景图
void preloadTexture(darkBgUrl)
void preloadTexture(lightBgUrl)

// ============================================================================
// Uniform 更新逻辑
// ============================================================================

function getEffectiveBlurRadius(theme: 'light' | 'dark') {
  if (typeof props.blurRadius === 'number') return props.blurRadius
  return glassPresets[theme].blurRadius
}

/** 应用主题预设到 uniforms */
function applyThemePreset(theme: 'light' | 'dark') {
  const p = glassPresets[theme]
  uniforms.ior = p.ior
  uniforms.glassThickness = p.glassThickness
  uniforms.normalStrength = p.normalStrength
  uniforms.displacementScale = p.displacementScale
  uniforms.heightTransitionWidth = p.heightTransitionWidth
  uniforms.sminSmoothing = p.sminSmoothing
  uniforms.blurRadius = getEffectiveBlurRadius(theme)
  uniforms.highlightWidth = p.highlightWidth
  uniforms.overlayColor = [...p.overlayColor, 1.0] as [number, number, number, number]
}

/** 初始化所有 uniform 值 */
function initUniforms() {
  uniforms.cornerRadius = props.cornerRadius
  uniforms.trailRadius = props.rippleRadius
  uniforms.trailStrength = props.rippleTrail ? props.rippleStrength : 0
  applyThemePreset(props.theme)
}

// ============================================================================
// Canvas 尺寸 / 偏移同步
// ============================================================================

function syncCanvasSize() {
  const container = containerRef.value
  const canvas = canvasRef.value
  if (!container || !canvas) return

  const rect = container.getBoundingClientRect()
  if (rect.width < 1 || rect.height < 1) return

  const dpr = window.devicePixelRatio || 1
  const w = rect.width * dpr
  const h = rect.height * dpr

  canvas.width = w
  canvas.height = h
  canvas.style.width = rect.width + 'px'
  canvas.style.height = rect.height + 'px'

  // 更新 uniforms
  uniforms.resolution = [window.innerWidth * dpr, window.innerHeight * dpr]
  uniforms.glassSize = [w, h]
  uniforms.mousePos = [w / 2, h / 2]
  uniforms.canvasOffset = [rect.left * dpr, rect.top * dpr]

  // 清除 trail
  trailPoints = []
  lastTrailPoint = null
}

function syncCanvasOffset() {
  const container = containerRef.value
  if (!container) return
  const rect = container.getBoundingClientRect()
  const dpr = window.devicePixelRatio || 1
  uniforms.resolution = [window.innerWidth * dpr, window.innerHeight * dpr]
  uniforms.canvasOffset = [rect.left * dpr, rect.top * dpr]
}

// ============================================================================
// Trail Points（鼠标涟漪）
// ============================================================================

function getPointerCanvasPoint(event: PointerEvent): [number, number] | null {
  const container = containerRef.value
  if (!container) return null
  const rect = container.getBoundingClientRect()
  const dpr = window.devicePixelRatio || 1
  const [width, height] = uniforms.glassSize
  return [
    (event.clientX - rect.left) * dpr - width / 2,
    (event.clientY - rect.top) * dpr - height / 2,
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
    if (Math.hypot(dx, dy) < TRAIL_MIN_DISTANCE * dpr) return
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
  uniforms.trailRadius = props.rippleRadius * (window.devicePixelRatio || 1)
  uniforms.trailStrength = props.rippleTrail ? props.rippleStrength : 0
}

// ============================================================================
// 背景纹理切换
// ============================================================================

async function syncBackgroundWithTheme(theme: LiquidGlassTheme) {
  const url = backgroundUrls[theme]

  // 先隐藏 canvas（允许 reveal 时）
  if (props.allowReveal || ui.themeTransitioning) {
    visible.value = false
    if (instanceId) {
      setInstanceFirstRenderCallback(instanceId, () => {
        visible.value = true
      })
    }
  }

  // 确保纹理已上传
  if (!hasTexture(url)) {
    try {
      const image = await loadImage(url)
      uploadTexture(url, image)
    } catch (e) {
      console.warn('[LiquidGlass] Failed to load background:', e)
    }
  }

  // 更新实例的背景 URL
  if (instanceId) {
    setInstanceBackground(instanceId, url)
    // 如果不需要 reveal 动画（纹理已就绪），直接标记 ready
    markInstanceReady(instanceId, true)
  }
}

// ============================================================================
// 生命周期
// ============================================================================

// 每帧更新 offset 和 trail（通过 RAF 轮询,渲染器内部每帧读取 uniforms）
let frameId = 0
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

  // 检查渲染器是否可用
  if (!isRendererAvailable()) {
    // 渲染器可能在首次调用时初始化,先尝试注册
  }

  // 初始化 uniforms
  initUniforms()
  syncCanvasSize()

  // 注册到共享渲染器
  const bgUrl = backgroundUrls[props.theme]
  instanceId = registerInstance(canvas, ctx2d, uniforms, bgUrl, () => {
    visible.value = true
  })

  // 注册 context lost/restored 回调
  onContextLost(handleContextLost)
  onContextRestored(handleContextRestored)

  // 加载纹理并标记实例为就绪
  void (async () => {
    if (!hasTexture(bgUrl)) {
      try {
        const image = await loadImage(bgUrl)
        uploadTexture(bgUrl, image)
      } catch (e) {
        console.warn('[LiquidGlass] Failed to load background:', e)
      }
    }
    // 确保 canvas 尺寸有效后标记为就绪
    const [gw, gh] = uniforms.glassSize
    if (gw >= 1 && gh >= 1) {
      markInstanceReady(instanceId, true)
    }
  })()

  // ResizeObserver：监听容器尺寸变化
  resizeObserver = new ResizeObserver(() => {
    syncCanvasSize()
    // 尺寸有效后标记就绪
    const [gw, gh] = uniforms.glassSize
    if (gw >= 1 && gh >= 1 && instanceId) {
      markInstanceReady(instanceId, true)
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
  if (!props.allowReveal && hasTexture(bgUrl)) {
    visible.value = true
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
</script>

<style scoped>
.liquid-glass {
  position: relative;
  width: 100%;
  height: 100%;
  border-radius: 16px;
  overflow: hidden;
}

.liquid-glass-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  pointer-events: none;
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
