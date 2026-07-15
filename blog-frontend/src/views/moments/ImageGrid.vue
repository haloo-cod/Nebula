<template>
  <!-- 图片九宫格:根据图片数量自适应布局 -->
  <div v-if="images.length > 0" class="image-grid" :class="gridClass">
    <div
      v-for="(img, i) in displayImages"
      :key="i"
      class="image-grid__item"
      @click="openLightbox(i)"
    >
      <img :src="img" :alt="`图片 ${i + 1}`" class="image-grid__img" loading="lazy" />
      <!-- 超出 4 张时,最后一格显示 +N 遮罩 -->
      <div v-if="i === 3 && images.length > 4" class="image-grid__more">
        +{{ images.length - 4 }}
      </div>
    </div>
  </div>

  <!-- 灯箱 overlay -->
  <Teleport to="body">
    <Transition name="lightbox-fade">
      <div v-if="lightboxOpen" class="lightbox-overlay" @click.self="closeLightbox">
        <button class="lightbox-close" aria-label="关闭灯箱" @click="closeLightbox">✕</button>

        <button
          v-if="images.length > 1"
          class="lightbox-arrow lightbox-arrow--prev"
          aria-label="上一张"
          @click="prevImage"
        >
          ◀
        </button>

        <img
          :src="images[currentIndex]"
          :alt="`图片 ${currentIndex + 1}`"
          class="lightbox-img"
        />

        <button
          v-if="images.length > 1"
          class="lightbox-arrow lightbox-arrow--next"
          aria-label="下一张"
          @click="nextImage"
        >
          ▶
        </button>

        <div class="lightbox-counter">{{ currentIndex + 1 }} / {{ images.length }}</div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'

const props = defineProps<{
  images: string[]
}>()

// ============ 九宫格布局逻辑 ============

/** 最多显示 4 格(超出的显示 +N) */
const displayImages = computed(() => props.images.slice(0, 4))

/** 根据图片数量决定网格 class */
const gridClass = computed(() => {
  const len = props.images.length
  if (len === 1) return 'image-grid--single'
  if (len === 2) return 'image-grid--double'
  if (len === 3) return 'image-grid--triple'
  return 'image-grid--quad'
})

// ============ 灯箱逻辑 ============

const lightboxOpen = ref(false)
const currentIndex = ref(0)

function openLightbox(index: number) {
  currentIndex.value = index
  lightboxOpen.value = true
}

function closeLightbox() {
  lightboxOpen.value = false
}

function prevImage() {
  currentIndex.value = (currentIndex.value - 1 + props.images.length) % props.images.length
}

function nextImage() {
  currentIndex.value = (currentIndex.value + 1) % props.images.length
}

function handleKeydown(e: KeyboardEvent) {
  if (!lightboxOpen.value) return
  if (e.key === 'Escape') closeLightbox()
  if (e.key === 'ArrowLeft') prevImage()
  if (e.key === 'ArrowRight') nextImage()
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
/* ===== 九宫格布局 ===== */
.image-grid {
  display: grid;
  gap: 0.4rem;
  margin-top: 0.75rem;
  border-radius: 0.75rem;
  overflow: hidden;
  width: 100%;
  max-width: 100%;
}

.image-grid--single {
  grid-template-columns: 1fr;
}

.image-grid--double {
  grid-template-columns: 1fr 1fr;
}

.image-grid--triple {
  grid-template-columns: 1fr 1fr;
  grid-template-rows: auto auto;
}

.image-grid--triple .image-grid__item:first-child {
  grid-column: 1 / -1;
}

.image-grid--quad {
  grid-template-columns: 1fr 1fr;
  grid-template-rows: 1fr 1fr;
}

.image-grid__item {
  position: relative;
  aspect-ratio: 16 / 10;
  overflow: hidden;
  cursor: pointer;
  border-radius: 0.5rem;
  background: rgba(255, 255, 255, 0.04);
}

.image-grid--single .image-grid__item {
  aspect-ratio: 16 / 9;
  max-height: 240px;
}

.image-grid__img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  transition: transform 0.25s ease;
}

.image-grid__item:hover .image-grid__img {
  transform: scale(1.03);
}

.image-grid__more {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.5);
  color: rgba(255, 255, 255, 0.9);
  font-size: 1.4rem;
  font-weight: 700;
}

/* ===== 灯箱 ===== */
.lightbox-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.88);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

.lightbox-img {
  max-width: 90vw;
  max-height: 85vh;
  object-fit: contain;
  border-radius: 0.5rem;
  user-select: none;
}

.lightbox-close {
  position: absolute;
  top: 1.5rem;
  right: 1.5rem;
  width: 2.5rem;
  height: 2.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.8);
  font-size: 1.1rem;
  cursor: pointer;
  transition: background 0.2s ease;
}

.lightbox-close:hover {
  background: rgba(255, 255, 255, 0.2);
}

.lightbox-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 3rem;
  height: 3rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.7);
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.2s ease;
}

.lightbox-arrow:hover {
  background: rgba(255, 255, 255, 0.18);
}

.lightbox-arrow--prev {
  left: 1.5rem;
}

.lightbox-arrow--next {
  right: 1.5rem;
}

.lightbox-counter {
  position: absolute;
  bottom: 1.5rem;
  left: 50%;
  transform: translateX(-50%);
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.85rem;
  font-variant-numeric: tabular-nums;
}

/* ===== 灯箱动画 ===== */
.lightbox-fade-enter-active,
.lightbox-fade-leave-active {
  transition: opacity 0.25s ease;
}

.lightbox-fade-enter-from,
.lightbox-fade-leave-to {
  opacity: 0;
}
</style>
