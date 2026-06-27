<template>
  <div class="carousel">
    <div class="carousel-track" :style="trackStyle">
      <!-- 尾部克隆：最后一张 -->
      <img
        :src="images[images.length - 1]"
        class="carousel-slide clone"
        loading="lazy"
      />
      <!-- 真实图片 -->
      <img
        v-for="(img, i) in images"
        :key="i"
        :src="img"
        :alt="`slide ${i + 1}`"
        class="carousel-slide"
        loading="lazy"
      />
      <!-- 头部克隆：第一张 -->
      <img
        :src="images[0]"
        class="carousel-slide clone"
        loading="lazy"
      />
    </div>
    <div class="carousel-dots">
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

const images = [
  new URL('@/assets/img2/01.PNG', import.meta.url).href,
  new URL('@/assets/img2/02.PNG', import.meta.url).href,
  new URL('@/assets/img2/03.PNG', import.meta.url).href,
  new URL('@/assets/img2/04.PNG', import.meta.url).href,
  new URL('@/assets/img2/05.PNG', import.meta.url).href,
  new URL('@/assets/img2/06.JPG', import.meta.url).href,
  new URL('@/assets/img2/07.PNG', import.meta.url).href,
]

const currentIndex = ref(0)
const autoPlayTimer = ref<number | null>(null)
const transitioning = ref(false)
const INTERVAL = 4000

// 真实图片从 index=1 开始（前面有一个尾部克隆）
const OFFSET = 1

const trackStyle = computed(() => ({
  transform: `translateX(-${(currentIndex.value + OFFSET) * 100}%)`,
  transition: transitioning.value ? 'transform 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94)' : 'none',
}))

function goTo(index: number) {
  if (transitioning.value) return
  currentIndex.value = index
  resetAutoPlay()
}

function next() {
  if (transitioning.value) return
  transitioning.value = true
  currentIndex.value += 1

  setTimeout(() => {
    // 到达尾部克隆，瞬间跳回第一张真实图片
    if (currentIndex.value === images.length + OFFSET) {
      transitioning.value = false
      currentIndex.value = 0
      transitioning.value = true
    }
  }, 500)

  setTimeout(() => {
    transitioning.value = false
  }, 550)
}

function resetAutoPlay() {
  if (autoPlayTimer.value) clearInterval(autoPlayTimer.value)
  autoPlayTimer.value = window.setInterval(next, INTERVAL)
}

onMounted(() => {
  autoPlayTimer.value = window.setInterval(next, INTERVAL)
})

onUnmounted(() => {
  if (autoPlayTimer.value) clearInterval(autoPlayTimer.value)
})
</script>

<style scoped>
.carousel {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  border-radius: 14px;
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