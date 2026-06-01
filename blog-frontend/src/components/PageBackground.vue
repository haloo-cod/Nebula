<template>
  <div class="relative min-h-screen w-full">
    <!-- 背景层：绝对定位，固定背景，避免随滚动和 overflow 变化 -->
    <div
      class="absolute inset-0 bg-cover bg-center bg-no-repeat bg-fixed"
      :style="{ backgroundImage: `url(${bgImage})` }"
    ></div>
    <!-- 叠加层 -->
    <div class="absolute inset-0" :style="{ background: `rgba(0,0,0,${overlay})` }"></div>
    <!-- 内容插槽 -->
    <div class="relative z-10">
      <slot />
    </div>
  </div>
</template>

<script setup>
import bgImage from '@/assets/img/test3.jpg'

defineProps({
  overlay: {
    type: Number,
    default: 0.25,
  },
})
</script>
