<template>
  <header class="liquid-glass-nav">
    <!-- 左侧：Logo + 翻译按钮 -->
    <div class="nav-left">
      <span class="logo">Starlit'blog</span>
      <div ref="translateRef" class="translate-wrap" translate="no">
        <button class="translate-btn" @click.stop="langOpen = !langOpen">
          <SvgIcon name="international" class="translate-icon" />
          <span class="translate-label">{{ currentLabel }}</span>
          <span class="translate-arrow" :class="{ 'is-open': langOpen }">▼</span>
        </button>
        <Transition name="lang-drop">
          <ul v-if="langOpen" class="lang-menu">
            <li
              v-for="lang in languages"
              :key="lang.code"
              class="lang-item"
              :class="currentLang === lang.code ? 'lang-item-active' : ''"
              @click="switchLang(lang.code)"
            >
              {{ lang.label }}
            </li>
          </ul>
        </Transition>
      </div>
    </div>

    <!-- 中部菜单（仅桌面端可见） -->
    <nav class="nav-menu">
      <RouterLink
        v-for="item in navItems"
        :key="item.path"
        :to="
          item.path === '/'
            ? { path: '/', state: { showContent: true, skipLiquidGlassReveal: true } }
            : item.path
        "
        class="menu-item"
        :class="{ active: isActive(item.path) }"
        @click="closeMenu"
      >
        <SvgIcon :name="item.icon" class="menu-icon" />
        <span class="menu-label">{{ item.label }}</span>
        <div class="active-dot" v-if="isActive(item.path)"></div>
      </RouterLink>
    </nav>

    <!-- 右侧功能区（仅桌面端可见） -->
    <div class="nav-actions">
      <button
        class="theme-pull-switch"
        :class="{ 'is-moon': themeIcon === 'moon', 'is-dragging': isThemeDragging }"
        :style="pullStyle"
        type="button"
        :aria-label="themeIcon === 'moon' ? '切换到浅色图标' : '切换到深色图标'"
        :aria-pressed="themeIcon === 'moon'"
        @click="onThemeClick"
        @pointerdown="onThemePointerDown"
        @pointermove="onThemePointerMove"
        @pointerup="onThemePointerUp"
        @pointercancel="onThemePointerCancel"
      >
        <span class="switch-anchor" aria-hidden="true"></span>
        <span class="switch-rig">
          <span class="switch-cord"></span>
          <span class="switch-handle">
            <SvgIcon name="sun" class="theme-icon theme-icon-sun" />
            <SvgIcon name="moon" class="theme-icon theme-icon-moon" />
          </span>
        </span>
      </button>
      <Transition name="theme-toast">
        <div v-if="themeToastVisible" class="theme-toast" role="status" aria-live="polite">
          {{ themeToastText }}
        </div>
      </Transition>
      <Transition name="tavern-confirm">
        <div
          v-if="tavernConfirmOpen"
          class="tavern-confirm"
          role="dialog"
          aria-modal="true"
          aria-label="深夜酒馆入口确认"
        >
          <p class="tavern-confirm-kicker">深夜的门铃响了第五次</p>
          <p class="tavern-confirm-title">酒馆的门开了一条缝，要进去吗？</p>
          <div class="tavern-confirm-actions">
            <button
              class="tavern-confirm-btn tavern-confirm-btn--ghost"
              type="button"
              @click="cancelTavernEntry"
            >
              先不进去
            </button>
            <button
              class="tavern-confirm-btn tavern-confirm-btn--primary"
              type="button"
              @click="enterTavern"
            >
              进入深夜酒馆
            </button>
          </div>
        </div>
      </Transition>
      <div ref="settingsRef" class="settings-wrap" translate="no">
        <button
          class="icon-btn"
          :class="{ 'icon-btn-active': settingsOpen }"
          aria-label="设置"
          aria-haspopup="dialog"
          :aria-expanded="settingsOpen"
          @click.stop="settingsOpen = !settingsOpen"
        >
          <SvgIcon name="settings" class="action-icon" />
        </button>
        <Transition name="settings-drop">
          <div v-if="settingsOpen" class="settings-panel" role="dialog" aria-label="显示设置面板">
            <div class="settings-section">
              <div class="settings-head">
                <div class="settings-copy">
                  <span class="settings-title">背景模糊</span>
                  <span class="settings-value"
                    >{{ ui.backgroundBlurEnabled ? ui.backgroundBlur : 0 }}px</span
                  >
                </div>
                <button
                  class="settings-toggle"
                  :class="{ 'settings-toggle--on': ui.backgroundBlurEnabled }"
                  type="button"
                  :aria-pressed="ui.backgroundBlurEnabled"
                  @click="ui.setBackgroundBlurEnabled(!ui.backgroundBlurEnabled)"
                >
                  <span class="settings-toggle-thumb"></span>
                </button>
              </div>
              <input
                class="settings-slider"
                type="range"
                min="0"
                max="24"
                step="1"
                :value="ui.backgroundBlur"
                :disabled="!ui.backgroundBlurEnabled"
                @input="onBackgroundBlurInput"
              />
            </div>

            <div class="settings-section settings-section--divider">
              <div class="settings-head">
                <div class="settings-copy">
                  <span class="settings-title">液态玻璃</span>
                </div>
                <button
                  class="settings-toggle"
                  :class="{ 'settings-toggle--on': ui.liquidGlassEnabled }"
                  type="button"
                  :aria-pressed="ui.liquidGlassEnabled"
                  @click="ui.setLiquidGlassEnabled(!ui.liquidGlassEnabled)"
                >
                  <span class="settings-toggle-thumb"></span>
                </button>
              </div>
              <div class="settings-head settings-head--compact">
                <span class="settings-subtitle">玻璃模糊</span>
                <span class="settings-value">{{ ui.liquidGlassBlur }}px</span>
              </div>
              <input
                class="settings-slider"
                type="range"
                min="0"
                max="12"
                step="1"
                :value="ui.liquidGlassBlur"
                :disabled="!ui.liquidGlassEnabled"
                @input="onLiquidGlassBlurInput"
              />
            </div>
          </div>
        </Transition>
      </div>
    </div>

    <!-- 移动端菜单按钮 -->
    <button
      class="mobile-toggle"
      :class="{ 'is-open': menuOpen }"
      @click="menuOpen = !menuOpen"
      aria-label="Toggle menu"
    >
      <span></span>
      <span></span>
      <span></span>
    </button>

    <!-- 移动端下拉菜单 -->
    <Transition name="menu-slide">
      <ul v-if="menuOpen" class="mobile-menu">
        <li v-for="item in navItems" :key="item.path">
          <RouterLink
            :to="
              item.path === '/'
                ? { path: '/', state: { showContent: true, skipLiquidGlassReveal: true } }
                : item.path
            "
            class="mobile-link"
            :class="isActive(item.path) ? 'mobile-link-active' : 'mobile-link-inactive'"
            @click="closeMenu"
          >
            <SvgIcon :name="item.icon" class="nav-icon" />
            <span>{{ item.label }}</span>
          </RouterLink>
        </li>
      </ul>
    </Transition>
  </header>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { languages } from '@/i18n/languages'
import { getCurrentLang, setLang, getLangLabel } from '@/i18n'
import SvgIcon from '@/components/SvgIcon.vue'
import { useUIStore } from '@/stores/ui'

const ui = useUIStore()
const currentLang = ref(getCurrentLang())
const langOpen = ref(false)
const translateRef = ref<HTMLElement | null>(null)
const settingsOpen = ref(false)
const settingsRef = ref<HTMLElement | null>(null)
// 图标随主题:暗色显示月亮,亮色显示太阳
const themeIcon = computed<'sun' | 'moon'>(() => (ui.theme === 'light' ? 'sun' : 'moon'))
const themeToastText = ref('')
const themeToastVisible = ref(false)
const isThemeDragging = ref(false)
const pullDistance = ref(0)
const pullOffsetX = ref(0)
const themeAnchorClientX = ref(0)
const themeAnchorClientY = ref(0)
const themeDragMoved = ref(false)
const suppressThemeClick = ref(false)
const tavernConfirmOpen = ref(false)
const THEME_HANDLE_BASE_Y = 48
const THEME_PULL_MAX_X = 34
const THEME_PULL_THRESHOLD = 22
const THEME_ANCHOR_CENTER_OFFSET = 9
const THEME_EGG_WINDOW = 10000
const THEME_TAVERN_TRIGGER_COUNT = 5
const themeEggTimestamps: number[] = []
let themeResetTimer: number | null = null
let themeToastTimer: number | null = null

const currentLabel = computed(() => getLangLabel(currentLang.value))
const pullStyle = computed(() => {
  const handleY = THEME_HANDLE_BASE_Y + pullDistance.value
  const cordLength = Math.hypot(pullOffsetX.value, handleY)
  const cordAngle = -Math.atan2(pullOffsetX.value, handleY)
  return {
    '--handle-x': `${pullOffsetX.value}px`,
    '--handle-y': `${handleY}px`,
    '--cord-length': `${cordLength}px`,
    '--cord-angle': `${cordAngle}rad`,
  }
})

function toggleThemeIcon() {
  ui.toggleTheme()
}

function clearThemeResetTimer() {
  if (themeResetTimer) {
    clearTimeout(themeResetTimer)
    themeResetTimer = null
  }
}

function clearThemeToastTimer() {
  if (themeToastTimer) {
    clearTimeout(themeToastTimer)
    themeToastTimer = null
  }
}

function showThemeToast(text: string) {
  clearThemeToastTimer()
  themeToastText.value = text
  themeToastVisible.value = true
  themeToastTimer = window.setTimeout(() => {
    themeToastVisible.value = false
    themeToastTimer = null
  }, 2400)
}

function recordThemeEggTrigger() {
  if (tavernConfirmOpen.value) return
  const now = Date.now()
  while (themeEggTimestamps.length > 0 && now - themeEggTimestamps[0] > THEME_EGG_WINDOW) {
    themeEggTimestamps.shift()
  }
  themeEggTimestamps.push(now)
  if (themeEggTimestamps.length >= 3) {
    showThemeToast('告诉你，不要再深夜的酒吧点炒面（doge')
    if (themeEggTimestamps.length >= THEME_TAVERN_TRIGGER_COUNT) {
      tavernConfirmOpen.value = true
    }
    return
  }
  showThemeToast('绳子只有这么长啦！')
}

function resetThemeEggCounter() {
  themeEggTimestamps.length = 0
}

function cancelTavernEntry() {
  tavernConfirmOpen.value = false
  resetThemeEggCounter()
  showThemeToast('门又悄悄合上了。')
}

function enterTavern() {
  tavernConfirmOpen.value = false
  resetThemeEggCounter()
  router.push('/midnight-tavern')
}

function animateThemePull(depth = 18) {
  clearThemeResetTimer()
  pullOffsetX.value = 0
  pullDistance.value = depth
  themeResetTimer = window.setTimeout(() => {
    pullDistance.value = 0
    pullOffsetX.value = 0
    themeResetTimer = null
  }, 180)
}

function onThemeClick() {
  if (suppressThemeClick.value) {
    suppressThemeClick.value = false
    return
  }
  toggleThemeIcon()
  animateThemePull(16)
}

function onThemePointerDown(e: PointerEvent) {
  isThemeDragging.value = true
  pullDistance.value = 0
  pullOffsetX.value = 0
  themeDragMoved.value = false
  clearThemeResetTimer()
  const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
  themeAnchorClientX.value = rect.left + rect.width / 2
  themeAnchorClientY.value = rect.top + THEME_ANCHOR_CENTER_OFFSET
  ;(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId)
}

function onThemePointerMove(e: PointerEvent) {
  if (!isThemeDragging.value) return
  const maxVisualDistance = Math.max(
    THEME_PULL_THRESHOLD,
    window.innerHeight * 0.5 - themeAnchorClientY.value - THEME_HANDLE_BASE_Y,
  )
  const rawDistance = Math.max(0, e.clientY - themeAnchorClientY.value - THEME_HANDLE_BASE_Y)
  const offsetX = Math.max(
    -THEME_PULL_MAX_X,
    Math.min(THEME_PULL_MAX_X, e.clientX - themeAnchorClientX.value),
  )
  const distance =
    rawDistance <= THEME_PULL_THRESHOLD
      ? rawDistance
      : THEME_PULL_THRESHOLD +
        (maxVisualDistance - THEME_PULL_THRESHOLD) *
          Math.pow(
            Math.min(
              1,
              (rawDistance - THEME_PULL_THRESHOLD) / (maxVisualDistance - THEME_PULL_THRESHOLD),
            ),
            1.35,
          )
  pullDistance.value = distance
  pullOffsetX.value = offsetX
  if (distance > 4 || Math.abs(offsetX) > 4) themeDragMoved.value = true

  if (e.clientY >= window.innerHeight * 0.5) {
    if ((e.currentTarget as HTMLElement).hasPointerCapture(e.pointerId)) {
      ;(e.currentTarget as HTMLElement).releasePointerCapture(e.pointerId)
    }
    isThemeDragging.value = false
    suppressThemeClick.value = true
    clearThemeResetTimer()
    pullDistance.value = 0
    pullOffsetX.value = 0
    themeDragMoved.value = false
    recordThemeEggTrigger()
  }
}

function onThemePointerUp(e: PointerEvent) {
  if (!isThemeDragging.value) return
  const shouldToggle = pullDistance.value >= THEME_PULL_THRESHOLD
  isThemeDragging.value = false
  if ((e.currentTarget as HTMLElement).hasPointerCapture(e.pointerId)) {
    ;(e.currentTarget as HTMLElement).releasePointerCapture(e.pointerId)
  }
  if (shouldToggle) {
    toggleThemeIcon()
    suppressThemeClick.value = true
  } else if (themeDragMoved.value) {
    suppressThemeClick.value = true
  }
  clearThemeResetTimer()
  pullDistance.value = 0
  pullOffsetX.value = 0
  themeDragMoved.value = false
}

function onThemePointerCancel(e: PointerEvent) {
  isThemeDragging.value = false
  if ((e.currentTarget as HTMLElement).hasPointerCapture(e.pointerId)) {
    ;(e.currentTarget as HTMLElement).releasePointerCapture(e.pointerId)
  }
  clearThemeResetTimer()
  pullDistance.value = 0
  pullOffsetX.value = 0
  themeDragMoved.value = false
}

function switchLang(code: string) {
  currentLang.value = code
  setLang(code)
  langOpen.value = false
}

function onBackgroundBlurInput(event: Event) {
  const value = Number((event.target as HTMLInputElement).value)
  ui.setBackgroundBlur(value)
}

function onLiquidGlassBlurInput(event: Event) {
  const value = Number((event.target as HTMLInputElement).value)
  ui.setLiquidGlassBlur(value)
}

function onDocumentClick(e: MouseEvent) {
  if (langOpen.value && translateRef.value && !translateRef.value.contains(e.target as Node)) {
    langOpen.value = false
  }
  if (settingsOpen.value && settingsRef.value && !settingsRef.value.contains(e.target as Node)) {
    settingsOpen.value = false
  }
}

/** 导航项 */
interface NavItem {
  label: string
  path: string
  icon: string
}

const navItems: NavItem[] = [
  { label: '首页', path: '/', icon: 'home' },
  { label: '博文', path: '/blog', icon: 'article' },
  { label: '图书', path: '/books', icon: 'book' },
  { label: '归档', path: '/archive', icon: 'archive' },
  { label: '展览', path: '/gallery', icon: 'gallery' },
  { label: '图片', path: '/images', icon: 'photo' },
  { label: '友链', path: '/friends', icon: 'friends' },
  { label: '藏宝阁', path: '/treasure', icon: 'gift' },
  { label: '关于', path: '/about', icon: 'about' },
]

const route = useRoute()
const router = useRouter()
const menuOpen = ref(false)

function isActive(path: string): boolean {
  if (path === '/') return route.path === '/'
  if (path === '/blog') return route.path === '/blog' || route.path.startsWith('/post/')
  return route.path === path || route.path.startsWith(path + '/')
}

function closeMenu() {
  menuOpen.value = false
}

onMounted(() => {
  document.addEventListener('click', onDocumentClick)
})

onUnmounted(() => {
  document.removeEventListener('click', onDocumentClick)
  clearThemeResetTimer()
  clearThemeToastTimer()
})
</script>

<style scoped>
/* ============================================
   液态玻璃导航栏 — 核心容器
   暗底透明玻璃 + backdrop-filter + 镜面高光
   ============================================ */
.liquid-glass-nav {
  position: fixed;
  top: 0;
  left: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 64px;
  padding: 0 30px;
  margin: 0;
  width: 100%;
  max-width: 100%;

  /* 极致通透：极低透明度 + 背景模糊 */
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-radius: 0 0 16px 16px;

  /* 液态玻璃边缘光晕 */
  border: 1px solid rgba(255, 255, 255, 0.2);

  /* 内高光折射 + 外悬浮阴影 */
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.3),
    inset 0 0 20px rgba(255, 255, 255, 0.08),
    0 4px 32px rgba(0, 0, 0, 0.25),
    0 12px 60px rgba(0, 0, 0, 0.15);
}

.nav-left,
.nav-menu,
.nav-actions {
  position: relative;
  z-index: 1;
}

/* ============================================
   左侧：Logo + 翻译
   ============================================ */
.nav-left {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
}

.logo {
  font-weight: 800;
  font-size: 1.15rem;
  color: #ffffff;
  text-shadow: 0 2px 12px rgba(0, 0, 0, 0.9);
  letter-spacing: 0.5px;
  white-space: nowrap;
  user-select: none;
  background: none;
}

/* 翻译按钮容器 */
.translate-wrap {
  position: relative;
}

.translate-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 7px 14px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.12);
  cursor: pointer;
  color: #ffffff;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.7);
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  transition:
    background 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.translate-btn:hover {
  background: rgba(255, 255, 255, 0.22);
  border-color: rgba(255, 255, 255, 0.5);
  box-shadow: 0 2px 14px rgba(0, 0, 0, 0.3);
}

.translate-icon {
  font-size: 16px;
}

.translate-label {
  white-space: nowrap;
}

.translate-arrow {
  font-size: 10px;
  transition: transform 0.3s ease;
  color: #ffffff;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.7);
}

.translate-arrow.is-open {
  transform: rotate(180deg);
}

/* 语言下拉菜单 — 液态玻璃,极高层级确保不被导航栏遮挡 */
.lang-menu {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  z-index: 1000;
  min-width: 100%;
  display: flex;
  flex-direction: column;
  padding: 6px;
  border-radius: 12px;
  background: rgba(20, 20, 30, 0.4);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
}

.lang-item {
  padding: 9px 14px;
  font-size: 14px;
  font-weight: 500;
  color: #ffffff;
  text-shadow: 0 2px 6px rgba(0, 0, 0, 0.6);
  border-radius: 10px;
  cursor: pointer;
  white-space: nowrap;
  transition:
    color 0.15s ease,
    background 0.15s ease;
}

.lang-item:hover {
  color: #3b82f6;
  background: rgba(255, 255, 255, 0.1);
}

.lang-item-active {
  color: #60a5fa;
  background: rgba(96, 165, 250, 0.15);
  font-weight: 600;
}

.lang-drop-enter-active {
  transition: all 0.2s ease;
}
.lang-drop-leave-active {
  transition: all 0.15s ease;
}
.lang-drop-enter-from {
  opacity: 0;
  transform: translateY(-6px);
}
.lang-drop-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

/* ============================================
   中部菜单（仅桌面端）
   所有文字纯白 + text-shadow 确保星空背景可读
   ============================================ */
.nav-menu {
  display: flex;
  align-items: center;
  gap: 4px;
}

.menu-item {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 20px;
  cursor: pointer;
  color: #ffffff;
  text-shadow: 0 2px 12px rgba(0, 0, 0, 0.8);
  font-size: 0.85rem;
  font-weight: 500;
  text-decoration: none;
  transition: all 0.2s ease;
  position: relative;
}

.menu-item:hover {
  background: rgba(255, 255, 255, 0.12);
}

.menu-item.active {
  color: #ffffff;
  text-shadow: 0 2px 16px rgba(0, 0, 0, 0.9);
}

.menu-icon {
  font-size: 1.2rem;
  line-height: 1;
}

.menu-label {
  font-size: 1rem;
}

/* 激活状态 — 带发光的蓝色小圆点指示器 */
.active-dot {
  position: absolute;
  bottom: -8px;
  left: 50%;
  transform: translateX(-50%);
  width: 5px;
  height: 5px;
  background-color: #60a5fa;
  border-radius: 50%;
  box-shadow:
    0 0 8px rgba(96, 165, 250, 0.8),
    0 0 16px rgba(96, 165, 250, 0.4),
    0 0 24px rgba(96, 165, 250, 0.2);
}

/* ============================================
   右侧功能区（仅桌面端）
   ============================================ */
.nav-actions {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-shrink: 0;
}

.theme-toast {
  position: absolute;
  top: calc(100% + 10px);
  right: 44px;
  max-width: min(280px, calc(100vw - 2rem));
  padding: 9px 14px;
  border-radius: 999px;
  background: rgba(18, 24, 38, 0.68);
  border: 1px solid rgba(255, 255, 255, 0.16);
  color: rgba(255, 255, 255, 0.92);
  font-size: 13px;
  line-height: 1.4;
  white-space: nowrap;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.2),
    0 10px 28px rgba(0, 0, 0, 0.28);
}

.theme-toast-enter-active,
.theme-toast-leave-active {
  transition:
    opacity 0.2s ease,
    transform 0.2s ease;
}

.theme-toast-enter-from,
.theme-toast-leave-to {
  opacity: 0;
  transform: translateY(-6px) scale(0.98);
}

.tavern-confirm {
  position: absolute;
  top: calc(100% + 18px);
  right: 0;
  width: min(320px, calc(100vw - 2rem));
  padding: 1rem;
  border: 1px solid rgba(255, 231, 186, 0.22);
  border-radius: 1.2rem;
  background:
    linear-gradient(135deg, rgba(44, 30, 20, 0.78), rgba(18, 24, 34, 0.7)), rgba(20, 18, 22, 0.68);
  color: rgba(255, 246, 225, 0.92);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  box-shadow:
    inset 0 1px 0 rgba(255, 244, 218, 0.16),
    0 22px 54px rgba(0, 0, 0, 0.34);
}

.tavern-confirm-kicker {
  margin: 0 0 0.38rem;
  color: rgba(255, 205, 134, 0.72);
  font-size: 0.72rem;
  letter-spacing: 0.12em;
}

.tavern-confirm-title {
  margin: 0;
  font-size: 0.96rem;
  line-height: 1.55;
}

.tavern-confirm-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.55rem;
  margin-top: 0.95rem;
}

.tavern-confirm-btn {
  border: 1px solid rgba(255, 238, 208, 0.2);
  border-radius: 999px;
  padding: 0.44rem 0.78rem;
  color: rgba(255, 246, 225, 0.92);
  cursor: pointer;
  font-size: 0.78rem;
  transition:
    background 0.2s ease,
    border-color 0.2s ease,
    transform 0.2s ease;
}

.tavern-confirm-btn:hover {
  transform: translateY(-1px);
}

.tavern-confirm-btn--ghost {
  background: rgba(255, 255, 255, 0.06);
}

.tavern-confirm-btn--primary {
  background: rgba(162, 96, 48, 0.42);
  border-color: rgba(255, 210, 145, 0.36);
}

.tavern-confirm-enter-active,
.tavern-confirm-leave-active {
  transition:
    opacity 0.22s ease,
    transform 0.22s ease;
}

.tavern-confirm-enter-from,
.tavern-confirm-leave-to {
  opacity: 0;
  transform: translateY(-8px) scale(0.98);
}

.theme-pull-switch {
  position: relative;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  width: 60px;
  height: 86px;
  padding: 0;
  border: none;
  background: transparent;
  color: #ffffff;
  cursor: pointer;
  filter: drop-shadow(0 8px 18px rgba(0, 0, 0, 0.32));
}

.switch-anchor {
  position: absolute;
  top: 4px;
  left: 50%;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  transform: translateX(-50%);
  background: radial-gradient(
    circle,
    rgba(255, 255, 255, 0.72),
    rgba(255, 255, 255, 0.18) 70%,
    transparent 72%
  );
  box-shadow:
    0 0 0 1px rgba(255, 255, 255, 0.18),
    0 0 12px rgba(255, 255, 255, 0.32);
}

.switch-rig {
  position: absolute;
  top: 4px;
  left: 50%;
  width: 34px;
  height: 82px;
  transform: translateX(-50%);
}

.switch-cord {
  position: absolute;
  top: 0;
  left: 50%;
  width: 4px;
  margin-left: -2px;
  height: var(--cord-length, 48px);
  border-radius: 999px;
  background:
    linear-gradient(
      90deg,
      rgba(255, 255, 255, 0.18),
      rgba(255, 255, 255, 0.86),
      rgba(255, 255, 255, 0.22)
    ),
    rgba(255, 255, 255, 0.18);
  box-shadow:
    0 0 8px rgba(255, 255, 255, 0.28),
    inset 0 1px 0 rgba(255, 255, 255, 0.35);
  transform-origin: top center;
  transition:
    height 0.28s ease,
    transform 0.28s ease;
  transform: rotate(var(--cord-angle, 0rad));
}

.switch-handle {
  position: absolute;
  top: var(--handle-y, 48px);
  left: 50%;
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background:
    radial-gradient(circle at 30% 22%, rgba(255, 255, 255, 0.62), transparent 32%),
    radial-gradient(circle at 70% 78%, rgba(96, 165, 250, 0.16), transparent 36%),
    linear-gradient(145deg, rgba(255, 255, 255, 0.22), rgba(255, 255, 255, 0.08));
  border: 1px solid rgba(255, 255, 255, 0.32);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -10px 18px rgba(0, 0, 0, 0.16),
    0 6px 18px rgba(0, 0, 0, 0.24);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  transition:
    transform 0.28s cubic-bezier(0.34, 1.56, 0.64, 1),
    top 0.28s cubic-bezier(0.34, 1.56, 0.64, 1),
    background 0.28s ease,
    border-color 0.28s ease;
  transform: translateX(calc(-50% + var(--handle-x, 0px))) translateY(-50%);
}

.theme-icon {
  grid-area: 1 / 1;
  font-size: 18px;
  transition:
    opacity 0.22s ease,
    transform 0.28s ease;
}

.theme-icon-sun {
  color: #fde68a;
  opacity: 1;
  filter: drop-shadow(0 0 8px rgba(253, 230, 138, 0.55));
}

.theme-icon-moon {
  color: #bfdbfe;
  opacity: 0;
  transform: translateY(4px) rotate(-18deg) scale(0.7);
  filter: drop-shadow(0 0 8px rgba(147, 197, 253, 0.45));
}

.theme-pull-switch:hover .switch-handle {
  background:
    radial-gradient(circle at 32% 24%, rgba(255, 255, 255, 0.62), transparent 34%),
    linear-gradient(145deg, rgba(255, 255, 255, 0.28), rgba(96, 165, 250, 0.14));
  border-color: rgba(255, 255, 255, 0.48);
}

.theme-pull-switch:active .switch-handle {
  transform: translateX(calc(-50% + var(--handle-x, 0px))) translateY(-50%) scale(0.96);
}

.theme-pull-switch.is-dragging .switch-cord,
.theme-pull-switch.is-dragging .switch-handle,
.theme-pull-switch.is-dragging .theme-icon {
  transition-duration: 0s;
}

.theme-pull-switch.is-moon .switch-handle {
  transform: translateX(calc(-50% + var(--handle-x, 0px))) translateY(-50%);
}

.theme-pull-switch.is-moon .theme-icon-sun {
  opacity: 0;
  transform: translateY(-4px) rotate(16deg) scale(0.7);
}

.theme-pull-switch.is-moon .theme-icon-moon {
  opacity: 1;
  transform: translateY(0) rotate(0) scale(1);
}

.theme-pull-switch:focus-visible {
  outline: 2px solid rgba(147, 197, 253, 0.9);
  outline-offset: 4px;
  border-radius: 999px;
}

.icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: transparent;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  color: #ffffff;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.7);
  transition:
    background 0.2s ease,
    color 0.2s ease;
}

.settings-wrap {
  position: relative;
}

.icon-btn:hover {
  background: rgba(255, 255, 255, 0.15);
  color: #ffffff;
}

.icon-btn-active {
  background: rgba(255, 255, 255, 0.18);
}

.action-icon {
  font-size: 20px;
}

.settings-panel {
  position: absolute;
  top: calc(100% + 10px);
  right: 0;
  z-index: 1000;
  width: 268px;
  padding: 14px;
  border-radius: 16px;
  background: rgba(18, 24, 38, 0.68);
  border: 1px solid rgba(255, 255, 255, 0.16);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.18),
    0 16px 38px rgba(0, 0, 0, 0.28);
}

.settings-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.settings-section--divider {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.settings-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
}

.settings-head--compact {
  margin-bottom: 0;
}

.settings-copy {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.settings-title {
  color: rgba(255, 255, 255, 0.92);
  font-size: 13px;
  font-weight: 600;
  line-height: 1.2;
}

.settings-subtitle {
  color: rgba(255, 255, 255, 0.72);
  font-size: 12px;
  line-height: 1.2;
}

.settings-value {
  color: rgba(176, 224, 255, 0.9);
  font-size: 12px;
  line-height: 1.2;
}

.settings-toggle {
  position: relative;
  width: 42px;
  height: 24px;
  flex-shrink: 0;
  padding: 0;
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  cursor: pointer;
  transition:
    background 0.18s ease,
    border-color 0.18s ease;
}

.settings-toggle--on {
  background: rgba(96, 165, 250, 0.3);
  border-color: rgba(147, 197, 253, 0.45);
}

.settings-toggle-thumb {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.24);
  transition: transform 0.18s ease;
}

.settings-toggle--on .settings-toggle-thumb {
  transform: translateX(18px);
}

.settings-slider {
  width: 100%;
  accent-color: #93c5fd;
  cursor: pointer;
}

.settings-slider:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.settings-drop-enter-active,
.settings-drop-leave-active {
  transition:
    opacity 0.18s ease,
    transform 0.18s ease;
}

.settings-drop-enter-from,
.settings-drop-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

/* ============================================
   移动端适配
   ============================================ */
@media (max-width: 767px) {
  .liquid-glass-nav {
    width: 100%;
    height: 56px;
    padding: 0 16px;
    margin: 0;
    border-radius: 0 0 16px 16px;
  }

  .logo {
    font-size: 1rem;
  }

  .translate-btn {
    padding: 5px 10px;
    font-size: 12px;
  }

  .translate-label {
    display: none;
  }

  .translate-icon {
    font-size: 18px;
  }

  .translate-arrow {
    display: none;
  }
}

/* 移动端：隐藏桌面菜单和功能区 */
@media (max-width: 767px) {
  .nav-menu {
    display: none;
  }
  .nav-actions {
    display: none;
  }
}

/* 桌面端：隐藏移动端汉堡按钮和下拉菜单 */
@media (min-width: 769px) {
  .mobile-toggle {
    display: none !important;
  }
  .mobile-menu {
    display: none !important;
  }
}

/* ============================================
   移动端汉堡按钮
   ============================================ */
.mobile-toggle {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 5px;
  padding: 0;
  border: 1px solid rgba(255, 255, 255, 0.25);
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  transition:
    background 0.2s ease,
    border-color 0.2s ease;
}

.mobile-toggle:hover {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.4);
}

.mobile-toggle span {
  display: block;
  width: 18px;
  height: 2px;
  background: #ffffff;
  border-radius: 2px;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.5);
  transition: all 0.3s ease;
  transform-origin: center;
}

.mobile-toggle.is-open span:nth-child(1) {
  transform: translateY(7px) rotate(45deg);
}
.mobile-toggle.is-open span:nth-child(2) {
  opacity: 0;
  transform: scaleX(0);
}
.mobile-toggle.is-open span:nth-child(3) {
  transform: translateY(-7px) rotate(-45deg);
}

/* ============================================
   移动端下拉菜单
   ============================================ */
.mobile-menu {
  position: fixed;
  top: 88px;
  left: 1rem;
  right: 1rem;
  z-index: 55;
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px;
  border-radius: 1.5rem;
  background: rgba(20, 20, 40, 0.94);
  backdrop-filter: blur(24px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.5);
}

.mobile-link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  font-size: 16px;
  font-weight: 500;
  border-radius: 12px;
  text-decoration: none;
  transition:
    background 0.2s ease,
    color 0.2s ease;
}

.mobile-link-inactive {
  color: rgba(255, 255, 255, 0.6);
}

.mobile-link-inactive:hover {
  color: rgba(255, 255, 255, 0.9);
  background: rgba(255, 255, 255, 0.08);
}

.mobile-link-active {
  color: #ffffff;
  background: rgba(255, 255, 255, 0.12);
}

.nav-icon {
  font-size: 20px;
  line-height: 1;
}

/* 移动端菜单动画 */
.menu-slide-enter-active {
  transition: all 0.25s ease;
}
.menu-slide-leave-active {
  transition: all 0.2s ease;
}
.menu-slide-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}
.menu-slide-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
