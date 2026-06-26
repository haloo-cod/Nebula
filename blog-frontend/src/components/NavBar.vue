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
        :to="item.path"
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
      <button class="icon-btn" aria-label="设置">
        <SvgIcon name="settings" class="action-icon" />
      </button>
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
            :to="item.path"
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
import { RouterLink, useRoute } from 'vue-router'
import { languages } from '@/i18n/languages'
import { getCurrentLang, setLang, getLangLabel } from '@/i18n'
import SvgIcon from '@/components/SvgIcon.vue'

const currentLang = ref(getCurrentLang())
const langOpen = ref(false)
const translateRef = ref<HTMLElement | null>(null)

const currentLabel = computed(() => getLangLabel(currentLang.value))

function switchLang(code: string) {
  currentLang.value = code
  setLang(code)
  langOpen.value = false
}

function onDocumentClick(e: MouseEvent) {
  if (!langOpen.value) return
  if (translateRef.value && !translateRef.value.contains(e.target as Node)) {
    langOpen.value = false
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
  { label: '归档', path: '/archive', icon: 'archive' },
  { label: '展览', path: '/gallery', icon: 'gallery' },
  { label: '友链', path: '/friends', icon: 'friends' },
  { label: '藏宝阁', path: '/treasure', icon: 'gift' },
  { label: '关于', path: '/about', icon: 'about' },
]

const route = useRoute()
const menuOpen = ref(false)

function isActive(path: string): boolean {
  if (path === '/') return route.path === '/' || route.path.startsWith('/post/')
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
  gap: 8px;
  flex-shrink: 0;
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

.icon-btn:hover {
  background: rgba(255, 255, 255, 0.15);
  color: #ffffff;
}

.action-icon {
  font-size: 20px;
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
