<template>
  <div class="moments-page" data-background-credit-boundary>
    <!-- 页头 -->
    <header class="moments-header post-rise-inner">
      <p class="moments-kicker">{{ siteText.moments.kicker }}</p>
      <h1 class="moments-title">{{ siteText.moments.title }}</h1>
      <p class="moments-desc">{{ siteText.moments.subtitle }}</p>
      <span class="moments-count">共 {{ total }} 条</span>
    </header>

    <!-- 时间线区域 -->
    <div class="moments-timeline">
      <template v-for="(group, gi) in dayGroups" :key="group.date">
        <div
          class="moments-day-divider post-rise-inner"
          :style="{ animationDelay: `${gi * 0.08 + 0.2}s` }"
        >
          <span class="moments-day-line"></span>
          <span class="moments-day-label">{{ group.label }} · {{ group.moments.length }}条</span>
          <span class="moments-day-line"></span>
        </div>
        <div
          v-for="(moment, mi) in group.moments"
          :key="moment.id"
          :id="`moment-${moment.id}`"
          class="moments-card-wrap"
          :class="{ 'moments-card-highlight': highlightId === moment.id }"
        >
          <LazyLiquidGlass
            v-if="ui.liquidGlassEnabled"
            class="moments-glass post-rise-inner"
            :style="{ animationDelay: `${gi * 0.08 + mi * 0.06 + 0.3}s` }"
            :corner-radius="18"
            :theme="ui.theme"
            :blur-radius="ui.liquidGlassBlur"
            :ripple-trail="true"
            realtime-offset
          >
            <MomentCard :moment="moment" @select="openDetail" />
          </LazyLiquidGlass>
          <PanelFallbackGlass
            v-else
            class="moments-panel post-rise-inner"
            :style="{ animationDelay: `${gi * 0.08 + mi * 0.06 + 0.3}s` }"
          >
            <MomentCard :moment="moment" @select="openDetail" />
          </PanelFallbackGlass>
        </div>
      </template>

      <div ref="sentinelRef" class="moments-sentinel">
        <span v-if="loadingMore" class="moments-loading">加载中...</span>
        <span v-else-if="noMore" class="moments-no-more">— 没有更多了 —</span>
      </div>
    </div>
  </div>
  <MomentDetail :moment="selectedMoment" @close="closeDetail" />
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import LazyLiquidGlass from '@/components/liquid-glass/LazyLiquidGlass.vue'
import PanelFallbackGlass from '@/components/panels/PanelFallbackGlass.vue'
import { useUIStore } from '@/stores/ui'
import { fetchMoments } from '@/api/moments'
import { siteText } from '@/data/site-text'
import type { Moment } from '@/types'
import MomentCard from './MomentCard.vue'
import MomentDetail from './MomentDetail.vue'
import { formatMomentDate } from '@/utils/momentDate'

const ui = useUIStore()
const route = useRoute()
const highlightId = ref<number | null>(null)
const selectedMoment = ref<Moment | null>(null)

function openDetail(moment: Moment) {
  selectedMoment.value = moment
}

function closeDetail() {
  selectedMoment.value = null
}

const PAGE_SIZE = 10
const allLoaded = ref<Moment[]>([])
const total = ref(0)
const currentPage = ref(0)
const loadingMore = ref(false)
const noMore = ref(false)
const sentinelRef = ref<HTMLElement | null>(null)
let observer: IntersectionObserver | null = null

async function loadNextPage() {
  if (loadingMore.value || noMore.value) return
  loadingMore.value = true
  currentPage.value++
  try {
    const res = await fetchMoments(currentPage.value, PAGE_SIZE)
    total.value = res.total
    allLoaded.value = [...allLoaded.value, ...res.items]
  } catch {
    total.value = 0
    noMore.value = true
  }
  if (allLoaded.value.length >= total.value) noMore.value = true
  loadingMore.value = false
}

interface DayGroup {
  date: string
  label: string
  moments: Moment[]
}

const dayGroups = computed<DayGroup[]>(() => {
  const map = new Map<string, Moment[]>()
  for (const moment of allLoaded.value) {
    const date = formatMomentDate(moment.date).slice(0, 10)
    if (!map.has(date)) map.set(date, [])
    map.get(date)!.push(moment)
  }
  return Array.from(map.entries()).map(([date, moments]) => ({
    date,
    label: formatDayLabel(date),
    moments,
  }))
})

function formatDayLabel(date: string): string {
  const [, month, day] = date.split('-').map(Number)
  return Number.isNaN(month) || Number.isNaN(day) ? '' : `${month}月${day}日`
}

onMounted(async () => {
  await loadNextPage()
  const hashMatch = route.hash.match(/^#moment-(\d+)$/)
  if (hashMatch) {
    const targetId = Number(hashMatch[1])
    while (!allLoaded.value.some((moment) => moment.id === targetId) && !noMore.value) {
      await loadNextPage()
    }
    nextTick(() => {
      const element = document.getElementById(`moment-${targetId}`)
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' })
        highlightId.value = targetId
        setTimeout(() => {
          highlightId.value = null
        }, 2000)
      }
    })
  }
  if (!sentinelRef.value) return
  observer = new IntersectionObserver(
    ([entry]) => {
      if (entry.isIntersecting) void loadNextPage()
    },
    { root: null, rootMargin: '200px', threshold: 0.01 },
  )
  observer.observe(sentinelRef.value)
})

onUnmounted(() => observer?.disconnect())
</script>

<style scoped>
.moments-page {
  position: relative;
  z-index: 10;
  width: 100%;
  max-width: 42rem;
  margin: 0 auto;
  padding: 6rem 1rem 3rem;
}

@media (min-width: 768px) {
  .moments-page { padding-top: 8rem; }
}

.moments-header { margin-bottom: 2.5rem; }
.moments-kicker {
  margin: 0 0 0.25rem;
  color: rgba(160, 205, 255, 0.7);
  font-size: 0.72rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}
.moments-title {
  margin: 0;
  color: var(--text-primary);
  font-size: 1.6rem;
  font-weight: 700;
  letter-spacing: 0.06em;
}
.moments-desc { margin: 0.4rem 0 0; color: var(--text-secondary); font-size: 0.86rem; }
.moments-count {
  display: inline-block;
  margin-top: 0.5rem;
  padding: 0.2rem 0.6rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: var(--text-muted);
  font-size: 0.72rem;
  font-variant-numeric: tabular-nums;
}
.moments-timeline { display: flex; flex-direction: column; gap: 1rem; }
.moments-day-divider { display: flex; align-items: center; gap: 0.8rem; padding: 0.6rem 0; }
.moments-day-line {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(140, 200, 255, 0.2), transparent);
}
.moments-day-label {
  color: var(--text-secondary);
  font-size: 0.78rem;
  font-weight: 600;
  white-space: nowrap;
  letter-spacing: 0.04em;
}
.moments-card-wrap { width: 100%; min-width: 0; }
.moments-card-highlight { animation: momentHighlight 2s ease-out; }
@keyframes momentHighlight {
  0%, 20% {
    box-shadow: 0 0 0 2px rgba(140, 200, 255, 0.6), 0 0 24px rgba(140, 200, 255, 0.3);
    border-radius: 1.1rem;
  }
  100% { box-shadow: 0 0 0 0 transparent, 0 0 0 transparent; }
}
.moments-glass {
  width: 100%;
  overflow: hidden;
  border-radius: 1.1rem;
  transition: transform 0.24s ease, filter 0.24s ease;
}
.moments-glass :deep(.liquid-glass-content) { padding: 0; min-width: 0; overflow: hidden; height: auto; }
.moments-glass :deep(.liquid-glass) { height: auto; }
.moments-panel {
  width: 100%;
  border-radius: 1rem;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  transition: border-color 0.25s ease, box-shadow 0.25s ease;
}
.moments-panel:hover {
  border-color: rgba(140, 185, 255, 0.2);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.24), inset 0 0 20px rgba(255, 255, 255, 0.06), 0 12px 36px rgba(80, 120, 255, 0.1);
}
.moments-sentinel { display: flex; justify-content: center; padding: 2rem 0 1rem; }
.moments-loading { color: var(--text-muted); font-size: 0.82rem; }
.moments-no-more { color: var(--text-faint); font-size: 0.78rem; }
.post-rise-inner { animation: contentRise 0.55s cubic-bezier(0.22, 1, 0.36, 1) both; }
@keyframes contentRise {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: none; }
}
@media (prefers-reduced-motion: reduce) {
  .post-rise-inner { opacity: 1; transform: none; animation: none; }
}
@media (max-width: 767px) {
  .moments-page { padding-top: 5rem; padding-left: 0.75rem; padding-right: 0.75rem; }
}
</style>
