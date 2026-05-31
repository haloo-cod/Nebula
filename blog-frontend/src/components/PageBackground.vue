<template>
  <div
    class="relative min-h-screen w-full bg-cover bg-center bg-no-repeat"
    :style="{ backgroundImage: `url(${bgImage})` }"
  >
    <div class="absolute inset-0" :style="{ background: `rgba(0,0,0,${overlay})` }"></div>
    <slot />
  </div>
</template>

<script setup>
import bgImage from '@/assets/img/test.jfif'

defineProps({
  overlay: {
    type: Number,
    default: 0.45,
  },
})
</script>
