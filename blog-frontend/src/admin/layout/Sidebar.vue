<script setup lang="ts">
/**
 * 管理后台侧边栏
 * 参考 art-design-pro 的左侧菜单布局：Logo + 可折叠菜单列表
 */
import { computed } from 'vue'
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
} from '@element-plus/icons-vue'
import { adminMenus } from './AdminMenu'

/** 图标名称 → 组件映射（用于 <component :is=""> 动态渲染） */
const iconMap: Record<string, unknown> = {
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
}

defineProps<{
  /** 是否折叠侧边栏 */
  collapsed: boolean
}>()

const route = useRoute()
const router = useRouter()

/** 当前激活的菜单路径 */
const activeMenu = computed(() => route.path)

/** 菜单点击跳转 */
function handleMenuSelect(path: string) {
  router.push(path)
}
</script>

<template>
  <div class="admin-sidebar">
    <!-- Logo 区域 -->
    <div class="sidebar-logo">
      <span v-if="!collapsed" class="logo-text">博客管理</span>
      <span v-else class="logo-text-mini">管</span>
    </div>

    <!-- 菜单列表 -->
    <el-scrollbar class="sidebar-menu-wrap">
      <el-menu
        :default-active="activeMenu"
        :collapse="collapsed"
        :collapse-transition="false"
        background-color="transparent"
        text-color="var(--admin-text-color)"
        active-text-color="var(--admin-primary-color)"
        @select="handleMenuSelect"
      >
        <el-menu-item v-for="item in adminMenus" :key="item.path" :index="item.path">
          <el-icon>
            <component :is="iconMap[item.icon]" />
          </el-icon>
          <template #title>{{ item.title }}</template>
        </el-menu-item>
      </el-menu>
    </el-scrollbar>
  </div>
</template>

<style scoped>
.admin-sidebar {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--admin-sidebar-bg);
  border-right: 1px solid var(--admin-border-color);
}

.sidebar-logo {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 56px;
  border-bottom: 1px solid var(--admin-border-color);
  flex-shrink: 0;
}

.logo-text {
  font-size: 18px;
  font-weight: 700;
  color: var(--admin-text-color);
  white-space: nowrap;
}

.logo-text-mini {
  font-size: 20px;
  font-weight: 700;
  color: var(--admin-primary-color);
}

.sidebar-menu-wrap {
  flex: 1;
  overflow: hidden;
}

/* Element Plus 菜单样式覆盖 */
:deep(.el-menu) {
  border-right: none;
}

:deep(.el-menu-item) {
  border-radius: 8px;
  margin: 4px 8px;
  height: 44px;
}

:deep(.el-menu-item.is-active) {
  background: var(--admin-menu-active-bg);
}

:deep(.el-menu-item:hover) {
  background: var(--admin-menu-hover-bg);
}
</style>
