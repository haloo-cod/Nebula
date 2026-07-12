<template>
  <PageBackground>
    <div class="page-wrap">
      <div class="timeline-wrap post-rise-inner">
        <div class="timeline-viewport">
          <div class="timeline-stage" :style="stageStyle">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="river-svg"
              :width="trackW"
              :height="svgH"
              :viewBox="`0 0 ${trackW} ${svgH}`"
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
            </svg>

            <RouterLink
              v-for="(post, i) in posts"
              :key="post.slug"
              :to="`/archive/post/${post.slug}`"
              class="archive-link"
              :style="cardStyle(i)"
            >
              <div v-if="!ui.liquidGlassEnabled" class="archive-panel">
                <ArchivePostCard :post="post" />
              </div>

              <LazyLiquidGlass
                v-else
                class="archive-glass"
                :corner-radius="16"
                :theme="ui.theme"
                :blur-radius="ui.liquidGlassBlur"
                :ripple-trail="true"
                realtime-offset
              >
                <ArchivePostCard :post="post" />
              </LazyLiquidGlass>
            </RouterLink>
          </div>
        </div>
      </div>
    </div>
  </PageBackground>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import PageBackground from '@/components/PageBackground.vue'
import LazyLiquidGlass from '@/components/liquid-glass/LazyLiquidGlass.vue'
import { getPosts } from '@/data/posts'
import { useUIStore } from '@/stores/ui'
import ArchivePostCard from './ArchivePostCard.vue'

const ui = useUIStore()
const posts = getPosts().filter((p) => !p.draft)

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
const stageStyle = computed(() => ({
  width: `${trackW.value}px`,
  height: `${svgH.value}px`,
}))

// ============ 河流路径 ============
function waveY(t: number): number {
  return (
    Math.sin(t * Math.PI * 1.5) * riverAmplitude * 0.6 +
    Math.sin(t * Math.PI * 3.7 + 0.8) * riverAmplitude * 0.3 +
    Math.sin(t * Math.PI * 6.1 + 2.3) * riverAmplitude * 0.15
  )
}

const riverPath = computed(() => {
  if (posts.length === 0) return 'M 0 0'
  const total = trackW.value
  const y = riverCenterY.value
  const steps = 80
  let d = `M 0 ${y} `
  for (let i = 0; i <= steps; i++) {
    const t = i / steps
    const x = total * t
    d += `L ${x.toFixed(1)} ${(y + waveY(t)).toFixed(1)} `
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
    return { x, y: riverCenterY.value + waveY(t) }
  })
})

function cardStyle(index: number) {
  const node = nodes.value[index]
  if (!node) return {}
  const top = index % 2 === 0 ? node.y - connLen - cardH : node.y + connLen
  return {
    left: `${node.x - cardW / 2}px`,
    top: `${top}px`,
    width: `${cardW}px`,
    height: `${cardH}px`,
  }
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
    transform: translateY(40px);
  }
  to {
    transform: none;
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

.timeline-stage {
  position: relative;
  min-width: 100%;
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
  position: absolute;
  inset: 0;
  overflow: visible;
}

.archive-link {
  position: absolute;
  display: block;
  border-radius: 1rem;
  overflow: visible;
  z-index: 5;
}

.archive-link:hover {
  transform: translateY(-3px);
}

.archive-glass {
  width: 100%;
  height: 100%;
  transition:
    transform 0.24s ease,
    filter 0.24s ease;
}

.archive-panel {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  min-width: 0;
  border-radius: 1rem;
  padding: 0.45rem;
  color: inherit;
  text-decoration: none;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow:
    0 8px 28px rgba(0, 0, 0, 0.18),
    inset 0 1px 0 rgba(255, 255, 255, 0.24),
    inset 0 0 20px rgba(255, 255, 255, 0.06);
  overflow: hidden;
  position: relative;
  transition:
    transform 0.24s ease,
    filter 0.24s ease;
}

.archive-link:hover .archive-glass {
  transform: translateY(-3px);
  filter: drop-shadow(0 16px 34px rgba(80, 140, 255, 0.18));
}

.archive-link:hover .archive-panel {
  transform: translateY(-3px);
  filter: drop-shadow(0 8px 24px rgba(80, 140, 255, 0.14));
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

/* ===== 移动端 ===== */
@media (max-width: 767px) {
  .page-wrap {
    padding-top: 6rem;
    padding-bottom: 2rem;
    padding-left: 0.75rem;
    padding-right: 0.75rem;
    min-height: auto;
  }
}
</style>
