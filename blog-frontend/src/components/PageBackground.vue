<template>
  <div class="relative min-h-screen w-full">
    <!-- 背景层：fixed 定位 + translate3d 强制 GPU 合成层，性能远优于 background-attachment:fixed -->
    <div
      class="bg-layer"
      :class="{ 'bg-layer-recomposite': recompositing }"
      :style="{ backgroundImage: `url(${bgImage})` }"
    ></div>
    <!-- 叠加层 -->
    <div class="overlay-layer" :style="{ background: `rgba(0,0,0,${overlay})` }"></div>
    <!-- 内容插槽 -->
    <div class="relative z-10">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useUIStore } from '@/stores/ui'
import darkBg from '@/assets/img/test3.jpg'
import lightBg from '@/assets/img/test6.png'

// overlay:遮罩层不透明度(0~1),数值越大背景越暗
withDefaults(defineProps<{ overlay?: number }>(), {
  overlay: 0.09,
})

const { theme } = storeToRefs(useUIStore())

// 背景图随主题切换:亮色用 test6,暗色用 test3
const bgImage = computed(() => (theme.value === 'light' ? lightBg : darkBg))

// 主题切换时,背景层被提升为独立合成层(translateZ + will-change),
// backdrop-filter 会采样该层的缓存快照,导致换图后毛玻璃仍显示旧背景。
// 切换瞬间临时撤销合成层提升,强制 backdrop-filter 重新采样新背景。
const recompositing = ref(false)
watch(theme, () => {
  recompositing.value = true
  // 跨两帧再恢复合成层优化,确保浏览器已用新背景重绘
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      recompositing.value = false
    })
  })
})
</script>

<style scoped>
.bg-layer {
  position: fixed;
  inset: 0;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  /* 强制独立合成层，避免每帧 repaint */
  transform: translateZ(0);
  will-change: transform;
  z-index: 0;
}

/* 主题切换瞬间:撤销合成层提升,让 backdrop-filter 重新采样新背景 */
.bg-layer-recomposite {
  transform: none;
  will-change: auto;
}

.overlay-layer {
  position: fixed;
  inset: 0;
  z-index: 1;
  transform: translateZ(0);
}
</style>
