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
  --admin-primary-color: #409eff;
  --admin-sidebar-bg: #ffffff;
  --admin-topbar-bg: #ffffff;
  --admin-content-bg: #f5f7fa;
  --admin-panel-bg: #ffffff;
  --admin-fill-bg: #f5f7fa;
  --admin-text-color: #303133;
  --admin-text-secondary: #909399;
  --admin-border-color: #e4e7ed;
  --admin-menu-active-bg: #ecf5ff;
  --admin-menu-hover-bg: #f5f7fa;

  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  color: var(--admin-text-color);
  background: var(--admin-content-bg);
  font-family:
    'Zen Maru Gothic',
    -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

/* ---------- CSS 变量：暗色主题 ---------- */
.admin-layout.admin-dark {
  --admin-primary-color: #409eff;
  --admin-sidebar-bg: #141414;
  --admin-topbar-bg: #1d1d1d;
  --admin-content-bg: #0a0a0a;
  --admin-panel-bg: #1d1e1f;
  --admin-fill-bg: #262727;
  --admin-text-color: #e5eaf3;
  --admin-text-secondary: #a3a6ad;
  --admin-border-color: #303030;
  --admin-menu-active-bg: #1d3043;
  --admin-menu-hover-bg: #1a1a1a;
}

/* ---------- 侧边栏 ---------- */
.admin-layout-sidebar {
  width: 220px;
  flex-shrink: 0;
  transition: width 0.3s ease;
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
  overflow: hidden;
  min-width: 0;
}

.admin-layout-header {
  flex-shrink: 0;
}

.admin-layout-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
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
  .admin-layout-sidebar {
    position: fixed;
    inset: 0 auto 0 0;
    z-index: 1001;
    width: min(82vw, 280px);
    transform: translateX(-100%);
    transition: transform 0.25s ease;
    box-shadow: 8px 0 28px rgba(0, 0, 0, 0.18);
  }

  .admin-layout-sidebar.is-collapsed {
    width: min(82vw, 280px);
  }

  .admin-layout.mobile-sidebar-open .admin-layout-sidebar {
    transform: translateX(0);
  }

  .admin-sidebar-overlay {
    position: fixed;
    inset: 0;
    z-index: 1000;
    display: block;
    border: 0;
    background: rgba(0, 0, 0, 0.38);
    cursor: pointer;
  }

  .admin-layout-content {
    padding: 12px;
  }
}
</style>

<style>
/* 后台弹窗挂载到 body，使用全局规则保证移动端尺寸不被各页面的 width 属性撑破。 */
.admin-layout ~ .el-overlay .el-dialog,
.el-overlay .el-dialog {
  max-width: calc(100vw - 32px);
  box-sizing: border-box;
}

.el-overlay .el-dialog__body {
  max-height: min(70vh, 680px);
  overflow-y: auto;
}

@media (max-width: 767px) {
  .el-overlay .el-dialog {
    width: calc(100vw - 24px) !important;
    margin: 12px auto;
    border-radius: 10px;
  }

  .el-overlay .el-dialog__header {
    padding: 16px 16px 10px;
  }

  .el-overlay .el-dialog__title {
    font-size: 16px;
  }

  .el-overlay .el-dialog__body {
    max-height: calc(100vh - 180px);
    padding: 12px 16px 16px;
  }

  .el-overlay .el-dialog__footer {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
    padding: 10px 16px 16px;
  }

  .el-overlay .el-dialog__footer .el-button {
    min-width: 76px;
    margin-left: 0;
  }

  .el-overlay .el-form-item {
    margin-bottom: 16px;
  }

  .el-overlay .el-form-item__label {
    padding-bottom: 4px;
  }

  .el-overlay .el-form--inline .el-form-item {
    display: flex;
    width: 100%;
    margin-right: 0;
  }

  .el-overlay .el-form--inline .el-form-item__content,
  .el-overlay .el-form--inline .el-input,
  .el-overlay .el-form--inline .el-select {
    width: 100% !important;
  }

  .el-overlay .el-upload-dragger {
    width: 100%;
    box-sizing: border-box;
  }
}
</style>
