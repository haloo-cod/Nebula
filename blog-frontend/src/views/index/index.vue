<template>
  <PageBackground>
    <div class="home-root" :class="{ 'home-locked': !showUIElements }">
      <!-- 面板区域（简介 + 占位） -->
      <div v-if="showUIElements" class="home-panels">
        <div class="home-panels-inner">
          <div class="left-panel-glass">
            <LiquidGlass
              v-if="ui.liquidGlassEnabled"
              :cornerRadius="16"
              :theme="ui.theme"
              :blur-radius="ui.liquidGlassBlur"
              :allow-reveal="allowLiquidGlassReveal"
              :ripple-trail="true"
              class="panel-liquid-glass"
            >
              <HomeProfilePanel
                :avatar="avatar"
                :name="profile.name"
                :bio="profile.bio"
                :links="socialLinks"
              />
            </LiquidGlass>
            <PanelFallbackGlass v-else>
              <HomeProfilePanel
                :avatar="avatar"
                :name="profile.name"
                :bio="profile.bio"
                :links="socialLinks"
              />
            </PanelFallbackGlass>
          </div>
          <div class="right-panel-glass">
            <LiquidGlass
              v-if="ui.liquidGlassEnabled"
              :cornerRadius="16"
              :theme="ui.theme"
              :blur-radius="ui.liquidGlassBlur"
              :allow-reveal="allowLiquidGlassReveal"
              :ripple-trail="true"
              class="panel-liquid-glass"
            >
              <DataDashboard />
            </LiquidGlass>
            <PanelFallbackGlass v-else>
              <DataDashboard />
            </PanelFallbackGlass>
          </div>
        </div>
      </div>

      <!-- 玻璃横条（标题） -->
      <div class="title-container" :class="containerClass">
        <div class="title-glass" :class="{ 'title-glass--visible': showUIElements }">
          <h1 class="typewriter-title" translate="no">
            {{ typewriterDone ? fullTitle : displayed }}<span class="caret caret-blink">|</span>
          </h1>
        </div>
      </div>

      <!-- 下方面板区域 -->
      <div v-if="showUIElements" class="home-bottom">
        <div class="bottom-grid">
          <!-- 左侧：轮播图 -->
          <div class="bottom-left">
            <LiquidGlass
              v-if="ui.liquidGlassEnabled"
              :cornerRadius="16"
              :theme="ui.theme"
              :blur-radius="ui.liquidGlassBlur"
              :allow-reveal="allowLiquidGlassReveal"
              :ripple-trail="true"
              class="panel-liquid-glass"
            >
              <Carousel />
            </LiquidGlass>
            <PanelFallbackGlass v-else>
              <Carousel />
            </PanelFallbackGlass>
          </div>
          <!-- 右侧上：日历 -->
          <div class="bottom-right-top">
            <LiquidGlass
              v-if="ui.liquidGlassEnabled"
              :cornerRadius="16"
              :theme="ui.theme"
              :blur-radius="ui.liquidGlassBlur"
              :allow-reveal="allowLiquidGlassReveal"
              :ripple-trail="true"
              class="panel-liquid-glass"
            >
              <CalendarPanel flat />
            </LiquidGlass>
            <PanelFallbackGlass v-else>
              <CalendarPanel flat />
            </PanelFallbackGlass>
          </div>
          <!-- 右侧中：电子时钟 -->
          <div class="bottom-right-middle">
            <LiquidGlass
              v-if="ui.liquidGlassEnabled"
              :cornerRadius="16"
              :theme="ui.theme"
              :blur-radius="ui.liquidGlassBlur"
              :allow-reveal="allowLiquidGlassReveal"
              :ripple-trail="true"
              class="panel-liquid-glass"
            >
              <DigitalClockPanel />
            </LiquidGlass>
            <PanelFallbackGlass v-else>
              <DigitalClockPanel />
            </PanelFallbackGlass>
          </div>
          <!-- 右侧下：文章缩略 + 日记（占位） -->
          <div class="bottom-right-bottom">
            <div class="bottom-right-bottom-inner">
              <LiquidGlass
                v-if="ui.liquidGlassEnabled"
                :cornerRadius="16"
                :theme="ui.theme"
                :blur-radius="ui.liquidGlassBlur"
                :allow-reveal="allowLiquidGlassReveal"
                class="panel-liquid-glass"
              />
              <PanelFallbackGlass v-else class="panel-fallback-glass--empty"></PanelFallbackGlass>
              <LiquidGlass
                v-if="ui.liquidGlassEnabled"
                :cornerRadius="16"
                :theme="ui.theme"
                :blur-radius="ui.liquidGlassBlur"
                :allow-reveal="allowLiquidGlassReveal"
                class="panel-liquid-glass"
              />
              <PanelFallbackGlass v-else class="panel-fallback-glass--empty"></PanelFallbackGlass>
            </div>
          </div>
        </div>
      </div>
    </div>
  </PageBackground>
</template>

<script setup lang="ts">
import { ref, watch, computed, onUnmounted } from 'vue'
import PageBackground from '@/components/PageBackground.vue'
import PanelFallbackGlass from '@/components/panels/PanelFallbackGlass.vue'
import HomeProfilePanel from '@/components/panels/HomeProfilePanel.vue'
import DataDashboard from '@/components/panels/DataDashboard.vue'
import CalendarPanel from '@/components/panels/CalendarPanel.vue'
import DigitalClockPanel from '@/components/panels/DigitalClockPanel.vue'
import Carousel from '@/components/panels/Carousel.vue'
import LiquidGlass from '@/components/liquid-glass/LiquidGlass.vue'
import { useTypewriter } from '@/composables/useTypewriter'
import { useUIStore } from '@/stores/ui'
import { avatar, profile, socialLinks } from '@/data/profile'

const ui = useUIStore()
const fullTitle = "Starlitn'blog"
const isMobile = ref(window.innerWidth < 768)
const showContentDirectly = history.state?.showContent === true
const skipLiquidGlassReveal = history.state?.skipLiquidGlassReveal === true
const instant = isMobile.value || showContentDirectly
const allowLiquidGlassReveal = !skipLiquidGlassReveal

const { displayed, done: typewriterDone } = useTypewriter(fullTitle, {
  speed: 120,
  startDelay: 400,
  instant,
})

const showUIElements = ref(instant)

if (!instant) {
  ui.showNavbar = false
}

watch(typewriterDone, (val) => {
  if (!val) return
  if (instant) {
    showUIElements.value = true
  } else {
    setTimeout(() => {
      showUIElements.value = true
      ui.showNavbar = true
    }, 850)
  }
})

onUnmounted(() => {
  ui.showNavbar = true
})

const containerClass = computed(() => {
  if (instant) return 'title-container--centered'
  if (typewriterDone.value) return 'title-container--sliding'
  return 'title-container--initial'
})
</script>

<style scoped>
/* ============================================
   根容器
   ============================================ */
.home-root {
  position: relative;
  width: 100%;
  min-height: 100vh;
}

.home-locked {
  height: 100vh;
  overflow: hidden;
}

/* ============================================
   标题容器 — 阶段 1: 偏上静止 → 阶段 2: 下滑定住
   ============================================ */
.title-container {
  position: absolute;
  top: 50vh;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 20;
  width: 100%;
  display: flex;
  justify-content: center;
}

.title-container--initial {
  transform: translate(-50%, calc(-50% - 50px));
}

.title-container--sliding {
  transform: translate(-50%, -50%);
  transition: transform 0.8s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  will-change: transform;
}

.title-container--centered {
  transform: translate(-50%, -50%);
}

/* ============================================
   标题文字 — 纯白细体,无任何背景
   ============================================ */
.typewriter-title {
  font-weight: 400;
  font-size: 2rem;
  color: #ffffff;
  text-shadow: 0 4px 20px rgba(0, 0, 0, 0.8);
  letter-spacing: 0.04em;
  text-align: center;
  user-select: none;
  white-space: nowrap;
  margin: 0;
}

@media (min-width: 640px) {
  .typewriter-title {
    font-size: 2.75rem;
  }
}

@media (min-width: 768px) {
  .typewriter-title {
    font-size: 2rem;
  }
}

/* ============================================
   玻璃胶囊 — 阶段 3: 与导航栏同步渐显
   ============================================ */
.title-glass {
  width: 85%;
  max-width: 1100px;
  height: 60px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 30px;

  background: rgba(255, 255, 255, 0);
  backdrop-filter: blur(0px);
  -webkit-backdrop-filter: blur(0px);
  border: 1px solid transparent;
  box-shadow: none;

  transition:
    background 0.8s ease-in-out,
    border-color 0.8s ease-in-out,
    box-shadow 0.8s ease-in-out;
}

.title-glass--visible {
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-color: rgba(255, 255, 255, 0.2);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.3),
    inset 0 0 20px rgba(255, 255, 255, 0.08),
    0 4px 32px rgba(0, 0, 0, 0.25);
}

.caret {
  font-weight: 300;
}

.caret-blink {
  animation: caret-pulse 1s step-end infinite;
}

@keyframes caret-pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .title-container--sliding {
    transition: none;
  }
  .title-glass {
    transition: none;
  }
}

/* ============================================
   双面板 — 阶段 3: 横条下方,简介 + 日历
   ============================================ */
.home-panels {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  top: 90px;
  z-index: 15;
  width: 85%;
  max-width: 1100px;
  max-height: calc(50vh - 130px);
  display: flex;
  flex-direction: column;
}

.home-panels-inner {
  flex: 1;
  min-height: 0;
  display: flex;
  gap: 20px;
  align-items: stretch;
}

.home-panels-inner > :first-child {
  flex: 0 0 calc(60% - 10px);
}

.home-panels-inner > :last-child {
  flex: 0 0 calc(40% - 10px);
}

.left-panel-glass,
.right-panel-glass {
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  border-radius: 16px;
}

.panel-liquid-glass {
  flex: 1;
}

.panel-fallback-glass {
  flex: 1;
  width: 100%;
  height: 100%;
  border-radius: 16px;
}

.panel-fallback-glass--empty {
  min-height: 100%;
}

@media (max-width: 768px) {
  .home-panels {
    top: 80px;
    width: 92%;
    max-height: none;
    display: block;
  }

  .home-panels-inner {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
    min-height: auto;
  }

  .home-panels-inner > :first-child,
  .home-panels-inner > :last-child {
    flex: none;
    width: 100%;
  }
}

/* ============================================
   下方面板区域
   ============================================ */
.home-bottom {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  top: calc(50vh + 40px);
  z-index: 15;
  width: 85%;
  max-width: 1100px;
}

.bottom-grid {
  display: grid;
  grid-template-columns: calc(40% - 8px) calc(60% - 8px);
  grid-template-rows: 350px 96px auto;
  gap: 16px;
}

.bottom-left {
  grid-column: 1;
  grid-row: 1 / span 3;
  display: flex;
  height: 900px;
  margin-bottom: 16px;
  /* padding: 14px; */
  box-sizing: border-box;
}

.bottom-right-top {
  grid-column: 2;
  grid-row: 1;
  display: flex;
  height: 350px;
  /* padding: 14px; */
  box-sizing: border-box;
}

.bottom-right-middle {
  grid-column: 2;
  grid-row: 2;
  display: flex;
  height: 96px;
  box-sizing: border-box;
}

.bottom-right-bottom {
  grid-column: 2;
  grid-row: 3;
  display: flex;
  min-height: 220px;
}

.bottom-right-bottom-inner {
  height: 300px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  width: 100%;
  /* padding: 14px; */
  box-sizing: border-box;
}

.posts-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  padding: 0.75rem;
  height: 100%;
  box-sizing: border-box;
}

@media (max-width: 768px) {
  .home-bottom {
    top: calc(50vh + 30px);
    width: 92%;
  }

  .bottom-grid {
    grid-template-columns: 1fr;
  }

  .bottom-left {
    height: auto;
    min-height: 400px;
    padding: 12px;
  }

  .bottom-right-bottom-inner {
    grid-template-columns: 1fr;
  }

  .bottom-right-top {
    padding: 12px;
  }

  .posts-grid {
    grid-template-columns: 1fr;
    padding: 0.5rem;
  }
}
</style>
