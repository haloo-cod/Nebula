<template>
  <PageBackground>
    <div class="about-page">
      <LiquidGlass
        v-if="ui.liquidGlassEnabled"
        class="about-glass"
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
          <div class="tab-panel" :style="{ height: panelHeight }">
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

      <PanelFallbackGlass v-else tag="div" class="about-glass about-glass--fallback">
        <div class="about-inner">
          <AboutHero />
          <div class="about-toolbar">
            <AboutTabs :active-tab="activeTab" @change="switchTab" />
          </div>
          <div class="about-divider"></div>
          <div class="tab-panel" :style="{ height: panelHeight }">
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
  </PageBackground>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import PageBackground from '@/components/PageBackground.vue'
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

/** 切换 Tab：先锁定当前高度，切换后平滑过渡到新高度 */
function switchTab(tab: 'intro' | 'activity') {
  if (tab === activeTab.value) return

  // 1. 锁定当前高度（从 auto 变为具体像素值，启动 transition 的起点）
  const currentHeight = getActiveHeight(activeTab.value)
  panelHeight.value = currentHeight + 'px'

  // 2. 切换 Tab
  activeTab.value = tab

  // 3. 下一帧测量新 Tab 高度并设置（触发 CSS transition）
  nextTick(() => {
    const newHeight = getActiveHeight(tab)
    // 用 requestAnimationFrame 确保浏览器已应用了锁定高度
    requestAnimationFrame(() => {
      panelHeight.value = newHeight + 'px'
    })
  })
}

// 初始化：挂载后设置初始高度
onMounted(() => {
  nextTick(() => {
    const h = getActiveHeight(activeTab.value)
    if (h > 0) {
      panelHeight.value = h + 'px'
      // 短暂延迟后恢复 auto
      requestAnimationFrame(() => {
        panelHeight.value = 'auto'
      })
    }
  })
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
