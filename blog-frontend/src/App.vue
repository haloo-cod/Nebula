<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import NavBar from './components/NavBar.vue'
import BackToTop from './components/BackToTop.vue'
import FloatingPlayer from './components/music/FloatingPlayer.vue'
import { useUIStore } from '@/stores/ui'

const ui = useUIStore()
const route = useRoute()
const hideChrome = computed(() => route.meta.hideChrome === true)

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
    <NavBar v-if="ui.showNavbar && !hideChrome" />
    <RouterView />
    <BackToTop v-if="ui.showNavbar && !hideChrome" />
    <FloatingPlayer v-if="ui.showNavbar && !hideChrome" />
    <div
      v-if="ui.themeTransitioning"
      class="theme-overlay"
      :class="{ 'theme-overlay--revealing': ui.themeTransitionRevealStarted }"
    ></div>
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
  background: var(--glass-bg);
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  border: 1px solid var(--glass-border);
  box-shadow:
    inset 0 1px 0 var(--glass-highlight),
    inset 0 0 20px rgba(255, 255, 255, 0.08),
    var(--glass-shadow);
}

/* 轻量毛玻璃 - 用于小标签、按钮等 */
.glass-subtle {
  background: var(--glass-bg-subtle);
  backdrop-filter: blur(var(--glass-blur-subtle));
  -webkit-backdrop-filter: blur(var(--glass-blur-subtle));
  border: 1px solid var(--glass-border-subtle);
}

/* 强毛玻璃 - 用于面板、卡片等 */
.glass-strong {
  background: var(--glass-bg-strong);
  backdrop-filter: blur(var(--glass-blur-strong));
  -webkit-backdrop-filter: blur(var(--glass-blur-strong));
  border: 1px solid var(--glass-border);
  box-shadow:
    inset 0 1px 0 var(--glass-highlight),
    var(--glass-shadow);
}
</style>

<style scoped>
.app-shell {
  min-height: 100vh;
}

.theme-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: rgba(8, 10, 14, 0.32);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  pointer-events: none;
  transition:
    opacity 0.2s ease,
    backdrop-filter 0.2s ease,
    -webkit-backdrop-filter 0.2s ease;
  opacity: 1;
}

.theme-overlay--revealing {
  opacity: 0;
  backdrop-filter: blur(0px);
  -webkit-backdrop-filter: blur(0px);
}
</style>
