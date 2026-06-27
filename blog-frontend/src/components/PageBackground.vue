<template>
  <div class="relative min-h-screen w-full">
    <!-- 背景层：fixed 定位 + translate3d 强制 GPU 合成层，性能远优于 background-attachment:fixed -->
    <div class="bg-layer" :style="{ backgroundImage: `url(${bgImage})` }"></div>
    <!-- 叠加层 -->
    <div class="overlay-layer" :style="{ background: `rgba(0,0,0,${overlay})` }"></div>
    <!-- 内容插槽 -->
    <div class="relative z-10">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import bgImage from '@/assets/img/test5.png'

// overlay:遮罩层不透明度(0~1),数值越大背景越暗
withDefaults(defineProps<{ overlay?: number }>(), {
  overlay: 0.09,
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

.overlay-layer {
  position: fixed;
  inset: 0;
  z-index: 1;
  transform: translateZ(0);
}
</style>
