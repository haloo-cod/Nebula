<template>
  <GlassPanel
    :flat="flat"
    class="panel-placeholder flex flex-col items-center justify-center text-center"
  >
    <span class="placeholder-icon">{{ icon }}</span>
    <span class="placeholder-text">{{ text }}</span>
  </GlassPanel>
</template>

<script setup lang="ts">
import GlassPanel from './GlassPanel.vue'

withDefaults(
  defineProps<{
    icon?: string // 占位图标
    text?: string // 占位文案
    flat?: boolean // 是否使用扁平(无毛玻璃)样式
  }>(),
  {
    icon: '✦',
    text: '更多内容',
    flat: false,
  },
)
</script>

<style scoped>
.panel-placeholder {
  min-height: 200px;
}

.placeholder-icon {
  font-size: 1.5rem;
  color: rgba(255, 255, 255, 0.15);
  margin-bottom: 0.5rem;
}

.placeholder-text {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.25);
}
</style>
