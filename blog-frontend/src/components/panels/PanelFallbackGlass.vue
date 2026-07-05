<template>
  <component :is="tag" class="panel-fallback-glass">
    <slot />
  </component>
</template>

<script setup lang="ts">
// 共享的关态毛玻璃外壳,直接复用首页已经验证过的 surface 语义。
withDefaults(
  defineProps<{
    tag?: string
  }>(),
  {
    tag: 'div',
  },
)
</script>

<style scoped>
.panel-fallback-glass {
  flex: 1;
  width: 100%;
  height: 100%;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.24),
    inset 0 0 20px rgba(255, 255, 255, 0.06),
    0 8px 28px rgba(0, 0, 0, 0.18);
  overflow: hidden;
}

.panel-fallback-glass--empty {
  min-height: 100%;
}
</style>
