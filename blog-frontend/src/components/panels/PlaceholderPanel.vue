<template>
  <div
    :flat="flat"
    class="panel-placeholder flex flex-col items-center justify-center text-center"
  >
    <span class="placeholder-icon">{{ icon }}</span>
    <span class="placeholder-text">{{ text }}</span>
  </div>
</template>

<script setup lang="ts">


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

</style>
