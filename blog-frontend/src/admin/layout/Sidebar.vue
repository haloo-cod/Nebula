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

const emit = defineEmits<{
  /** 移动端选择菜单后关闭抽屉。 */
  navigate: []
}>()

/** 当前激活的菜单路径 */
const activeMenu = computed(() => route.path)

/** 菜单点击跳转 */
function handleMenuSelect(path: string) {
  void router.push(path)
  emit('navigate')
}
</script>

<template>
  <div class="admin-sidebar">
    <div class="sidebar-brand">
      <span class="brand-mark" aria-hidden="true">S</span>
      <div v-if="!collapsed" class="brand-copy">
        <strong>Starlit</strong>
        <span>内容管理</span>
      </div>
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

.sidebar-logo,
.sidebar-brand {
  display: flex;
  align-items: center;
  height: 64px;
  padding: 0 18px;
  border-bottom: 1px solid var(--admin-border-color);
  flex-shrink: 0;
}

.sidebar-brand {
  gap: 11px;
}

.brand-mark {
  display: grid;
  width: 32px;
  height: 32px;
  flex: 0 0 32px;
  place-items: center;
  border-radius: 10px;
  background: var(--admin-primary-color);
  color: #ffffff;
  font-family: Georgia, serif;
  font-size: 18px;
  font-weight: 700;
  box-shadow: 0 5px 12px color-mix(in srgb, var(--admin-primary-color) 24%, transparent);
}

.brand-copy {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 1px;
}

.brand-copy strong {
  color: var(--admin-text-color);
  font-size: 15px;
  line-height: 1.2;
}

.brand-copy span {
  color: var(--admin-text-secondary);
  font-size: 11px;
  line-height: 1.2;
}

.logo-text,
.logo-text-mini {
  font-weight: 700;
  color: var(--admin-text-color);
  white-space: nowrap;
}

.logo-text {
  font-size: 18px;
}

.logo-text-mini {
  margin: 0 auto;
  color: var(--admin-primary-color);
  font-size: 20px;
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
  height: 48px;
  margin: 4px 12px;
  padding: 0 12px;
  border-radius: 10px;
  color: var(--admin-text-secondary);
  font-size: 13px;
  font-weight: 550;
  transition:
    background-color 180ms ease,
    color 180ms ease,
    transform 180ms ease;
}

:deep(.el-menu-item .el-icon) {
  margin-right: 12px;
  color: currentColor;
  font-size: 18px;
}

:deep(.el-menu-item.is-active) {
  color: var(--admin-primary-color) !important;
  font-weight: 650;
  box-shadow: inset 3px 0 0 var(--admin-primary-color);
}

:deep(.el-menu-item:hover) {
  color: var(--admin-text-color);
  transform: translateX(2px);
}
</style>
