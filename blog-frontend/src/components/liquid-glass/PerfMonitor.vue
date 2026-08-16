<template>
  <div
    ref="rootRef"
    class="perf-monitor"
    :class="{ 'perf-monitor--collapsed': collapsed, 'perf-monitor--dragging': dragging }"
    :style="posStyle"
  >
    <div class="perf-monitor__header" @pointerdown="onDragStart">
      <span class="perf-monitor__title">性能监控</span>
      <span class="perf-monitor__fps" :class="fpsClass">{{ fps }} FPS</span>
      <button
        class="perf-monitor__toggle"
        type="button"
        @pointerdown.stop
        @click.stop="collapsed = !collapsed"
      >
        {{ collapsed ? '展开' : '收起' }}
      </button>
    </div>

    <div v-if="!collapsed" class="perf-monitor__body">
      <!-- 页面级帧率(requestAnimationFrame 实测) -->
      <div class="perf-row">
        <span class="perf-label">页面 FPS</span>
        <span class="perf-value" :class="fpsClass">{{ fps }}</span>
      </div>
      <div class="perf-row">
        <span class="perf-label">帧间隔 (avg)</span>
        <span class="perf-value">{{ avgFrameMs.toFixed(1) }} ms</span>
      </div>
      <div class="perf-row">
        <span class="perf-label">帧间隔 (max)</span>
        <span class="perf-value" :class="{ 'perf-value--warn': maxFrameMs > 33 }">
          {{ maxFrameMs.toFixed(1) }} ms
        </span>
      </div>

      <div class="perf-divider"></div>

      <!-- 液态玻璃渲染器指标 -->
      <div class="perf-row">
        <span class="perf-label">渲染 FPS</span>
        <span class="perf-value" :class="renderFpsClass">{{ metrics.renderFps }}</span>
      </div>
      <div class="perf-row">
        <span class="perf-label">GL 帧耗时</span>
        <span class="perf-value" :class="{ 'perf-value--warn': metrics.lastFrameDuration > 8 }">
          {{ metrics.lastFrameDuration.toFixed(2) }} ms
        </span>
      </div>
      <div class="perf-row">
        <span class="perf-label">├ GL 绘制</span>
        <span class="perf-value" :class="{ 'perf-value--warn': metrics.lastDrawDuration > 5 }">
          {{ metrics.lastDrawDuration.toFixed(2) }} ms
        </span>
      </div>
      <div class="perf-row">
        <span class="perf-label">└ 2D 拷贝</span>
        <span class="perf-value" :class="{ 'perf-value--warn': metrics.lastCopyDuration > 3 }">
          {{ metrics.lastCopyDuration.toFixed(2) }} ms
        </span>
      </div>
      <div class="perf-row">
        <span class="perf-label">渲染实例</span>
        <span class="perf-value">{{ metrics.renderedInstances }} / {{ stats.total }}</span>
      </div>
      <div class="perf-row">
        <span class="perf-label">就绪实例</span>
        <span class="perf-value">{{ stats.ready }}</span>
      </div>
      <div class="perf-row">
        <span class="perf-label">Draw calls</span>
        <span class="perf-value">{{ drawCallsPerSec }}/s</span>
      </div>
      <div class="perf-row">
        <span class="perf-label">Copy calls</span>
        <span class="perf-value">{{ copyCallsPerSec }}/s</span>
      </div>
      <div class="perf-row">
        <span class="perf-label">Video uploads</span>
        <span class="perf-value">{{ videoUploadsPerSec }}/s</span>
      </div>
      <div class="perf-row">
        <span class="perf-label">Watchdog uploads</span>
        <span class="perf-value">{{ videoWatchdogUploadsPerSec }}/s</span>
      </div>
      <div class="perf-row">
        <span class="perf-label">Video failures</span>
        <span class="perf-value" :class="{ 'perf-value--warn': videoUploadFailuresPerSec > 0 }">
          {{ videoUploadFailuresPerSec }}/s
        </span>
      </div>
      <div class="perf-row perf-row--wrap">
        <span class="perf-label">Video state</span>
        <span class="perf-value perf-value--url">{{ videoState }}</span>
      </div>
      <div class="perf-row">
        <span class="perf-label">Canvas resize</span>
        <span class="perf-value" :class="{ 'perf-value--warn': resizesPerSec > 5 }">
          {{ resizesPerSec }}/s
        </span>
      </div>
      <div class="perf-row">
        <span class="perf-label">Copy bounds</span>
        <span
          class="perf-value"
          :class="{ 'perf-value--warn': copyBoundsPerSec > 0 || metrics.copyBoundsErrors > 0 }"
        >
          {{ metrics.copyBoundsErrors }} ({{ copyBoundsPerSec }}/s)
        </span>
      </div>

      <div class="perf-divider"></div>

      <div class="perf-row">
        <span class="perf-label">渲染缩放</span>
        <span class="perf-value">{{ stats.renderScale.toFixed(2) }}x</span>
      </div>
      <div class="perf-row">
        <span class="perf-label">纹理缓存</span>
        <span class="perf-value">{{ stats.textures }}</span>
      </div>
      <div class="perf-row">
        <span class="perf-label">DPR</span>
        <span class="perf-value">{{ dpr }}</span>
      </div>
      <div class="perf-row">
        <span class="perf-label">视口</span>
        <span class="perf-value">{{ viewport }}</span>
      </div>
      <div class="perf-row">
        <span class="perf-label">内存</span>
        <span class="perf-value">{{ memoryMb }}</span>
      </div>

      <div class="perf-divider"></div>

      <!-- 网络/API 探针(调试手机访问后端用) -->
      <div class="perf-row perf-row--wrap">
        <span class="perf-label">API Base</span>
        <span class="perf-value perf-value--url">{{ apiBase || '(同域)' }}</span>
      </div>
      <div class="perf-row">
        <span class="perf-label">API 延迟</span>
        <span class="perf-value" :class="apiLatencyClass">{{ apiLatencyText }}</span>
      </div>
      <div class="perf-row perf-row--wrap" v-if="apiError">
        <span class="perf-value perf-value--bad">{{ apiError }}</span>
      </div>
      <button class="perf-monitor__probe" type="button" @pointerdown.stop @click.stop="probeApi">
        重测 API
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 临时性能监控面板 — 液态玻璃性能调试用
 *
 * 显示两类数据:
 *   1. 页面级帧率(自建 RAF 循环实测,不依赖渲染器)
 *   2. 液态玻璃共享渲染器的内部指标(轮询 getRendererMetrics)
 *
 * 仅用于开发/调试,可通过快捷键或查询参数开关(见 App.vue)。
 */
import { ref, computed, onMounted, onUnmounted } from 'vue'
import {
  getRendererMetrics,
  getInstanceStats,
  getVideoTextureStats,
  type RendererMetrics,
  type InstanceStats,
} from '@/components/liquid-glass/liquidGlassRenderer'
import { BASE_URL } from '@/api/client'

const collapsed = ref(false)

// ============================================================================
// 拖动逻辑（指针拖动标题栏移动面板）
// ============================================================================
const rootRef = ref<HTMLElement | null>(null)
const dragging = ref(false)
// null 时用 CSS 默认定位(右下角);拖动后改为 left/top 绝对定位
const pos = ref<{ x: number; y: number } | null>(null)
let dragOffsetX = 0
let dragOffsetY = 0

/** 拖动时的内联定位样式(未拖动时返回空,沿用 CSS 右下角) */
const posStyle = computed(() => {
  if (!pos.value) return {}
  return {
    left: `${pos.value.x}px`,
    top: `${pos.value.y}px`,
    right: 'auto',
    bottom: 'auto',
  }
})

function onDragStart(e: PointerEvent) {
  const el = rootRef.value
  if (!el) return
  dragging.value = true
  const rect = el.getBoundingClientRect()
  dragOffsetX = e.clientX - rect.left
  dragOffsetY = e.clientY - rect.top
  window.addEventListener('pointermove', onDragMove)
  window.addEventListener('pointerup', onDragEnd)
}

function onDragMove(e: PointerEvent) {
  if (!dragging.value) return
  const el = rootRef.value
  const w = el?.offsetWidth ?? 220
  const h = el?.offsetHeight ?? 200
  // 约束在视口内,留 4px 边距
  const x = Math.min(Math.max(4, e.clientX - dragOffsetX), window.innerWidth - w - 4)
  const y = Math.min(Math.max(4, e.clientY - dragOffsetY), window.innerHeight - h - 4)
  pos.value = { x, y }
}

function onDragEnd() {
  dragging.value = false
  window.removeEventListener('pointermove', onDragMove)
  window.removeEventListener('pointerup', onDragEnd)
}

// ============================================================================
// 页面级 FPS 实测
// ============================================================================
const fps = ref(0)
const avgFrameMs = ref(0)
const maxFrameMs = ref(0)

let rafId = 0
let lastTime = performance.now()
let frames = 0
let frameMsSum = 0
let frameMsMax = 0
let windowStart = performance.now()

/** 每帧记录间隔,每 500ms 汇总一次 FPS/平均帧时/峰值帧时 */
function tickFps() {
  const now = performance.now()
  const delta = now - lastTime
  lastTime = now
  frames++
  frameMsSum += delta
  if (delta > frameMsMax) frameMsMax = delta

  const elapsed = now - windowStart
  if (elapsed >= 500) {
    fps.value = Math.round((frames * 1000) / elapsed)
    avgFrameMs.value = frames > 0 ? frameMsSum / frames : 0
    maxFrameMs.value = frameMsMax
    frames = 0
    frameMsSum = 0
    frameMsMax = 0
    windowStart = now
  }
  rafId = requestAnimationFrame(tickFps)
}

const fpsClass = computed(() => {
  if (fps.value >= 55) return 'perf-value--good'
  if (fps.value >= 30) return 'perf-value--warn'
  return 'perf-value--bad'
})

const renderFpsClass = computed(() => {
  const v = metrics.value.renderFps
  if (v >= 55) return 'perf-value--good'
  if (v >= 28) return 'perf-value--warn'
  return 'perf-value--bad'
})

// ============================================================================
// 渲染器指标轮询(计算每秒增量)
// ============================================================================
const metrics = ref<RendererMetrics>(getRendererMetrics())
const stats = ref<InstanceStats>(getInstanceStats())
const drawCallsPerSec = ref(0)
const copyCallsPerSec = ref(0)
const videoUploadsPerSec = ref(0)
const videoWatchdogUploadsPerSec = ref(0)
const videoUploadFailuresPerSec = ref(0)
const copyBoundsPerSec = ref(0)
const videoState = ref('none')
const resizesPerSec = ref(0)

let pollId = 0
let prevMetrics = getRendererMetrics()
let prevPollTime = performance.now()

/** 每 500ms 拉取一次渲染器指标,把累计计数换算成每秒速率 */
function pollMetrics() {
  const m = getRendererMetrics()
  const now = performance.now()
  const dt = (now - prevPollTime) / 1000 || 1

  drawCallsPerSec.value = Math.round((m.drawCalls - prevMetrics.drawCalls) / dt)
  copyCallsPerSec.value = Math.round((m.copyCalls - prevMetrics.copyCalls) / dt)
  videoUploadsPerSec.value = Math.round((m.videoFrameUploads - prevMetrics.videoFrameUploads) / dt)
  videoWatchdogUploadsPerSec.value = Math.round(
    (m.videoWatchdogUploads - prevMetrics.videoWatchdogUploads) / dt,
  )
  videoUploadFailuresPerSec.value = Math.round(
    (m.videoUploadFailures - prevMetrics.videoUploadFailures) / dt,
  )
  resizesPerSec.value = Math.round((m.canvasResizes - prevMetrics.canvasResizes) / dt)
  copyBoundsPerSec.value = Math.round((m.copyBoundsErrors - prevMetrics.copyBoundsErrors) / dt)

  metrics.value = m
  stats.value = getInstanceStats()
  const videos = getVideoTextureStats()
  videoState.value = videos.length
    ? videos
        .map((v) => `${v.readyState}/${v.paused ? 'paused' : 'playing'} ${v.width}x${v.height}`)
        .join(' · ')
    : 'none'
  prevMetrics = m
  prevPollTime = now
}

// ============================================================================
// 环境信息
// ============================================================================
const dpr = typeof window !== 'undefined' ? window.devicePixelRatio || 1 : 1
const viewport = ref('')
const memoryMb = ref('N/A')

function updateViewport() {
  viewport.value = `${window.innerWidth}×${window.innerHeight}`
}

/** performance.memory 是 Chromium 私有 API,类型未标准化,故用 any 读取 */
function updateMemory() {
  const mem = (performance as any).memory
  if (mem && typeof mem.usedJSHeapSize === 'number') {
    memoryMb.value = `${(mem.usedJSHeapSize / 1048576).toFixed(0)} MB`
  }
}

// ============================================================================
// API 网络探针(调试手机访问后端)
// ============================================================================
const apiBase = BASE_URL
const apiLatency = ref<number | null>(null)
const apiError = ref('')
const apiProbing = ref(false)

const apiLatencyText = computed(() => {
  if (apiProbing.value) return '测试中…'
  if (apiLatency.value === null) return '—'
  return `${apiLatency.value} ms`
})

const apiLatencyClass = computed(() => {
  if (apiError.value) return 'perf-value--bad'
  if (apiLatency.value === null) return ''
  if (apiLatency.value < 150) return 'perf-value--good'
  if (apiLatency.value < 500) return 'perf-value--warn'
  return 'perf-value--bad'
})

/** 请求 /health 测量后端可达性与延迟,失败时暴露具体错误(手机调试关键) */
async function probeApi() {
  apiProbing.value = true
  apiError.value = ''
  const start = performance.now()
  try {
    const res = await fetch(`${apiBase}/health`, { credentials: 'include' })
    apiLatency.value = Math.round(performance.now() - start)
    if (!res.ok) apiError.value = `HTTP ${res.status}`
  } catch (e) {
    apiLatency.value = null
    // 网络层失败(CORS/连接拒绝/混合内容)会走到这里
    apiError.value = e instanceof Error ? `${e.name}: ${e.message}` : '请求失败'
  } finally {
    apiProbing.value = false
  }
}

onMounted(() => {
  updateViewport()
  updateMemory()
  window.addEventListener('resize', updateViewport)
  rafId = requestAnimationFrame(tickFps)
  pollId = window.setInterval(() => {
    pollMetrics()
    updateMemory()
  }, 500)
  void probeApi()
})

onUnmounted(() => {
  if (rafId) cancelAnimationFrame(rafId)
  if (pollId) clearInterval(pollId)
  window.removeEventListener('resize', updateViewport)
  window.removeEventListener('pointermove', onDragMove)
  window.removeEventListener('pointerup', onDragEnd)
})
</script>

<style scoped>
.perf-monitor {
  position: fixed;
  right: 12px;
  bottom: 12px;
  z-index: 100000;
  width: 220px;
  font-family: ui-monospace, 'SF Mono', 'Cascadia Code', Menlo, Consolas, monospace;
  font-size: 11px;
  line-height: 1.4;
  color: #e6edf3;
  background: rgba(13, 17, 23, 0.82);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
  overflow: hidden;
  user-select: none;
}

.perf-monitor--collapsed {
  width: auto;
}

.perf-monitor--dragging {
  opacity: 0.9;
}

.perf-monitor__header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  cursor: grab;
  touch-action: none;
  background: rgba(255, 255, 255, 0.04);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.perf-monitor--dragging .perf-monitor__header {
  cursor: grabbing;
}

.perf-monitor--collapsed .perf-monitor__header {
  border-bottom: none;
}

.perf-monitor__title {
  font-weight: 600;
  letter-spacing: 0.5px;
  white-space: nowrap;
}

.perf-monitor__fps {
  margin-left: auto;
  font-variant-numeric: tabular-nums;
  font-weight: 700;
}

.perf-monitor__toggle {
  padding: 1px 6px;
  font-size: 10px;
  color: #e6edf3;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 5px;
  cursor: pointer;
}

.perf-monitor__body {
  padding: 8px 10px;
}

.perf-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1px 0;
}

.perf-row--wrap {
  flex-wrap: wrap;
  gap: 2px;
}

.perf-label {
  color: #8b949e;
}

.perf-value {
  font-variant-numeric: tabular-nums;
  font-weight: 600;
}

.perf-value--url {
  font-weight: 500;
  font-size: 10px;
  word-break: break-all;
  text-align: right;
  color: #79c0ff;
}

.perf-monitor__probe {
  width: 100%;
  margin-top: 6px;
  padding: 4px 0;
  font-size: 10px;
  color: #e6edf3;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 5px;
  cursor: pointer;
  touch-action: manipulation;
}

.perf-value--good {
  color: #3fb950;
}

.perf-value--warn {
  color: #d29922;
}

.perf-value--bad {
  color: #f85149;
}

.perf-divider {
  height: 1px;
  margin: 6px 0;
  background: rgba(255, 255, 255, 0.08);
}
</style>
