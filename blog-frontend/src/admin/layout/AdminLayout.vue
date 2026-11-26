<script setup lang="ts">
/**
 * 管理后台主布局
 * 亮色默认采用方案 A（纸墨刊物），暗色切换采用方案 B（星夜曜石）。
 * 同步在 <html> 挂载 admin-theme 与 dark 类，确保 Teleport 浮层与页面配色一致。
 */
import { onBeforeUnmount, onMounted, ref } from 'vue'
import 'element-plus/es/components/message/style/css'
import 'element-plus/es/components/message-box/style/css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import '@/assets/admin.css'
import Sidebar from './Sidebar.vue'
import Topbar from './Topbar.vue'
import AdminCommandPalette from '@/admin/components/AdminCommandPalette.vue'

/** 侧边栏折叠状态 */
const collapsed = ref(false)
const mobileSidebarOpen = ref(false)
const commandOpen = ref(false)

/** 暗色模式状态（独立于博客前台，默认亮色） */
const DARK_KEY = 'admin_dark_mode'
const isDark = ref(typeof localStorage !== 'undefined' && localStorage.getItem(DARK_KEY) === 'true')

// 在子页面挂载前同步根主题类，避免首帧闪烁。
document.documentElement.classList.add('admin-theme')
document.documentElement.classList.toggle('dark', isDark.value)

/** 全局 ⌘K / Ctrl+K 唤起快捷命令面板 */
function handleGlobalKeydown(event: KeyboardEvent) {
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
    event.preventDefault()
    commandOpen.value = !commandOpen.value
  }
}

onMounted(() => {
  applyDarkTheme()
  window.addEventListener('keydown', handleGlobalKeydown)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleGlobalKeydown)
  document.documentElement.classList.remove('dark', 'admin-theme')
})

/** 切换侧边栏折叠或移动端抽屉 */
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

/** 同步 Element Plus 根主题，并通知 Vditor 等第三方组件 */
function applyDarkTheme() {
  document.documentElement.classList.add('admin-theme')
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

    <div class="admin-layout-main">
      <header class="admin-layout-header">
        <Topbar
          :collapsed="collapsed"
          :is-dark="isDark"
          @toggle-collapse="toggleCollapse"
          @toggle-dark="toggleDark"
          @open-command="commandOpen = true"
        />
      </header>

      <main class="admin-layout-content">
        <router-view v-slot="{ Component }">
          <transition name="admin-fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>

    <AdminCommandPalette v-model="commandOpen" :is-dark="isDark" @toggle-dark="toggleDark" />
  </div>
</template>

<style scoped>
.admin-layout {
  display: flex;
  flex-direction: row;
  height: 100dvh;
  min-height: 100dvh;
  width: 100%;
  overflow: hidden;
  color: var(--admin-text-color);
  background: var(--admin-content-bg);
  font-family: var(--admin-font-sans);
}

.admin-layout-sidebar {
  width: 224px;
  flex-shrink: 0;
  transition: width 220ms ease;
  overflow: hidden;
}

.admin-layout-sidebar.is-collapsed {
  width: 64px;
}

.admin-layout-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
}

.admin-layout-header {
  height: 54px;
  flex-shrink: 0;
  background: var(--admin-topbar-bg);
  border-bottom: 1px solid var(--admin-border-color);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.admin-layout-content {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding: 24px clamp(18px, 3vw, 36px) 44px;
  background: var(--admin-content-bg);
}

.admin-sidebar-overlay {
  display: none;
}

.admin-fade-enter-active,
.admin-fade-leave-active {
  transition: opacity 160ms ease;
}

.admin-fade-enter-from,
.admin-fade-leave-to {
  opacity: 0;
}

@media (max-width: 767px) {
  .admin-layout-main {
    min-height: 100dvh;
  }

  .admin-layout-sidebar {
    position: fixed;
    inset: 0 auto 0 0;
    z-index: 30;
    width: min(82vw, 276px);
    transform: translateX(-100%);
    transition: transform 220ms ease;
    box-shadow: var(--admin-shadow-overlay);
  }

  .admin-layout-sidebar.is-collapsed {
    width: min(82vw, 276px);
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
    background: rgba(11, 12, 14, 0.45);
    cursor: pointer;
  }

  .admin-layout-content {
    padding: 18px 14px 28px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .admin-layout-sidebar,
  .admin-fade-enter-active,
  .admin-fade-leave-active {
    transition: none;
  }
}
</style>
