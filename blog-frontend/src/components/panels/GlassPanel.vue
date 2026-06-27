<template>
  <div class="panel" :class="{ 'panel-compact': compact, 'panel-flat': flat }">
    <slot />
  </div>
</template>

<script setup lang="ts">
// 玻璃面板组件，提供毛玻璃效果和统一的样式 ,黑色毛玻璃的面板组件
withDefaults(
  defineProps<{
    compact?: boolean // 紧凑模式,减小内边距
    // flat: 去掉毛玻璃(backdrop-filter blur),仅保留半透明底色,用于两侧面板
    flat?: boolean
  }>(),
  {
    compact: false,
    flat: false,
  },
)
</script>

<style scoped>
/* ============================================
   毛玻璃面板 - 全站公共样式
   ============================================ */
.panel {
  background: var(--glass-bg);
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  border: 1px solid var(--glass-border);
  border-radius: 1rem;
  padding: 1.5rem;
  min-height: 200px;
}

.panel-compact {
  padding: 1.5rem;
}

/* 扁平变体：去掉毛玻璃模糊，保持主题一致的半透明底色 */
.panel-flat {
  backdrop-filter: none;
  -webkit-backdrop-filter: none;
}
</style>
