<template>
  <div class="carousel">
    <div v-if="images.length > 0" class="carousel-viewport">
      <div class="carousel-track" ref="trackRef" :style="trackStyle">
        <!-- 尾部克隆：最后一张 -->
        <img :src="images[images.length - 1]" class="carousel-slide clone" loading="eager" />
        <!-- 真实图片 -->
        <img
          v-for="(img, i) in images"
          :key="i"
          :src="img"
          :alt="`slide ${i + 1}`"
          class="carousel-slide"
          :loading="i < 2 ? 'eager' : 'lazy'"
        />
        <!-- 头部克隆：第一张 -->
        <img :src="images[0]" class="carousel-slide clone" loading="eager" />
      </div>
    </div>
    <div v-else class="carousel-empty">暂无轮播图片</div>
    <div v-if="images.length > 1" class="carousel-dots">
      <span
        v-for="(_, i) in images"
        :key="i"
        class="carousel-dot"
        :class="{ active: i === currentIndex }"
        @click="goTo(i)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { fetchCarouselSlides } from '@/api/carousel'

const fallbackImages = import.meta.glob<string>(
  '../../assets/carousel/*.{png,PNG,jpg,JPG,jpeg,webp,WEBP}',
  {
    query: '?url',
    import: 'default',
    eager: true,
  },
)

const images = ref<string[]>(Object.values(fallbackImages))

const currentIndex = ref(0)
const autoPlayTimer = ref<number | null>(null)
const transitioning = ref(false)
const trackRef = ref<HTMLElement | null>(null)
const INTERVAL = 4000
const TRANSITION_DURATION = 500
const TRANSITION_FALLBACK_DELAY = TRANSITION_DURATION + 100
let transitionFallbackTimer: number | null = null

// 真实图片从 index=1 开始（前面有一个尾部克隆）
const OFFSET = 1

const trackStyle = computed(() => ({
  transform: `translateX(-${(currentIndex.value + OFFSET) * 100}%)`,
  transition: transitioning.value ? 'transform 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94)' : 'none',
}))

function goTo(index: number) {
  if (transitioning.value) return
  transitioning.value = true
  currentIndex.value = index
  scheduleTransitionFallback()
  resetAutoPlay()
}

function next() {
  if (transitioning.value) return
  transitioning.value = true
  currentIndex.value += 1
  scheduleTransitionFallback()
  resetAutoPlay()
}

function clearTransitionFallback() {
  if (transitionFallbackTimer !== null) {
    window.clearTimeout(transitionFallbackTimer)
    transitionFallbackTimer = null
  }
}

function scheduleTransitionFallback() {
  clearTransitionFallback()
  transitionFallbackTimer = window.setTimeout(finishTransition, TRANSITION_FALLBACK_DELAY)
}

// transitionend 可能因页面重排或组件不可见而丢失，超时回调负责兜底解锁。
function finishTransition() {
  clearTransitionFallback()
  if (currentIndex.value === images.value.length) {
    transitioning.value = false
    currentIndex.value = 0
    void trackRef.value?.offsetWidth
  } else {
    transitioning.value = false
  }
}

function onTransitionEnd(event: TransitionEvent) {
  if (event.propertyName === 'transform') finishTransition()
}

function onTransitionCancel(event: TransitionEvent) {
  if (event.propertyName === 'transform') finishTransition()
}

function resetAutoPlay() {
  if (autoPlayTimer.value) clearInterval(autoPlayTimer.value)
  autoPlayTimer.value = window.setInterval(next, INTERVAL)
}

onMounted(async () => {
  trackRef.value?.addEventListener('transitionend', onTransitionEnd)
  trackRef.value?.addEventListener('transitioncancel', onTransitionCancel)
  // 即使 API 不可用，也应让本地 fallback 图片自动播放。
  resetAutoPlay()
  // 尝试从后端 API 加载轮播图列表
  try {
    const slides = await fetchCarouselSlides()
    if (slides.length > 0) {
      clearTransitionFallback()
      transitioning.value = false
      images.value = slides
      // 重置索引避免越界
      currentIndex.value = 0
      resetAutoPlay()
    }
  } catch {
    // API 失败时保留本地预览图片
  }
})

onUnmounted(() => {
  trackRef.value?.removeEventListener('transitionend', onTransitionEnd)
  trackRef.value?.removeEventListener('transitioncancel', onTransitionCancel)
  if (autoPlayTimer.value) clearInterval(autoPlayTimer.value)
  clearTransitionFallback()
})
</script>

<style scoped>
.carousel {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  border-radius: 14px;
  padding: 20px;
  box-sizing: border-box;
}

.carousel-viewport {
  width: 100%;
  height: 100%;
  overflow: hidden;
  border-radius: 8px;
}

.carousel-empty {
  display: grid;
  width: 100%;
  height: 100%;
  place-items: center;
  color: var(--text-muted);
  font-size: 0.85rem;
}

.carousel-track {
  display: flex;
  height: 100%;
  will-change: transform;
}

.carousel-slide {
  flex: 0 0 100%;
  width: 100%;
  height: 100%;
  object-fit: cover;
  user-select: none;
  -webkit-user-drag: none;
}

.carousel-dots {
  position: absolute;
  bottom: 14px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 8px;
  z-index: 2;
}

.carousel-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.35);
  cursor: pointer;
  transition: all 0.3s ease;
}

.carousel-dot.active {
  background: rgba(255, 255, 255, 0.95);
  width: 18px;
  border-radius: 3px;
}
</style>
