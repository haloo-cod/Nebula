<script setup>
import { onMounted } from 'vue'
import { RouterView } from 'vue-router'
import NavBar from './components/NavBar.vue'
import BackToTop from './components/BackToTop.vue'

onMounted(() => {
  const splash = document.getElementById('splash')
  const app = document.getElementById('app')
  if (app) app.style.opacity = '1'
  if (splash) {
    splash.classList.add('hide')
    setTimeout(() => splash.remove(), 400)
  }
})
</script>

<template>
  <div class="app-shell">
    <NavBar />
    <RouterView />
    <BackToTop />
  </div>
</template>

<style>
/* 全局样式，解决滚动条抖动并隐藏滚动条UI */
html {
  overflow-y: scroll;
}

/* 隐藏滚动条 - WebKit and old Edge */
::-webkit-scrollbar {
  width: 0px;
  background: transparent; /* make scrollbar transparent */
}

/* 隐藏滚动条 - Firefox */
html {
  scrollbar-width: none;
}

/* 隐藏滚动条 - IE/Edge */
html {
  -ms-overflow-style: none;
}
</style>

<style scoped>
.app-shell {
  min-height: 100vh;
}
</style>
