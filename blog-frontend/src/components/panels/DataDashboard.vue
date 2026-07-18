<template>
  <div class="data-dashboard">
    <div class="dashboard-header">
      <span class="dashboard-title">访客统计</span>
      <span class="dashboard-sub">Visitors</span>
    </div>

    <div class="metrics-grid">
      <div class="metric-card">
        <span class="metric-value">{{ formatNum(totalVisitors) }}</span>
        <span class="metric-label">总访客</span>
      </div>
      <div class="metric-card">
        <span class="metric-value">{{ formatNum(todayVisitors) }}</span>
        <span class="metric-label">今日访客</span>
      </div>
      <div class="metric-card">
        <span class="metric-value">{{ formatNum(totalViews) }}</span>
        <span class="metric-label">总浏览</span>
      </div>
      <div class="metric-card">
        <span class="metric-value">{{ formatNum(todayViews) }}</span>
        <span class="metric-label">今日浏览</span>
      </div>
    </div>

    <div class="chart-section">
      <div class="chart-header">
        <span class="chart-title">近7天访客</span>
      </div>

      <svg
        class="chart-svg"
        :viewBox="`0 0 ${W} ${H}`"
        preserveAspectRatio="none"
        role="img"
        aria-label="近7天访客趋势图"
      >
        <g class="grid">
          <template v-for="t in yTicks" :key="t.value">
            <line :x1="padL" :y1="t.y" :x2="W - padR" :y2="t.y" class="grid-line" />
            <text :x="padL - 4" :y="t.y + 3" class="axis-label y-label">{{ t.value }}</text>
          </template>
        </g>

        <path :d="areaPath" class="area" />
        <path :d="linePath" class="line" />

        <g>
          <template v-for="(p, i) in points" :key="i">
            <circle :cx="p.x" :cy="p.y" r="3" class="dot" />
            <text :x="p.x" :y="H - padB + 13" class="axis-label x-label">{{ p.label }}</text>
          </template>
        </g>
      </svg>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

// 模拟访客数据（后端接入后替换为 API 请求）
const mockVisitors = [
  { label: '周一', value: 128 },
  { label: '周二', value: 156 },
  { label: '周三', value: 142 },
  { label: '周四', value: 189 },
  { label: '周五', value: 213 },
  { label: '周六', value: 267 },
  { label: '周日', value: 245 },
]

const totalVisitors = 12847
const todayVisitors = 245
const totalViews = 38621
const todayViews = 812

function formatNum(n: number): string {
  if (n >= 10000) return (n / 10000).toFixed(1) + 'w'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k'
  return String(n)
}

// SVG 坐标系
const W = 260
const H = 130
const padL = 26
const padR = 10
const padT = 12
const padB = 22

const maxVal = computed(() => Math.max(1, ...mockVisitors.map((d) => d.value)))

interface YTick {
  value: number
  y: number
}

interface ChartPoint {
  x: number
  y: number
  label: string
  value: number
}

const yTicks = computed<YTick[]>(() => {
  const max = maxVal.value
  const step = Math.max(1, Math.ceil(max / 3))
  const ticks: YTick[] = []
  for (let v = 0; v <= max; v += step) {
    const y = padT + (H - padT - padB) * (1 - v / max)
    ticks.push({ value: v, y })
  }
  return ticks
})

const points = computed<ChartPoint[]>(() => {
  const list = mockVisitors
  if (list.length === 0) return []
  const innerW = W - padL - padR
  const innerH = H - padT - padB
  const max = maxVal.value
  return list.map((d, i) => {
    const x = list.length === 1 ? padL + innerW / 2 : padL + (innerW * i) / (list.length - 1)
    const y = padT + innerH * (1 - d.value / max)
    return { x, y, label: d.label, value: d.value }
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
.data-dashboard {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  padding: 1rem;
  box-sizing: border-box;
}

.dashboard-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  /* margin-bottom: 0.2rem; */
}

.dashboard-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.92);
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.6);
}

.dashboard-sub {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.4);
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.4rem;
}

.metric-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.1rem;
  padding: 0.45rem 0.2rem;
  border-radius: 0.5rem;
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  border: 1px solid rgba(255, 255, 255, 0.15);
}

.metric-value {
  font-size: 1.15rem;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
  line-height: 1.1;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.6);
}

.metric-label {
  font-size: 0.6rem;
  color: rgba(255, 255, 255, 0.55);
  letter-spacing: 0.05em;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

.chart-section {
  display: flex;
  flex-direction: column;
}

.chart-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 0.3rem;
}

.chart-title {
  font-size: 0.78rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

.chart-svg {
  width: 100%;
  height: auto;
  overflow: visible;
}

.grid-line {
  stroke: rgba(255, 255, 255, 0.12);
  stroke-width: 1;
}

.axis-label {
  fill: rgba(255, 255, 255, 0.9);
  font-size: 9px;
  font-weight: 600;
  paint-order: stroke;
  stroke: rgba(0, 0, 0, 0.5);
  stroke-width: 0.5;
}

.y-label {
  text-anchor: end;
  font-size: 9px;
}

.x-label {
  text-anchor: middle;
  font-size: 10px;
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
