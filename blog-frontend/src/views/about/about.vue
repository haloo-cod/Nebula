<template>
  <div class="about-page">
    <LiquidGlass
      v-if="ui.liquidGlassEnabled"
      class="about-glass" data-background-credit-boundary
      :theme="ui.theme"
      :corner-radius="32"
      :blur-radius="ui.liquidGlassBlur"
      :glass-thickness="42"
      :highlight-width="3"
      ripple-trail
    >
      <div class="about-inner">
        <AboutHero />
        <div class="about-toolbar">
          <AboutTabs :active-tab="activeTab" @change="switchTab" />
        </div>
        <div class="about-divider"></div>
        <!-- 高度过渡容器：用 inline style 绑定动态高度 -->
        <div ref="panelRef" class="tab-panel" :style="{ height: panelHeight }" @transitionend="onPanelTransitionEnd">
          <div
            ref="introRef"
            class="tab-pane"
            :class="{ 'tab-pane--active': activeTab === 'intro' }"
          >
            <AboutIntro />
          </div>
          <div
            ref="activityRef"
            class="tab-pane"
            :class="{ 'tab-pane--active': activeTab === 'activity' }"
          >
            <AboutActivity />
          </div>
        </div>
        <AboutComments v-show="activeTab === 'intro'" />
      </div>
    </LiquidGlass>

    <PanelFallbackGlass v-else tag="div" class="about-glass about-glass--fallback" data-background-credit-boundary>
      <div class="about-inner">
        <AboutHero />
        <div class="about-toolbar">
          <AboutTabs :active-tab="activeTab" @change="switchTab" />
        </div>
        <div class="about-divider"></div>
        <div ref="panelRefFallback" class="tab-panel" :style="{ height: panelHeight }" @transitionend="onPanelTransitionEnd">
          <div
            ref="introRefFallback"
            class="tab-pane"
            :class="{ 'tab-pane--active': activeTab === 'intro' }"
          >
            <AboutIntro />
          </div>
          <div
            ref="activityRefFallback"
            class="tab-pane"
            :class="{ 'tab-pane--active': activeTab === 'activity' }"
          >
            <AboutActivity />
          </div>
        </div>
        <AboutComments v-show="activeTab === 'intro'" />
      </div>
    </PanelFallbackGlass>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onUnmounted } from 'vue'
import LiquidGlass from '@/components/liquid-glass/LiquidGlass.vue'
import PanelFallbackGlass from '@/components/panels/PanelFallbackGlass.vue'
import AboutHero from './AboutHero.vue'
import AboutTabs from './AboutTabs.vue'
import AboutIntro from './AboutIntro.vue'
import AboutActivity from './AboutActivity.vue'
import AboutComments from './AboutComments.vue'
import { useUIStore } from '@/stores/ui'

const ui = useUIStore()
const activeTab = ref<'intro' | 'activity'>('intro')

// Tab 面板高度（带单位的字符串）
const panelHeight = ref('auto')
const panelRef = ref<HTMLElement | null>(null)
const panelRefFallback = ref<HTMLElement | null>(null)
let pendingFrame = 0
let switchGeneration = 0
let targetHeight: number | null = null

// Tab 内容元素引用（LiquidGlass 模式）
const introRef = ref<HTMLElement | null>(null)
const activityRef = ref<HTMLElement | null>(null)

// Tab 内容元素引用（Fallback 模式）
const introRefFallback = ref<HTMLElement | null>(null)
const activityRefFallback = ref<HTMLElement | null>(null)

/** 获取当前激活 Tab 的实际内容高度 */
function getActiveHeight(tab: 'intro' | 'activity'): number {
  // 优先取 LiquidGlass 模式下的 ref，fallback 时取 fallback ref
  const introEl = introRef.value || introRefFallback.value
  const activityEl = activityRef.value || activityRefFallback.value
  const el = tab === 'intro' ? introEl : activityEl
  if (!el) return 0
  return el.scrollHeight
}

/** 切换 Tab 时从当前可见高度继续过渡，快速切换以最后一次为准。 */
function switchTab(tab: 'intro' | 'activity') {
  if (tab === activeTab.value) return
  const generation = ++switchGeneration
  if (pendingFrame) cancelAnimationFrame(pendingFrame)
  pendingFrame = 0
  targetHeight = null
  const panel = panelRef.value || panelRefFallback.value
  const currentHeight = panel?.getBoundingClientRect().height ?? 0
  panelHeight.value = panel && currentHeight > 0 ? `${currentHeight}px` : 'auto'
  activeTab.value = tab

  void nextTick(() => {
    if (generation !== switchGeneration) return
    const newHeight = getActiveHeight(tab)
    if (!panel || currentHeight <= 0 || newHeight <= 0 || Math.abs(newHeight - currentHeight) < 0.5) {
      panelHeight.value = 'auto'
      return
    }
    // 先提交锁定高度，再启动目标高度的 CSS 过渡。
    void panel.offsetHeight
    pendingFrame = requestAnimationFrame(() => {
      pendingFrame = 0
      if (generation !== switchGeneration) return
      targetHeight = newHeight
      panelHeight.value = `${newHeight}px`
    })
  })
}

function onPanelTransitionEnd(event: TransitionEvent) {
  const panel = panelRef.value || panelRefFallback.value
  if (!panel || event.target !== panel || event.propertyName !== 'height' || targetHeight === null) return
  if (Math.abs(panel.getBoundingClientRect().height - targetHeight) >= 1) return
  targetHeight = null
  panelHeight.value = 'auto'
}

onUnmounted(() => {
  switchGeneration++
  if (pendingFrame) cancelAnimationFrame(pendingFrame)
})
</script>

<style scoped>
.about-page {
  position: relative;
  z-index: 10;
  display: flex;
  justify-content: center;
  min-height: 100vh;
  padding: 6rem 1rem 3rem;
}

.about-glass {
  width: 100%;
  max-width: 52rem;
  border-radius: 2rem;
  overflow: hidden;
  align-self: flex-start;
}

.about-glass--fallback {
  transition:
    border-color 0.25s ease,
    box-shadow 0.25s ease;
}

.about-inner {
  display: flex;
  flex-direction: column;
}

.about-toolbar {
  padding: 1.25rem 1.5rem 0;
}

.about-divider {
  height: 1px;
  margin: 1rem 1.5rem;
  background: rgba(255, 255, 255, 0.08);
}

/* Tab 面板：平滑高度过渡 */
.tab-panel {
  position: relative;
  min-width: 0;
  overflow: hidden;
  transition: height 0.5s cubic-bezier(0.22, 1, 0.36, 1);
}

/* Tab 内容页：非激活的绝对定位（不影响高度），激活的回到文档流 */
.tab-pane {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.3s ease;
}

.tab-pane--active {
  position: relative;
  opacity: 1;
  pointer-events: auto;
}

@media (max-width: 767px) {
  .about-page {
    padding-top: 5rem;
  }

  .about-toolbar {
    padding: 1rem 1rem 0;
  }

  .about-divider {
    margin: 0.75rem 1rem;
  }
}
</style>

<!-- Light 主题适配 -->
<style>
[data-theme='light'] .about-inner .about-divider {
  background: rgba(0, 0, 0, 0.06);
}
</style>
