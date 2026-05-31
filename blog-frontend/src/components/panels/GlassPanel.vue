<template>
  <div class="panel" :class="{ 'panel-compact': compact }">
    <slot />
  </div>
</template>

<script setup>
defineProps({
  compact: {
    type: Boolean,
    default: false,
  },
})
</script>

<style scoped>
/* ============================================
   毛玻璃面板 - 全站公共样式
   ============================================ */
.panel {
  background: rgba(0, 0, 0, 0.35); /* 面板背景透明度，越大越不透明 */
  backdrop-filter: blur(12px); /* 毛玻璃模糊程度 */
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 1rem; /* 圆角大小 */
  padding: 1.5rem; /* 面板内边距 */
  min-height: 200px; /* 面板最小高度 */
}

.panel-compact {
  padding: 1.5rem;
}
</style>
