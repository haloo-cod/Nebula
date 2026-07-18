<template>
  <div class="bg-picker">
    <!-- 当前背景预览 -->
    <div class="picker-preview-wrap">
      <button
        class="picker-arrow picker-arrow--left"
        type="button"
        aria-label="上一张"
        @click="prev"
      >
        ←
      </button>
      <img :src="currentSrc" alt="当前背景" class="picker-preview" />
      <button
        class="picker-arrow picker-arrow--right"
        type="button"
        aria-label="下一张"
        @click="next"
      >
        →
      </button>

      <!-- 圆点指示器 -->
      <div class="picker-dots">
        <button
          v-for="(_, i) in group"
          :key="i"
          class="picker-dot"
          :class="{ 'picker-dot--active': i === currentIndex }"
          type="button"
          :aria-label="`背景 ${i + 1}`"
          @click="select(i)"
        ></button>
      </div>
    </div>

    <!-- 缩略图网格 展开/收起 -->
    <div class="picker-grid-header">
      <button class="picker-grid-toggle" type="button" @click="expanded = !expanded">
        {{ expanded ? '收起' : '展开全部' }}
      </button>
    </div>
    <div v-if="expanded" class="picker-grid">
      <button
        v-for="(item, i) in group"
        :key="i"
        class="picker-thumb"
        :class="{ 'picker-thumb--active': i === currentIndex }"
        type="button"
        @click="select(i)"
      >
        <img :src="item.src" alt="" class="picker-thumb-img" />
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useUIStore } from '@/stores/ui'
import {
  darkBackgrounds,
  lightBackgrounds,
  mobileDarkBackgrounds,
  mobileLightBackgrounds,
} from '@/data/backgrounds'

const ui = useUIStore()
const expanded = ref(false)

const group = computed(() => {
  const isDark = ui.theme === 'dark'
  if (ui.isMobile) {
    return isDark ? mobileDarkBackgrounds : mobileLightBackgrounds
  }
  return isDark ? darkBackgrounds : lightBackgrounds
})

const currentIndex = computed(() => {
  if (ui.isMobile) {
    return ui.theme === 'dark' ? ui.mobileDarkBgIndex : ui.mobileLightBgIndex
  }
  return ui.theme === 'dark' ? ui.darkBgIndex : ui.lightBgIndex
})

const currentSrc = computed(() => group.value[currentIndex.value]?.src ?? '')

function select(index: number) {
  if (ui.isMobile) {
    if (ui.theme === 'dark') {
      ui.setMobileDarkBg(index)
    } else {
      ui.setMobileLightBg(index)
    }
    return
  }
  if (ui.theme === 'dark') {
    ui.setDarkBg(index)
  } else {
    ui.setLightBg(index)
  }
}

function prev() {
  const len = group.value.length
  select((currentIndex.value - 1 + len) % len)
}

function next() {
  const len = group.value.length
  select((currentIndex.value + 1) % len)
}
</script>

<style scoped>
.bg-picker {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

/* 预览区 */
.picker-preview-wrap {
  position: relative;
  border-radius: 0.75rem;
  overflow: hidden;
  aspect-ratio: 16 / 9;
  background: rgba(255, 255, 255, 0.04);
}

.picker-preview {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.picker-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  z-index: 2;
  width: 1.8rem;
  height: 1.8rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.4);
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.8rem;
  cursor: pointer;
  transition: background 0.2s ease;
}

.picker-arrow:hover {
  background: rgba(0, 0, 0, 0.65);
}

.picker-arrow--left {
  left: 0.4rem;
}

.picker-arrow--right {
  right: 0.4rem;
}

/* 圆点指示器 */
.picker-dots {
  position: absolute;
  bottom: 0.5rem;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 0.35rem;
}

.picker-dot {
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 50%;
  border: none;
  background: rgba(255, 255, 255, 0.35);
  cursor: pointer;
  padding: 0;
  transition: all 0.2s ease;
}

.picker-dot--active {
  background: rgba(255, 255, 255, 0.9);
  width: 1.2rem;
  border-radius: 999px;
}

/* 网格切换按钮 */
.picker-grid-header {
  display: flex;
  justify-content: flex-end;
}

.picker-grid-toggle {
  border: none;
  background: none;
  color: var(--text-secondary);
  font-size: 0.72rem;
  cursor: pointer;
  padding: 0.2rem 0;
  transition: color 0.2s ease;
}

.picker-grid-toggle:hover {
  color: var(--text-primary);
}

/* 缩略图网格 */
.picker-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.45rem;
}

.picker-thumb {
  position: relative;
  border-radius: 0.5rem;
  overflow: hidden;
  aspect-ratio: 16 / 9;
  border: 2px solid transparent;
  background: rgba(255, 255, 255, 0.04);
  cursor: pointer;
  padding: 0;
  transition: all 0.2s ease;
}

.picker-thumb:hover {
  border-color: rgba(140, 185, 255, 0.4);
}

.picker-thumb--active {
  border-color: rgba(100, 160, 255, 0.8);
  box-shadow: 0 0 0 2px rgba(100, 160, 255, 0.25);
}

.picker-thumb-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
</style>
