<template>
  <GlassPanel :flat="flat" class="chart-panel">
    <div class="chart-header">
      <span class="chart-title">发文统计</span>
      <span class="chart-sub">共 {{ total }} 篇</span>
    </div>

    <div v-if="points.length === 0" class="chart-empty">暂无数据</div>

    <svg
      v-else
      class="chart-svg"
      :viewBox="`0 0 ${W} ${H}`"
      preserveAspectRatio="none"
      role="img"
      aria-label="按时间统计的发文数量折线图"
    >
      <!-- 横向网格线 + y 轴刻度 -->
      <g class="grid">
        <template v-for="t in yTicks" :key="t.value">
          <line :x1="padL" :y1="t.y" :x2="W - padR" :y2="t.y" class="grid-line" />
          <text :x="padL - 6" :y="t.y + 3" class="axis-label y-label">{{ t.value }}</text>
        </template>
      </g>

      <!-- 面积填充 -->
      <path :d="areaPath" class="area" />

      <!-- 折线 -->
      <path :d="linePath" class="line" />

      <!-- 数据点 + x 轴标签 -->
      <g>
        <template v-for="(p, i) in points" :key="i">
          <circle :cx="p.x" :cy="p.y" r="3.5" class="dot" />
          <text :x="p.x" :y="H - padB + 16" class="axis-label x-label">{{ p.label }}</text>
        </template>
      </g>
    </svg>
  </GlassPanel>
</template>

<script setup>
import { computed } from 'vue'
import GlassPanel from './GlassPanel.vue'
import { getPostStats } from '@/data/posts'

defineProps({
  flat: { type: Boolean, default: false },
})

// SVG 视图坐标系（用 viewBox 自适应面板宽度）
const W = 280
const H = 180
const padL = 28 // 左侧留给 y 轴刻度
const padR = 12
const padT = 14
const padB = 26 // 底部留给 x 轴标签

const stats = computed(() => getPostStats())
const total = computed(() => stats.value.reduce((sum, s) => sum + s.count, 0))

const maxCount = computed(() => Math.max(1, ...stats.value.map((s) => s.count)))

// y 轴刻度（0 到 maxCount，最多 4 段）
const yTicks = computed(() => {
  const max = maxCount.value
  const step = Math.max(1, Math.ceil(max / 4))
  const ticks = []
  for (let v = 0; v <= max; v += step) {
    const y = padT + (H - padT - padB) * (1 - v / max)
    ticks.push({ value: v, y })
  }
  return ticks
})

const points = computed(() => {
  const list = stats.value
  if (list.length === 0) return []
  const innerW = W - padL - padR
  const innerH = H - padT - padB
  const max = maxCount.value
  return list.map((s, i) => {
    const x = list.length === 1 ? padL + innerW / 2 : padL + (innerW * i) / (list.length - 1)
    const y = padT + innerH * (1 - s.count / max)
    return { x, y, label: s.label, count: s.count }
  })
})

const linePath = computed(() =>
  points.value.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' '),
)

const areaPath = computed(() => {
  const pts = points.value
  if (pts.length === 0) return ''
  const baseline = H - padB
  const line = pts.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ')
  return `${line} L ${pts[pts.length - 1].x} ${baseline} L ${pts[0].x} ${baseline} Z`
})
</script>

<style scoped>
.chart-panel {
  display: flex;
  flex-direction: column;
}

.chart-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.chart-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.88);
}

.chart-sub {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.45);
}

.chart-empty {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.4);
  padding: 1.5rem 0;
  text-align: center;
}

.chart-svg {
  width: 100%;
  height: auto;
  overflow: visible;
}

.grid-line {
  stroke: rgba(255, 255, 255, 0.08);
  stroke-width: 1;
}

.axis-label {
  fill: rgba(255, 255, 255, 0.45);
  font-size: 9px;
}

.y-label {
  text-anchor: end;
}

.x-label {
  text-anchor: middle;
}

.area {
  fill: rgba(120, 170, 255, 0.14);
}

.line {
  fill: none;
  stroke: rgba(140, 185, 255, 0.9);
  stroke-width: 2;
  stroke-linejoin: round;
  stroke-linecap: round;
}

.dot {
  fill: rgba(180, 210, 255, 1);
  stroke: rgba(20, 30, 50, 0.6);
  stroke-width: 1;
}
</style>
