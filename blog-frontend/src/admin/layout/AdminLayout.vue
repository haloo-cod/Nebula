<script setup lang="ts">
/**
 * 管理后台主布局
 * 参考 art-design-pro 的经典布局：左侧边栏 + 顶栏 + 内容区
 * 暗色模式独立于博客前台,通过 .admin-dark class 控制
 */
import { onBeforeUnmount, onMounted, ref } from 'vue'
// Element Plus 通过 JS 调用的组件（ElMessage/ElMessageBox）需要手动引入样式
import 'element-plus/es/components/message/style/css'
import 'element-plus/es/components/message-box/style/css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import '@/assets/admin.css'
import Sidebar from './Sidebar.vue'
import Topbar from './Topbar.vue'

/** 侧边栏折叠状态 */
const collapsed = ref(false)
const mobileSidebarOpen = ref(false)

/** 暗色模式状态（独立于博客前台,存 localStorage） */
const DARK_KEY = 'admin_dark_mode'
const isDark = ref(typeof localStorage !== 'undefined' && localStorage.getItem(DARK_KEY) === 'true')

// 在子页面挂载前应用主题，避免 Element Plus 面板短暂显示亮色。
document.documentElement.classList.toggle('dark', isDark.value)

onMounted(() => {
  applyDarkTheme()
})

onBeforeUnmount(() => {
  document.documentElement.classList.remove('dark')
})

/** 切换侧边栏折叠 */
function toggleCollapse() {
  if (window.matchMedia('(max-width: 767px)').matches) {
    mobileSidebarOpen.value = !mobileSidebarOpen.value
    return
  }
  collapsed.value = !collapsed.value
}

function closeMobileSidebar() {
  mobileSidebarOpen.value = false
}

/** 切换暗色模式 */
function toggleDark() {
  isDark.value = !isDark.value
  localStorage.setItem(DARK_KEY, String(isDark.value))
  applyDarkTheme()
}

/** 同步 Element Plus 根主题，并通知需要独立切换主题的第三方组件 */
function applyDarkTheme() {
  document.documentElement.classList.toggle('dark', isDark.value)
  window.dispatchEvent(new CustomEvent('admin-theme-change', { detail: { isDark: isDark.value } }))
}
</script>

<template>
  <div
    id="admin-app"
    class="admin-layout"
    :class="{ 'admin-dark': isDark, 'mobile-sidebar-open': mobileSidebarOpen }"
  >
    <!-- 侧边栏 -->
    <aside class="admin-layout-sidebar" :class="{ 'is-collapsed': collapsed }">
      <Sidebar :collapsed="collapsed" @navigate="closeMobileSidebar" />
    </aside>

    <button
      v-if="mobileSidebarOpen"
      class="admin-sidebar-overlay"
      type="button"
      aria-label="关闭菜单"
      @click="closeMobileSidebar"
    ></button>

    <!-- 右侧主区域 -->
    <div class="admin-layout-main">
      <!-- 顶栏 -->
      <header class="admin-layout-header">
        <Topbar
          :collapsed="collapsed"
          @toggle-collapse="toggleCollapse"
          @toggle-dark="toggleDark"
        />
      </header>

      <!-- 内容区 -->
      <main class="admin-layout-content">
        <router-view v-slot="{ Component }">
          <transition name="admin-fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<style scoped>
/* ---------- CSS 变量：亮色主题 ---------- */
.admin-layout {
  --admin-primary-color: #1f7a68;
  --admin-sidebar-bg: #ffffff;
  --admin-topbar-bg: rgba(255, 255, 255, 0.92);
  --admin-content-bg: #f4f6f8;
  --admin-panel-bg: #ffffff;
  --admin-fill-bg: #f7f8fa;
  --admin-text-color: #18181b;
  --admin-text-secondary: #71717a;
  --admin-border-color: #e4e4e7;
  --admin-menu-active-bg: #e6f4f0;
  --admin-menu-hover-bg: #f1f5f4;

  display: flex;
  flex-direction: row;
  height: 100dvh;
  min-height: 100dvh;
  width: 100%;
  overflow: hidden;
  color: var(--admin-text-color);
  background: var(--admin-content-bg);
  font-family:
    'Zen Maru Gothic',
    -apple-system,
    BlinkMacSystemFont,
    'Segoe UI',
    Roboto,
    'Helvetica Neue',
    Arial,
    sans-serif;
}

/* ---------- CSS 变量：暗色主题 ---------- */
.admin-layout.admin-dark {
  --admin-primary-color: #62c9ad;
  --admin-sidebar-bg: #151918;
  --admin-topbar-bg: rgba(23, 27, 25, 0.94);
  --admin-content-bg: #101312;
  --admin-panel-bg: #191d1b;
  --admin-fill-bg: #202623;
  --admin-text-color: #f4f7f5;
  --admin-text-secondary: #a8b3ae;
  --admin-border-color: #2b3531;
  --admin-menu-active-bg: #203b33;
  --admin-menu-hover-bg: #222a26;
}

/* ---------- 侧边栏 ---------- */
.admin-layout-sidebar {
  width: 240px;
  flex-shrink: 0;
  transition: width 0.24s ease;
  overflow: hidden;
}

.admin-layout-sidebar.is-collapsed {
  width: 64px;
}

/* ---------- 右侧主区域 ---------- */
.admin-layout-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
}

.admin-layout-header {
  height: 64px;
  flex-shrink: 0;
  background: var(--admin-topbar-bg);
  border-bottom: 1px solid var(--admin-border-color);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
}

.admin-layout-content {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding: 28px clamp(16px, 3vw, 40px) 40px;
  background: var(--admin-content-bg);
}

.admin-sidebar-overlay {
  display: none;
}

/* ---------- 页面切换过渡动画 ---------- */
.admin-fade-enter-active,
.admin-fade-leave-active {
  transition: opacity 0.2s ease;
}

.admin-fade-enter-from,
.admin-fade-leave-to {
  opacity: 0;
}

@media (max-width: 767px) {
  .admin-layout-main {
    min-height: 100dvh;
  }

  .admin-layout-content {
    min-height: 0;
  }

  .admin-layout-sidebar {
    position: fixed;
    inset: 0 auto 0 0;
    z-index: 30;
    width: min(86vw, 300px);
    transform: translateX(-100%);
    transition: transform 0.24s ease;
    box-shadow: 12px 0 32px rgba(0, 0, 0, 0.2);
  }

  .admin-layout-sidebar.is-collapsed {
    width: min(86vw, 300px);
  }

  .admin-layout.mobile-sidebar-open .admin-layout-sidebar {
    transform: translateX(0);
  }

  .admin-sidebar-overlay {
    position: fixed;
    inset: 0;
    z-index: 20;
    display: block;
    width: 100%;
    border: 0;
    background: rgba(9, 12, 11, 0.48);
    cursor: pointer;
  }

  .admin-layout-content {
    min-height: 0;
    padding: 20px 14px 28px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .admin-layout-sidebar,
  .admin-layout-content,
  .admin-fade-enter-active,
  .admin-fade-leave-active {
    transition: none;
  }
}
</style>
