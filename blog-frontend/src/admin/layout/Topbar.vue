<script setup lang="ts">
/**
 * 管理后台顶部栏
 * 包含：折叠按钮 + 面包屑 + 暗色模式切换 + 用户下拉菜单
 */
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { Fold, Expand, Moon, User, House, SwitchButton } from '@element-plus/icons-vue'
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
    <!-- 左侧：折叠按钮 + 面包屑 -->
    <div class="topbar-left">
      <el-icon class="collapse-btn" :size="20" @click="emit('toggleCollapse')">
        <Fold v-if="!collapsed" />
        <Expand v-else />
      </el-icon>
      <span class="breadcrumb-text">{{ currentTitle }}</span>
    </div>

    <!-- 右侧：暗色模式 + 用户 -->
    <div class="topbar-right">
      <el-icon class="action-btn" :size="18" @click="emit('toggleDark')">
        <Moon />
      </el-icon>

      <el-dropdown trigger="click" @command="handleCommand">
        <span class="user-info">
          <el-icon :size="18"><User /></el-icon>
          <span class="username">{{ authStore.user?.username ?? '管理员' }}</span>
        </span>
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
  height: 56px;
  padding: 0 20px;
  background: var(--admin-topbar-bg);
  border-bottom: 1px solid var(--admin-border-color);
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.collapse-btn {
  cursor: pointer;
  color: var(--admin-text-color);
  transition: color 0.2s;
}

.collapse-btn:hover {
  color: var(--admin-primary-color);
}

.breadcrumb-text {
  font-size: 16px;
  font-weight: 500;
  color: var(--admin-text-color);
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.action-btn {
  cursor: pointer;
  color: var(--admin-text-color);
  transition: color 0.2s;
}

.action-btn:hover {
  color: var(--admin-primary-color);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  color: var(--admin-text-color);
  transition: color 0.2s;
}

.user-info:hover {
  color: var(--admin-primary-color);
}

.username {
  font-size: 14px;
}

@media (max-width: 767px) {
  .admin-topbar {
    height: 52px;
    padding: 0 12px;
  }

  .topbar-left,
  .topbar-right {
    gap: 10px;
  }

  .breadcrumb-text {
    font-size: 14px;
  }

  .username {
    max-width: 92px;
    overflow: hidden;
    font-size: 12px;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}
</style>
