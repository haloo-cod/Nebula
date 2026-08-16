<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import NavBar from './components/NavBar.vue'
import BackToTop from './components/BackToTop.vue'
import FloatingPlayer from './components/music/FloatingPlayer.vue'
import RainEffect from './components/RainEffect.vue'
import PageBackground from './components/PageBackground.vue'
import PerfMonitor from './components/liquid-glass/PerfMonitor.vue'
import { useUIStore } from '@/stores/ui'
import { useAuthStore } from '@/stores/auth'
import { preloadTexture, preloadVideoTexture } from '@/components/liquid-glass/liquidGlassRenderer'
import { isVideoBackground } from '@/data/backgrounds'

const ui = useUIStore()
const auth = useAuthStore()
const route = useRoute()
const hideChrome = computed(() => route.meta.hideChrome === true)
const hideRain = computed(() => route.meta.hideRain === true)
const showBackground = computed(() => !hideChrome.value && route.meta.hideBackground !== true)
const backgroundOverlay = computed(() =>
  typeof route.meta.backgroundOverlay === 'number' ? route.meta.backgroundOverlay : 0.09,
)

// 临时性能监控面板:默认常驻显示,Ctrl+Shift+P 可切换隐藏
const showPerf = ref(false)

/** Ctrl+Shift+P 切换性能面板 */
function handlePerfHotkey(e: KeyboardEvent) {
  if (e.ctrlKey && e.shiftKey && (e.key === 'P' || e.key === 'p')) {
    e.preventDefault()
    showPerf.value = !showPerf.value
  }
}

onMounted(() => {
  window.addEventListener('keydown', handlePerfHotkey)
  const splash = document.getElementById('splash')
  const app = document.getElementById('app')
  if (app) app.style.opacity = '1'
  if (splash) {
    splash.classList.add('hide')
    setTimeout(() => splash.remove(), 400)
  }

  // 启动即预热当前背景纹理(静态 fallback URL),让下载+GPU 上传在玻璃出现之前完成,
  // 避免首个 LiquidGlass 挂载时在主线程同步上传大图造成首帧卡顿。
  void preloadCurrentBackground()

  // 从后端加载背景图列表（替换静态 fallback），加载完成后预热新 URL
  ui.loadBackgrounds().then(() => {
    void preloadCurrentBackground()
  })

  if (auth.token || route.meta.requiresAuth || route.path === '/auth/callback') {
    void auth.init()
  } else {
    auth.initialized = true
  }
})

// 主题切换或背景图手动切换时预热新纹理,下次玻璃刷新时直接命中缓存
async function preloadCurrentBackground() {
  const background = ui.currentBackground
  if (!background.src) return
  if (isVideoBackground(background)) await preloadVideoTexture(background.src)
  else await preloadTexture(background.src)
}

watch(
  () => ui.currentBackground,
  () => {
    void preloadCurrentBackground()
  },
  { deep: true },
)

onUnmounted(() => {
  window.removeEventListener('keydown', handlePerfHotkey)
})
</script>

<template>
  <div class="app-shell">
    <PageBackground v-if="showBackground" :overlay="backgroundOverlay" />
    <div class="app-content">
      <NavBar v-if="ui.showNavbar && !hideChrome" />
      <RouterView />
      <BackToTop v-if="ui.showNavbar && !hideChrome" />
      <FloatingPlayer v-if="ui.showNavbar && !hideChrome" />
      <RainEffect v-if="!hideChrome && !hideRain" />
    </div>
    <div
      v-if="ui.themeTransitioning"
      class="theme-overlay"
      :class="{ 'theme-overlay--revealing': ui.themeTransitionRevealStarted }"
    ></div>
    <PerfMonitor v-if="showPerf" />
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
  position: relative;
  min-height: 100vh;
}

.app-content {
  position: relative;
  z-index: 2;
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
