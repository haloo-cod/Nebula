<script setup lang="ts">
/**
 * 管理后台顶部栏
 * 包含：折叠按钮 + 面包屑 + 暗色模式切换 + 用户下拉菜单
 */
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { Fold, Expand, Moon, House, SwitchButton, ArrowDown } from '@element-plus/icons-vue'
import { adminMenus } from './AdminMenu'

defineProps<{
  /** 侧边栏是否折叠 */
  collapsed: boolean
}>()

const emit = defineEmits<{
  /** 切换侧边栏折叠状态 */
  toggleCollapse: []
  /** 切换暗色模式 */
  toggleDark: []
}>()

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

/** 当前页面标题（匹配菜单配置） */
const currentTitle = computed(() => {
  const menu = adminMenus.find((m) => route.path.startsWith(m.path))
  return menu?.title ?? '管理后台'
})

/** 处理用户下拉命令 */
async function handleCommand(command: string) {
  if (command === 'logout') {
    await authStore.logout()
    await router.push('/admin/login')
  } else if (command === 'home') {
    // 返回博客前台
    router.push('/')
  }
}
</script>

<template>
  <div class="admin-topbar">
    <div class="topbar-left">
      <button
        class="admin-icon-button collapse-btn"
        type="button"
        :aria-label="collapsed ? '展开侧边栏' : '收起侧边栏'"
        @click="emit('toggleCollapse')"
      >
        <el-icon :size="19">
          <Fold v-if="!collapsed" />
          <Expand v-else />
        </el-icon>
      </button>
      <div class="page-context">
        <span class="context-kicker">WORKSPACE</span>
        <strong>{{ currentTitle }}</strong>
      </div>
    </div>

    <div class="topbar-right">
      <button
        class="admin-icon-button action-btn"
        type="button"
        aria-label="切换暗色模式"
        @click="emit('toggleDark')"
      >
        <el-icon :size="18"><Moon /></el-icon>
      </button>

      <el-dropdown trigger="click" @command="handleCommand">
        <button class="user-menu-button" type="button" aria-label="打开管理员菜单">
          <span class="avatar" aria-hidden="true">{{
            (authStore.user?.username ?? '管').slice(0, 1).toUpperCase()
          }}</span>
          <span class="username">{{ authStore.user?.username ?? '管理员' }}</span>
          <el-icon class="user-chevron"><ArrowDown /></el-icon>
        </button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="home">
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
  min-height: 64px;
  padding: 0 clamp(14px, 2.5vw, 32px);
  background: transparent;
  border: 0;
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.admin-icon-button,
.user-menu-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 42px;
  min-height: 42px;
  border: 0;
  border-radius: 11px;
  background: transparent;
  color: var(--admin-text-secondary);
  cursor: pointer;
  transition:
    color 180ms ease,
    background-color 180ms ease,
    transform 180ms ease;
}

.admin-icon-button:hover,
.user-menu-button:hover {
  background: var(--admin-menu-hover-bg);
  color: var(--admin-text-color);
}

.admin-icon-button:active,
.user-menu-button:active {
  transform: translateY(1px);
}

.page-context {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.context-kicker {
  color: var(--admin-text-secondary);
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.16em;
  line-height: 1.2;
}

.breadcrumb-text {
  font-size: 16px;
  font-weight: 600;
  color: var(--admin-text-color);
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-menu-button {
  gap: 8px;
  padding: 0 8px 0 6px;
}

.avatar {
  display: grid;
  width: 30px;
  height: 30px;
  place-items: center;
  border-radius: 10px;
  background: var(--admin-menu-active-bg);
  color: var(--admin-primary-color);
  font-size: 13px;
  font-weight: 700;
}

.user-chevron {
  color: var(--admin-text-secondary);
  font-size: 14px;
}

.username {
  max-width: 130px;
  overflow: hidden;
  color: var(--admin-text-color);
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 767px) {
  .admin-topbar {
    min-height: 58px;
    padding: 0 10px;
  }

  .topbar-left,
  .topbar-right {
    gap: 7px;
  }

  .breadcrumb-text {
    font-size: 14px;
  }

  .context-kicker {
    display: none;
  }

  .username,
  .user-chevron {
    display: none;
  }

  .user-menu-button {
    min-width: 42px;
    padding: 0;
  }
}
</style>
