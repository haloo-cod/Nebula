<script setup lang="ts">
/**
 * 管理后台分组侧边栏
 * 按 4 大功能分组组织导航项，折叠态保持图标居中与悬停提示，底部常驻返回前台入口。
 */
import { computed, type Component } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Odometer,
  Document,
  ChatDotRound,
  Reading,
  Picture,
  Camera,
  Connection,
  Present,
  ColdDrink,
  Comment,
  Film,
  Sunrise,
  EditPen,
  User,
  UserFilled,
  FolderOpened,
  Setting,
  DataAnalysis,
  UploadFilled,
  TopRight,
} from '@element-plus/icons-vue'
import { adminMenuGroups } from './AdminMenu'

/** 图标名称到组件映射 */
const iconMap: Record<string, Component> = {
  Odometer,
  Document,
  ChatDotRound,
  Reading,
  Picture,
  Camera,
  Connection,
  Present,
  ColdDrink,
  Comment,
  Film,
  Sunrise,
  EditPen,
  User,
  UserFilled,
  FolderOpened,
  Setting,
  DataAnalysis,
  UploadFilled,
}

defineProps<{
  /** 是否折叠侧边栏 */
  collapsed: boolean
}>()

const route = useRoute()
const router = useRouter()

const emit = defineEmits<{
  /** 移动端点击菜单后关闭抽屉 */
  navigate: []
}>()

/** 判断菜单项是否处于当前激活路径（含子路由如 /admin/posts/new） */
function isItemActive(path: string): boolean {
  return route.path === path || route.path.startsWith(`${path}/`)
}

const currentPath = computed(() => route.path)

function navigateTo(path: string) {
  if (currentPath.value !== path) {
    void router.push(path)
  }
  emit('navigate')
}
</script>

<template>
  <div class="admin-sidebar" :class="{ 'is-collapsed': collapsed }">
    <button
      type="button"
      class="sidebar-brand"
      aria-label="返回管理后台仪表盘"
      @click="navigateTo('/admin/dashboard')"
    >
      <span class="brand-mark" aria-hidden="true">S</span>
      <span v-if="!collapsed" class="brand-wordmark">Starlit</span>
    </button>

    <el-scrollbar class="sidebar-scroll">
      <nav class="sidebar-nav" aria-label="后台导航">
        <div v-for="(group, groupIndex) in adminMenuGroups" :key="group.key" class="nav-group">
          <div v-if="!collapsed" class="nav-group-label">{{ group.title }}</div>
          <div v-else-if="groupIndex > 0" class="nav-group-divider" aria-hidden="true"></div>

          <button
            v-for="item in group.items"
            :key="item.path"
            type="button"
            class="nav-item"
            :class="{ 'is-active': isItemActive(item.path) }"
            :title="collapsed ? item.title : undefined"
            @click="navigateTo(item.path)"
          >
            <el-icon class="nav-item-icon">
              <component :is="iconMap[item.icon]" />
            </el-icon>
            <span v-if="!collapsed" class="nav-item-label">{{ item.title }}</span>
          </button>
        </div>
      </nav>
    </el-scrollbar>

    <footer class="sidebar-footer">
      <button
        type="button"
        class="sidebar-site-link"
        :title="collapsed ? '返回博客前台' : undefined"
        @click="navigateTo('/')"
      >
        <span class="status-dot" aria-hidden="true"></span>
        <span v-if="!collapsed" class="site-link-text">返回前台</span>
        <el-icon v-if="!collapsed" class="site-link-arrow"><TopRight /></el-icon>
      </button>
    </footer>
  </div>
</template>

<style scoped>
.admin-sidebar {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--admin-sidebar-bg);
  border-right: 1px solid var(--admin-border-color);
  user-select: none;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 54px;
  padding: 0 16px;
  border: 0;
  border-bottom: 1px solid var(--admin-border-color);
  background: transparent;
  cursor: pointer;
  flex-shrink: 0;
  text-align: left;
}

.admin-sidebar.is-collapsed .sidebar-brand {
  justify-content: center;
  padding: 0;
}

.brand-mark {
  display: grid;
  width: 28px;
  height: 28px;
  flex: 0 0 28px;
  place-items: center;
  border: 1px solid var(--admin-border-strong);
  border-radius: 7px;
  background: var(--admin-panel-bg);
  color: var(--admin-text-color);
  font-family: var(--admin-font-serif);
  font-size: 15px;
  font-weight: 700;
}

.brand-wordmark {
  color: var(--admin-text-color);
  font-family: var(--admin-font-serif);
  font-size: 17px;
  font-weight: 700;
  letter-spacing: -0.02em;
  white-space: nowrap;
}

.sidebar-scroll {
  flex: 1;
  min-height: 0;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 14px 10px 18px;
}

.nav-group {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-group-label {
  padding: 2px 10px 6px;
  color: var(--admin-text-muted);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.06em;
}

.nav-group-divider {
  height: 1px;
  margin: 4px 10px 6px;
  background: var(--admin-border-color);
}

.nav-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  height: 36px;
  padding: 0 10px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: var(--admin-text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  text-align: left;
  transition:
    background-color 140ms ease,
    color 140ms ease;
}

.admin-sidebar.is-collapsed .nav-item {
  justify-content: center;
  padding: 0;
}

.nav-item:hover {
  background: var(--admin-menu-hover-bg);
  color: var(--admin-text-color);
}

.nav-item.is-active {
  background: var(--admin-menu-active-bg);
  color: var(--admin-nav-active-text);
  font-weight: 600;
}

.nav-item.is-active::before {
  position: absolute;
  left: 0;
  top: 7px;
  bottom: 7px;
  width: 2.5px;
  border-radius: 2px;
  background: var(--admin-nav-active-bar);
  content: '';
}

.nav-item-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.nav-item-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sidebar-footer {
  padding: 10px;
  border-top: 1px solid var(--admin-border-color);
  flex-shrink: 0;
}

.sidebar-site-link {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  height: 34px;
  padding: 0 10px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: var(--admin-text-secondary);
  font-size: 12.5px;
  cursor: pointer;
  transition:
    background-color 140ms ease,
    color 140ms ease;
}

.admin-sidebar.is-collapsed .sidebar-site-link {
  justify-content: center;
  padding: 0;
}

.sidebar-site-link:hover {
  background: var(--admin-menu-hover-bg);
  color: var(--admin-text-color);
}

.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--admin-success-color);
  flex-shrink: 0;
}

.site-link-text {
  flex: 1;
  text-align: left;
}

.site-link-arrow {
  font-size: 13px;
  color: var(--admin-text-muted);
}
</style>
