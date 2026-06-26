<script setup lang="ts">
import { onMounted } from 'vue'
import { RouterView } from 'vue-router'
import NavBar from './components/NavBar.vue'
import BackToTop from './components/BackToTop.vue'
import FloatingPlayer from './components/music/FloatingPlayer.vue'
import { useUIStore } from '@/stores/ui'

const ui = useUIStore()

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
    <NavBar v-if="ui.showNavbar" />
    <RouterView />
    <BackToTop v-if="ui.showNavbar" />
    <FloatingPlayer v-if="ui.showNavbar" />
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
  background: transparent;
}

/* 隐藏滚动条 - Firefox */
html {
  scrollbar-width: none;
}

/* 隐藏滚动条 - IE/Edge */
html {
  -ms-overflow-style: none;
}

/* ============================================
   玻璃表面 - 全站统一的毛玻璃样式
   ============================================ */
.glass-surface {
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.3),
    inset 0 0 20px rgba(255, 255, 255, 0.08),
    0 4px 32px rgba(0, 0, 0, 0.25);
}
</style>

<style scoped>
.app-shell {
  min-height: 100vh;
}
</style>
