<script setup lang="ts">
/**
 * 管理后台顶部栏
 * 提供折叠开关、两段式面包屑、⌘K 全局命令搜索入口、写文章主操作、亮/暗主题切换与用户菜单。
 */
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  Fold,
  Expand,
  Moon,
  Sunny,
  House,
  SwitchButton,
  Search,
  EditPen,
} from '@element-plus/icons-vue'
import { findAdminMenuContext } from './AdminMenu'

defineProps<{
  /** 侧边栏是否折叠 */
  collapsed: boolean
  /** 当前是否为暗色模式 */
  isDark: boolean
}>()

const emit = defineEmits<{
  toggleCollapse: []
  toggleDark: []
  openCommand: []
}>()

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

/** 当前页面面包屑上下文 */
const menuContext = computed(() => findAdminMenuContext(route.path))

const pageTitle = computed(() => {
  if (route.path === '/admin/posts/new') return '新建文章'
  if (route.path.startsWith('/admin/posts/') && route.path !== '/admin/posts') return '编辑文章'
  return menuContext.value.item?.title ?? '管理后台'
})

const isPostEditorRoute = computed(
  () => route.path === '/admin/posts/new' || route.path.startsWith('/admin/posts/'),
)

/** 处理用户下拉命令 */
async function handleCommand(command: string) {
  if (command === 'logout') {
    await authStore.logout()
    await router.push('/admin/login')
  } else if (command === 'home') {
    await router.push('/')
  } else if (command === 'profile') {
    await router.push('/admin/profile')
  }
}
</script>

<template>
  <div class="admin-topbar">
    <div class="topbar-left">
      <button
        class="admin-icon-button"
        type="button"
        :aria-label="collapsed ? '展开侧边栏' : '收起侧边栏'"
        @click="emit('toggleCollapse')"
      >
        <el-icon :size="17">
          <Fold v-if="!collapsed" />
          <Expand v-else />
        </el-icon>
      </button>

      <nav class="topbar-breadcrumb" aria-label="当前位置">
        <span class="crumb-group">{{ menuContext.groupTitle }}</span>
        <span class="crumb-sep" aria-hidden="true">/</span>
        <strong class="crumb-current">{{ pageTitle }}</strong>
      </nav>
    </div>

    <button
      type="button"
      class="topbar-command-pill"
      aria-label="搜索模块或命令"
      @click="emit('openCommand')"
    >
      <el-icon class="cmd-icon"><Search /></el-icon>
      <span class="cmd-placeholder">搜索文章、说说、命令...</span>
      <kbd class="cmd-shortcut">⌘K</kbd>
    </button>

    <div class="topbar-right">
      <button
        type="button"
        class="admin-icon-button mobile-search-btn"
        aria-label="打开命令搜索"
        @click="emit('openCommand')"
      >
        <el-icon :size="16"><Search /></el-icon>
      </button>

      <el-button
        v-if="!isPostEditorRoute"
        type="primary"
        size="small"
        class="topbar-write-btn"
        @click="router.push('/admin/posts/new')"
      >
        <el-icon><EditPen /></el-icon>写文章
      </el-button>

      <button
        class="theme-switch-pill"
        type="button"
        :aria-label="isDark ? '切换为亮色模式' : '切换为暗色模式'"
        @click="emit('toggleDark')"
      >
        <span class="theme-chip" :class="{ 'is-active': !isDark }" aria-hidden="true">
          <el-icon :size="14"><Sunny /></el-icon>
        </span>
        <span class="theme-chip" :class="{ 'is-active': isDark }" aria-hidden="true">
          <el-icon :size="14"><Moon /></el-icon>
        </span>
      </button>

      <el-dropdown trigger="click" @command="handleCommand">
        <button class="user-menu-button" type="button" aria-label="打开管理员菜单">
          <span class="avatar" aria-hidden="true">
            {{ (authStore.user?.username ?? 'S').slice(0, 1).toUpperCase() }}
          </span>
        </button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item disabled>
              {{ authStore.user?.display_name || authStore.user?.username || '管理员' }}
            </el-dropdown-item>
            <el-dropdown-item command="home" divided>
              <el-icon><House /></el-icon>返回前台
            </el-dropdown-item>
            <el-dropdown-item command="logout" divided>
              <el-icon><SwitchButton /></el-icon>退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<style scoped>
.admin-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  height: 54px;
  padding: 0 clamp(12px, 2.4vw, 28px);
}

.topbar-left,
.topbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.admin-icon-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: var(--admin-text-secondary);
  cursor: pointer;
  transition:
    background-color 140ms ease,
    color 140ms ease;
}

.admin-icon-button:hover {
  background: var(--admin-menu-hover-bg);
  color: var(--admin-text-color);
}

.topbar-breadcrumb {
  display: flex;
  align-items: center;
  gap: 7px;
  min-width: 0;
  font-size: 13px;
  white-space: nowrap;
}

.crumb-group,
.crumb-sep {
  color: var(--admin-text-muted);
}

.crumb-current {
  color: var(--admin-text-color);
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
}

.topbar-command-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  width: min(290px, 34vw);
  height: 34px;
  padding: 0 8px 0 11px;
  border: 1px solid var(--admin-border-color);
  border-radius: 8px;
  background: var(--admin-panel-bg);
  color: var(--admin-text-muted);
  font-size: 12.5px;
  cursor: pointer;
  transition:
    border-color 140ms ease,
    color 140ms ease;
}

.topbar-command-pill:hover {
  border-color: var(--admin-border-strong);
  color: var(--admin-text-secondary);
}

.cmd-icon {
  font-size: 14px;
  flex-shrink: 0;
}

.cmd-placeholder {
  flex: 1;
  text-align: left;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cmd-shortcut {
  padding: 1px 6px;
  border: 1px solid var(--admin-border-color);
  border-radius: 5px;
  background: var(--admin-fill-bg);
  color: var(--admin-text-secondary);
  font-family: var(--admin-font-mono);
  font-size: 10.5px;
}

.mobile-search-btn {
  display: none;
}

.topbar-write-btn {
  height: 32px;
  padding: 0 13px;
}

.theme-switch-pill {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  height: 32px;
  padding: 3px;
  border: 1px solid var(--admin-border-color);
  border-radius: 999px;
  background: var(--admin-fill-bg);
  cursor: pointer;
}

.theme-chip {
  display: grid;
  width: 24px;
  height: 24px;
  place-items: center;
  border-radius: 50%;
  color: var(--admin-text-muted);
  transition:
    background-color 140ms ease,
    color 140ms ease;
}

.theme-chip.is-active {
  background: var(--admin-panel-bg);
  color: var(--admin-text-color);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
}

.user-menu-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  padding: 0;
  border: 1px solid var(--admin-border-color);
  border-radius: 50%;
  background: var(--admin-panel-bg);
  cursor: pointer;
}

.avatar {
  display: grid;
  width: 100%;
  height: 100%;
  place-items: center;
  border-radius: 50%;
  background: var(--admin-menu-active-bg);
  color: var(--admin-primary-color);
  font-size: 12.5px;
  font-weight: 700;
}

@media (max-width: 860px) {
  .topbar-command-pill {
    display: none;
  }

  .mobile-search-btn {
    display: inline-flex;
  }
}

@media (max-width: 640px) {
  .crumb-group,
  .crumb-sep,
  .topbar-write-btn {
    display: none;
  }
}
</style>
