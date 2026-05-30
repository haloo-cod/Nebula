<template>
  <div
    class="relative min-h-screen w-full flex items-center justify-center bg-cover bg-center bg-no-repeat"
    :style="{ backgroundImage: `url(${bgImage})` }"
  ></div>
  <div class="index">
    <h1>这是post页</h1>
  </div>
</template>

<script setup>
import bgImage from '@/assets/img/test.jfif'
</script>

<style scoped></style>
