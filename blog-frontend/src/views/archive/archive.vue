<template>
  <PageBackground>
    <div class="page-wrap">
      <div class="timeline-wrap post-rise-inner">
        <div class="timeline-viewport">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="river-svg"
            :width="svgW"
            :height="svgH"
            :viewBox="`0 0 ${svgW} ${svgH}`"
          >
            <defs>
              <linearGradient id="river-grad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="rgba(56,189,248,0.08)" />
                <stop offset="20%" stop-color="rgba(99,179,237,0.6)" />
                <stop offset="50%" stop-color="rgba(129,140,248,0.7)" />
                <stop offset="80%" stop-color="rgba(167,139,250,0.5)" />
                <stop offset="100%" stop-color="rgba(56,189,248,0.08)" />
              </linearGradient>
            </defs>

            <!-- 外层大发光 -->
            <path :d="riverPath" class="river-glow-outer" />
            <!-- 中层发光 -->
            <path :d="riverPath" class="river-glow-mid" />
            <!-- 内层发光 -->
            <path :d="riverPath" class="river-glow-inner" />
            <!-- 主曲线 -->
            <path :d="riverPath" class="river-path" />
            <!-- 流动粒子 -->
            <circle class="particle" r="4">
              <animateMotion dur="14s" repeatCount="indefinite" :path="riverPath" begin="0s" />
            </circle>
            <circle class="particle" r="3.5">
              <animateMotion dur="18s" repeatCount="indefinite" :path="riverPath" begin="5s" />
            </circle>
            <circle class="particle" r="3">
              <animateMotion dur="16s" repeatCount="indefinite" :path="riverPath" begin="9s" />
            </circle>

            <!-- 连接线 -->
            <line
              v-for="(n, i) in nodes"
              :key="'cl' + i"
              :x1="n.x"
              :y1="n.y"
              :x2="n.x"
              :y2="i % 2 === 0 ? n.y - connLen : n.y + connLen"
              class="conn-line"
            />
            <!-- 节点 -->
            <circle
              v-for="(n, i) in nodes"
              :key="'nd' + i"
              :cx="n.x"
              :cy="n.y"
              r="6"
              class="node-dot"
            />
            <circle
              v-for="(n, i) in nodes"
              :key="'ng' + i"
              :cx="n.x"
              :cy="n.y"
              r="14"
              class="node-glow"
            />

            <!-- 卡片(foreignObject) -->
            <foreignObject
              v-for="(post, i) in posts"
              :key="'fo' + post.slug"
              :x="nodes[i].x - cardW / 2"
              :y="i % 2 === 0 ? nodes[i].y - connLen - cardH : nodes[i].y + connLen"
              :width="cardW"
              :height="cardH"
            >
              <RouterLink
                :to="`/archive/post/${post.slug}`"
                class="post-card"
                xmlns="http://www.w3.org/1999/xhtml"
              >
                <div class="card-cover" :style="{ background: coverGradient(i) }">
                  <span class="card-cover-date">{{ formatDate(post.date) }}</span>
                </div>
                <div class="card-body">
                  <h3 class="card-title">{{ post.title }}</h3>
                  <p v-if="post.description" class="card-desc">{{ post.description }}</p>
                  <span
                    v-if="post.category"
                    class="card-cat"
                    :class="'cat-' + catColorKey(post.category)"
                    >{{ post.category }}</span
                  >
                </div>
              </RouterLink>
            </foreignObject>
          </svg>
        </div>
      </div>
    </div>
  </PageBackground>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import PageBackground from '@/components/PageBackground.vue'
import { getPosts } from '@/data/posts'

const posts = getPosts().filter((p) => !p.draft)

// ============ 封面渐变池 ============
const gradients = [
  'linear-gradient(135deg, #1e293b, #334155)',
  'linear-gradient(135deg, #1e293b, #0f3460)',
  'linear-gradient(135deg, #1e293b, #1a365d)',
  'linear-gradient(135deg, #0f172a, #1e3a5f)',
  'linear-gradient(135deg, #1e293b, #2d1b4e)',
]

function coverGradient(i: number): string {
  return gradients[i % gradients.length]
}

// ============ 分类色标 ============
const categoryColors: Record<string, string> = {
  技术: 'cyan',
  生活: 'violet',
  随笔: 'pink',
  项目: 'emerald',
  教程: 'blue',
  前端: 'sky',
  后端: 'indigo',
  AI: 'purple',
  Rust: 'orange',
  工具: 'teal',
  算法: 'rose',
  日记: 'amber',
}

function catColorKey(cat: string): string {
  return categoryColors[cat] || 'slate'
}

// ============ 布局参数 ============
const cardW = 280
const cardH = 310
const cardGap = 40
const sidePad = 24
const riverYTop = 40
const riverYBot = 40
const connLen = 18
const riverAmplitude = 46

const postX = (i: number) => sidePad + i * (cardW + cardGap)

const trackW = computed(() =>
  posts.length > 0 ? sidePad * 2 + posts.length * (cardW + cardGap) - cardGap : 600,
)

const riverCenterY = computed(() => riverYTop + cardH + connLen)
const svgH = computed(() => riverYTop + cardH + connLen + connLen + cardH + riverYBot)
const svgW = trackW

// ============ 河流路径 ============
const riverPath = computed(() => {
  if (posts.length === 0) return 'M 0 0'
  const total = trackW.value
  const y = riverCenterY.value
  const steps = 80
  let d = `M 0 ${y} `
  for (let i = 0; i <= steps; i++) {
    const t = i / steps
    const x = total * t
    const dy =
      Math.sin(t * Math.PI * 1.5) * riverAmplitude * 0.6 +
      Math.sin(t * Math.PI * 3.7 + 0.8) * riverAmplitude * 0.3 +
      Math.sin(t * Math.PI * 6.1 + 2.3) * riverAmplitude * 0.15
    d += `L ${x.toFixed(1)} ${(y + dy).toFixed(1)} `
  }
  return d
})

// ============ 节点位置 ============
interface NodePoint {
  x: number
  y: number
}

const nodes = computed<NodePoint[]>(() => {
  if (posts.length === 0) return []
  return posts.map((_, i) => {
    const x = postX(i) + cardW / 2
    const t = x / Math.max(1, trackW.value)
    const dy =
      Math.sin(t * Math.PI * 1.5) * riverAmplitude * 0.6 +
      Math.sin(t * Math.PI * 3.7 + 0.8) * riverAmplitude * 0.3 +
      Math.sin(t * Math.PI * 6.1 + 2.3) * riverAmplitude * 0.15
    return { x, y: riverCenterY.value + dy }
  })
})

// ============ 日期格式化 ============
function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return dateStr
  return `${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}
</script>

<style scoped>
.page-wrap {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: 100vh;
  position: relative;
  z-index: 10;
  width: 100%;
  max-width: 96rem;
  margin: 0 auto;
  padding: 5rem 1rem 2rem;
}

@media (min-width: 768px) {
  .page-wrap {
    padding-top: 6rem;
    padding-bottom: 4rem;
  }
}

/* ===== 时间轴外容器 ===== */
.timeline-wrap {
  position: relative;
  flex: 1;
  display: flex;
  align-items: center;
}

/* ===== 入场动画 ===== */
.post-rise-inner {
  animation: contentRise 0.6s cubic-bezier(0.22, 1, 0.36, 1) both;
  animation-delay: 0.15s;
}

@keyframes contentRise {
  from {
    opacity: 0;
    transform: translateY(40px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (prefers-reduced-motion: reduce) {
  .post-rise-inner {
    animation: none;
  }
}

/* ===== 横向滚动视口 ===== */
.timeline-viewport {
  overflow-x: auto;
  overflow-y: hidden;
}

.timeline-viewport::-webkit-scrollbar {
  height: 4px;
}

.timeline-viewport::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.02);
  border-radius: 2px;
}

.timeline-viewport::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 2px;
}

/* ===== SVG 河流 ===== */
.river-svg {
  display: block;
  overflow: visible;
}

.river-glow-outer {
  fill: none;
  stroke: rgba(99, 179, 237, 0.12);
  stroke-width: 36;
  stroke-linejoin: round;
  filter: blur(20px);
}

.river-glow-mid {
  fill: none;
  stroke: rgba(99, 179, 237, 0.22);
  stroke-width: 20;
  stroke-linejoin: round;
  filter: blur(10px);
}

.river-glow-inner {
  fill: none;
  stroke: rgba(167, 139, 250, 0.3);
  stroke-width: 10;
  stroke-linejoin: round;
  filter: blur(5px);
}

.river-path {
  fill: none;
  stroke: url(#river-grad);
  stroke-width: 6;
  stroke-linejoin: round;
  stroke-linecap: round;
  filter: drop-shadow(0 0 10px rgba(99, 179, 237, 0.4));
}

.node-dot {
  fill: rgba(255, 255, 255, 1);
  stroke: rgba(99, 179, 237, 0.7);
  stroke-width: 3;
}

.node-glow {
  fill: none;
  stroke: rgba(99, 179, 237, 0.3);
  stroke-width: 3;
}

.conn-line {
  stroke: rgba(148, 163, 184, 0.4);
  stroke-width: 2;
  stroke-dasharray: 5 5;
}

/* ===== 流动粒子 ===== */
.particle {
  fill: rgba(200, 230, 255, 0.85);
  filter: drop-shadow(0 0 6px rgba(99, 179, 237, 0.6));
}

/* ===== 卡片(foreignObject 内) ===== */
.post-card {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  border-radius: 1rem;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  border: 1px solid rgba(255, 255, 255, 0.07);
  overflow: hidden;
  text-decoration: none;
  transition:
    transform 0.3s ease,
    border-color 0.3s ease,
    box-shadow 0.3s ease,
    background 0.3s ease;
  color: inherit;
}

.post-card:hover {
  transform: translateY(-3px);
  background: rgba(255, 255, 255, 0.09);
  border-color: rgba(99, 179, 237, 0.4);
  box-shadow:
    0 12px 36px rgba(59, 130, 246, 0.18),
    0 0 20px rgba(99, 179, 237, 0.08);
}

.card-cover {
  position: relative;
  height: 130px;
  flex-shrink: 0;
}

.card-cover-date {
  position: absolute;
  bottom: 10px;
  right: 10px;
  font-size: 0.82rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.75);
  background: rgba(0, 0, 0, 0.4);
  padding: 3px 10px;
  border-radius: 4px;
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.04em;
}

.card-body {
  display: flex;
  flex-direction: column;
  flex: 1;
  padding: 0 1rem 0.85rem;
}

.card-title {
  font-size: 1.05rem;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.92);
  line-height: 1.45;
  margin: 0;
  padding: 0.75rem 0 0.35rem;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-desc {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.55);
  line-height: 1.55;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  flex: 1;
}

.card-cat {
  font-size: 0.78rem;
  padding: 0.2rem 0.6rem;
  border-radius: 999px;
  border: 1px solid;
  display: inline-block;
  margin-top: 0.35rem;
  align-self: flex-start;
}

/* 分类颜色 */
.cat-cyan {
  color: rgba(34, 211, 238, 0.9);
  background: rgba(34, 211, 238, 0.1);
  border-color: rgba(34, 211, 238, 0.25);
}

.cat-violet {
  color: rgba(167, 139, 250, 0.9);
  background: rgba(167, 139, 250, 0.1);
  border-color: rgba(167, 139, 250, 0.25);
}

.cat-pink {
  color: rgba(244, 114, 182, 0.9);
  background: rgba(244, 114, 182, 0.1);
  border-color: rgba(244, 114, 182, 0.25);
}

.cat-emerald {
  color: rgba(52, 211, 153, 0.9);
  background: rgba(52, 211, 153, 0.1);
  border-color: rgba(52, 211, 153, 0.25);
}

.cat-blue {
  color: rgba(96, 165, 250, 0.9);
  background: rgba(96, 165, 250, 0.1);
  border-color: rgba(96, 165, 250, 0.25);
}

.cat-sky {
  color: rgba(56, 189, 248, 0.9);
  background: rgba(56, 189, 248, 0.1);
  border-color: rgba(56, 189, 248, 0.25);
}

.cat-indigo {
  color: rgba(129, 140, 248, 0.9);
  background: rgba(129, 140, 248, 0.1);
  border-color: rgba(129, 140, 248, 0.25);
}

.cat-purple {
  color: rgba(168, 85, 247, 0.9);
  background: rgba(168, 85, 247, 0.1);
  border-color: rgba(168, 85, 247, 0.25);
}

.cat-orange {
  color: rgba(251, 146, 60, 0.9);
  background: rgba(251, 146, 60, 0.1);
  border-color: rgba(251, 146, 60, 0.25);
}

.cat-teal {
  color: rgba(45, 212, 191, 0.9);
  background: rgba(45, 212, 191, 0.1);
  border-color: rgba(45, 212, 191, 0.25);
}

.cat-rose {
  color: rgba(251, 113, 133, 0.9);
  background: rgba(251, 113, 133, 0.1);
  border-color: rgba(251, 113, 133, 0.25);
}

.cat-amber {
  color: rgba(252, 211, 77, 0.9);
  background: rgba(252, 211, 77, 0.1);
  border-color: rgba(252, 211, 77, 0.25);
}

.cat-slate {
  color: rgba(148, 163, 184, 0.85);
  background: rgba(148, 163, 184, 0.08);
  border-color: rgba(148, 163, 184, 0.2);
}

/* ===== 移动端 ===== */
@media (max-width: 767px) {
  .page-wrap {
    padding-top: 6rem;
    padding-bottom: 2rem;
    padding-left: 0.75rem;
    padding-right: 0.75rem;
    min-height: auto;
  }

  .card-cover {
    height: 100px;
  }

  .card-title {
    font-size: 0.92rem;
  }

  .card-desc {
    font-size: 0.78rem;
  }

  .card-cat {
    font-size: 0.72rem;
  }
}
</style>
