<script setup lang="ts">
/**
 * 管理后台主布局
 * 参考 art-design-pro 的经典布局：左侧边栏 + 顶栏 + 内容区
 * 暗色模式独立于博客前台,通过 .admin-dark class 控制
 */
import { ref, onMounted } from 'vue'
import Sidebar from './Sidebar.vue'
import Topbar from './Topbar.vue'

/** 侧边栏折叠状态 */
const collapsed = ref(false)

/** 暗色模式状态（独立于博客前台,存 localStorage） */
const isDark = ref(false)
const DARK_KEY = 'admin_dark_mode'

onMounted(() => {
  // 从 localStorage 恢复暗色模式偏好
  isDark.value = localStorage.getItem(DARK_KEY) === 'true'
  applyDarkClass()
})

/** 切换侧边栏折叠 */
function toggleCollapse() {
  collapsed.value = !collapsed.value
}

/** 切换暗色模式 */
function toggleDark() {
  isDark.value = !isDark.value
  localStorage.setItem(DARK_KEY, String(isDark.value))
  applyDarkClass()
}

/** 将暗色 class 应用到 admin 容器 */
function applyDarkClass() {
  const el = document.getElementById('admin-app')
  if (el) {
    el.classList.toggle('admin-dark', isDark.value)
  }
}
</script>

<template>
  <div
    id="admin-app"
    class="admin-layout"
    :class="{ 'admin-dark': isDark }"
  >
    <!-- 侧边栏 -->
    <aside
      class="admin-layout-sidebar"
      :class="{ 'is-collapsed': collapsed }"
    >
      <Sidebar :collapsed="collapsed" />
    </aside>

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
  --admin-text-color: #303133;
  --admin-text-secondary: #909399;
  --admin-border-color: #e4e7ed;
  --admin-menu-active-bg: #ecf5ff;
  --admin-menu-hover-bg: #f5f7fa;

  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

/* ---------- CSS 变量：暗色主题 ---------- */
.admin-layout.admin-dark {
  --admin-primary-color: #409eff;
  --admin-sidebar-bg: #141414;
  --admin-topbar-bg: #1d1d1d;
  --admin-content-bg: #0a0a0a;
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

/* ---------- 页面切换过渡动画 ---------- */
.admin-fade-enter-active,
.admin-fade-leave-active {
  transition: opacity 0.2s ease;
}

.admin-fade-enter-from,
.admin-fade-leave-to {
  opacity: 0;
}
</style>
