<template>
  <div class="relative min-h-screen w-full">
    <!-- 背景层：fixed 定位，不使用 translateZ/will-change 以免阻断子元素 backdrop-filter 采样 -->
    <div
      class="bg-layer"
      :style="bgLayerStyle"
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
import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useUIStore } from '@/stores/ui'

// overlay:遮罩层不透明度(0~1),数值越大背景越暗
withDefaults(defineProps<{ overlay?: number }>(), {
  overlay: 0.09,
})

const { backgroundBlur, backgroundBlurEnabled, currentBgUrl } = storeToRefs(useUIStore())

const bgLayerStyle = computed(() => {
  const blur = backgroundBlurEnabled.value ? backgroundBlur.value : 0
  const scale = blur > 0 ? 1 + Math.min(blur / 240, 0.08) : 1
  return {
    backgroundImage: `url(${currentBgUrl.value})`,
    filter: blur > 0 ? `blur(${blur}px)` : undefined,
    transform: scale !== 1 ? `scale(${scale})` : undefined,
  }
})
</script>

<style scoped>
.bg-layer {
  position: fixed;
  inset: 0;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  z-index: 0;
}

.overlay-layer {
  position: fixed;
  inset: 0;
  z-index: 1;
}
</style>
