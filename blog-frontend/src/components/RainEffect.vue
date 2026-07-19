<template>
  <canvas
    ref="canvasRef"
    class="rain-canvas"
    :class="{ 'rain-canvas--hidden': !rainEnabled }"
    aria-hidden="true"
  ></canvas>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useUIStore } from '@/stores/ui'

const ui = useUIStore()
const { rainEnabled, rainIntensity, theme } = storeToRefs(ui)

const canvasRef = ref<HTMLCanvasElement | null>(null)
let ctx: CanvasRenderingContext2D | null = null
let rafId = 0
let panesCache: DOMRect[] = []
let paneCacheAge = 0
const PANE_CACHE_TTL = 5

// —— Particles ——
interface Raindrop {
  x: number
  y: number
  speed: number
  length: number
  opacity: number
  active: boolean
  wasInsidePane: boolean
}

interface Splash {
  x: number
  y: number
  vx: number
  vy: number
  life: number
  maxLife: number
  active: boolean
}

interface IntensityConfig {
  maxDrops: number
  spawnRate: number
  speedMin: number
  speedMax: number
  lengthMin: number
  lengthMax: number
}

const MAX_RAINDROPS = 250
const MAX_SPLASHES = 80

const raindrops: Raindrop[] = []
const splashes: Splash[] = []

for (let i = 0; i < MAX_RAINDROPS; i++) {
  raindrops.push({ x: 0, y: 0, speed: 0, length: 0, opacity: 0, active: false, wasInsidePane: false })
}
for (let i = 0; i < MAX_SPLASHES; i++) {
  splashes.push({ x: 0, y: 0, vx: 0, vy: 0, life: 0, maxLife: 0, active: false })
}

const intensityConfigs: IntensityConfig[] = [
  { maxDrops: 80, spawnRate: 0.5, speedMin: 5, speedMax: 10, lengthMin: 12, lengthMax: 24 },
  { maxDrops: 150, spawnRate: 0.8, speedMin: 8, speedMax: 14, lengthMin: 16, lengthMax: 32 },
  { maxDrops: 250, spawnRate: 2, speedMin: 10, speedMax: 20, lengthMin: 20, lengthMax: 40 },
]

let dropsSpawnAcc = 0

// —— Theme colors ——
const rainColor = computed(() =>
  theme.value === 'dark'
    ? 'rgba(180, 210, 255, {{o}})'
    : 'rgba(60, 120, 220, {{o}})',
)

const splashColor = computed(() =>
  theme.value === 'dark'
    ? 'rgba(200, 230, 255, {{o}})'
    : 'rgba(80, 140, 220, {{o}})',
)

function colorWithOpacity(template: string, opacity: number): string {
  return template.replace('{{o}}', opacity.toFixed(2))
}

// —— Canvas sizing ——
let w = 0
let h = 0

function resize() {
  const canvas = canvasRef.value
  if (!canvas) return
  const dpr = window.devicePixelRatio || 1
  w = window.innerWidth
  h = window.innerHeight
  canvas.width = w * dpr
  canvas.height = h * dpr
  canvas.style.width = w + 'px'
  canvas.style.height = h + 'px'
  if (ctx) ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
}

// —— Glass pane detection ——
function updatePaneCache() {
  const els = document.querySelectorAll('.liquid-glass')
  panesCache = []
  els.forEach((el) => {
    const rect = el.getBoundingClientRect()
    if (rect.width > 0 && rect.height > 0) panesCache.push(rect)
  })
  paneCacheAge = 0
}

function isInsidePane(x: number, y: number): boolean {
  for (const r of panesCache) {
    if (x >= r.left && x <= r.right && y >= r.top && y <= r.bottom) return true
  }
  return false
}

// —— Spawn helpers ——
function spawnSplashes(x: number, y: number, count: number) {
  let actual = Math.min(count, 12)
  for (let i = 0; i < MAX_SPLASHES; i++) {
    const s = splashes[i]
    if (s.active) continue
    const angle = -Math.PI / 2 + (Math.random() - 0.5) * Math.PI * 0.9
    const speed = 2 + Math.random() * 5
    s.x = x
    s.y = y
    s.vx = Math.cos(angle) * speed
    s.vy = Math.sin(angle) * speed
    s.life = 8 + Math.random() * 8
    s.maxLife = s.life
    s.active = true
    if (--actual <= 0) break
  }
}

// —— Main loop ——
function tick() {
  if (!ctx) return
  const cfg = intensityConfigs[rainIntensity.value]

  ctx.clearRect(0, 0, w, h)

  paneCacheAge++
  if (paneCacheAge >= PANE_CACHE_TTL) updatePaneCache()

  // Spawn raindrops
  dropsSpawnAcc += cfg.spawnRate
  while (dropsSpawnAcc >= 1) {
    dropsSpawnAcc -= 1
    let activeCount = 0
    for (const d of raindrops) { if (d.active) activeCount++ }
    if (activeCount < cfg.maxDrops) {
      for (const d of raindrops) {
        if (!d.active) {
          d.x = Math.random() * w
          d.y = -(cfg.lengthMax + Math.random() * 100)
          d.speed = cfg.speedMin + Math.random() * (cfg.speedMax - cfg.speedMin)
          d.length = cfg.lengthMin + Math.random() * (cfg.lengthMax - cfg.lengthMin)
          d.opacity = 0.3 + Math.random() * 0.35
          d.active = true
          d.wasInsidePane = false
          break
        }
      }
    }
  }

  // Draw raindrops + collision
  const rColor = rainColor.value
  for (const d of raindrops) {
    if (!d.active) continue

    d.y += d.speed
    const tailY = d.y - d.length

    ctx.beginPath()
    ctx.moveTo(d.x, tailY)
    ctx.lineTo(d.x, d.y)
    ctx.strokeStyle = colorWithOpacity(rColor, d.opacity)
    ctx.lineWidth = 1.5
    ctx.stroke()

    const inside = isInsidePane(d.x, d.y)
    if (inside && !d.wasInsidePane) {
      spawnSplashes(d.x, d.y, 8 + Math.floor(Math.random() * 5))
    }
    d.wasInsidePane = inside

    if (tailY > h + 10) d.active = false
  }

  // Draw splashes
  const spColor = splashColor.value
  for (const s of splashes) {
    if (!s.active) continue

    s.x += s.vx
    s.y += s.vy
    s.vy += 0.12
    s.life--
    if (s.life <= 0) { s.active = false; continue }

    const t = s.life / s.maxLife
    const angle = Math.atan2(s.vy, s.vx)
    const rx = 3 * t
    const ry = 1.5 * t

    ctx.save()
    ctx.translate(s.x, s.y)
    ctx.rotate(angle)
    ctx.beginPath()
    ctx.ellipse(0, 0, rx, ry, 0, 0, Math.PI * 2)
    ctx.fillStyle = colorWithOpacity(spColor, t * 0.8)
    ctx.fill()
    ctx.restore()
  }

  rafId = requestAnimationFrame(tick)
}

// —— Lifecycle ——
onMounted(() => {
  const canvas = canvasRef.value
  if (!canvas) return
  ctx = canvas.getContext('2d')
  if (!ctx) return
  resize()
  window.addEventListener('resize', resize)
  updatePaneCache()
  if (rainEnabled.value) rafId = requestAnimationFrame(tick)
})

onUnmounted(() => {
  cancelAnimationFrame(rafId)
  window.removeEventListener('resize', resize)
  ctx = null
})

watch(rainEnabled, (enabled) => {
  if (!enabled) {
    cancelAnimationFrame(rafId)
    ctx?.clearRect(0, 0, w, h)
  } else {
    resize()
    updatePaneCache()
    cancelAnimationFrame(rafId)
    rafId = requestAnimationFrame(tick)
  }
})
</script>

<style scoped>
.rain-canvas {
  position: fixed;
  inset: 0;
  z-index: 45;
  pointer-events: none;
}

.rain-canvas--hidden {
  display: none;
}
</style>
