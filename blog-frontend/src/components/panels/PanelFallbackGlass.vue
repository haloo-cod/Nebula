<template>
  <component
    :is="tag"
    class="panel-fallback-glass"
    :class="{ 'panel-fallback-glass--static-blur': staticBlur }"
    :style="staticBlurStyle"
  >
    <slot />
  </component>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useUIStore } from '@/stores/ui'

// 共享的关态毛玻璃外壳,直接复用首页已经验证过的 surface 语义。
const props = withDefaults(
  defineProps<{
    tag?: string
    /** 使用复制背景图的普通 blur，避免动态 backdrop-filter 重采样。 */
    staticBlur?: boolean
  }>(),
  {
    tag: 'div',
    staticBlur: false,
  },
)

const ui = useUIStore()
const staticBlurStyle = computed(() =>
  props.staticBlur
    ? { '--panel-background': `url(${ui.currentBgUrl})` }
    : undefined,
)
</script>

<style scoped>
.panel-fallback-glass {
  position: relative;
  flex: 1;
  width: 100%;
  height: 100%;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.24),
    inset 0 0 20px rgba(255, 255, 255, 0.06),
  0 8px 28px rgba(0, 0, 0, 0.18);
  overflow: hidden;
}

/* 独立的滤镜层不随轮播、图表和按钮内容一起重绘。 */
.panel-fallback-glass::before {
  position: absolute;
  inset: 0;
  z-index: 0;
  border-radius: inherit;
  background: transparent;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  content: '';
  pointer-events: none;
}

.panel-fallback-glass > * {
  position: relative;
  z-index: 1;
}

.panel-fallback-glass--empty {
  min-height: 100%;
}

/* 用页面背景的副本做普通 blur，不参与页面背后的动态重采样。 */
.panel-fallback-glass--static-blur {
  background: rgba(255, 255, 255, 0.14);
  border-color: rgba(255, 255, 255, 0.12);
  box-shadow:
    0 8px 28px rgba(0, 0, 0, 0.18),
    inset 0 1px 0 rgba(255, 255, 255, 0.12),
    inset 0 0 20px rgba(255, 255, 255, 0.04);
  isolation: isolate;
}

.panel-fallback-glass--static-blur::before {
  inset: -18px;
  background-image: var(--panel-background);
  background-position: center;
  background-size: cover;
  background-attachment: fixed;
  filter: blur(12px);
  opacity: 0.9;
}

.panel-fallback-glass--static-blur::after {
  position: absolute;
  inset: 0;
  z-index: 0;
  background: rgba(255, 255, 255, 0.1);
  content: '';
  pointer-events: none;
}

/* 移动端无复杂 transform 交互，直接用 backdrop-filter 替代 staticBlur 的伪元素背景方案 */
@media (max-width: 768px) {
  .panel-fallback-glass--static-blur::before {
    inset: 0;
    background-image: none;
    background-attachment: initial;
    filter: none;
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
  }

  .panel-fallback-glass--static-blur :deep(.post-carousel),
  .panel-fallback-glass--static-blur :deep(.moment-carousel) {
    transform: translateZ(0);
    backface-visibility: hidden;
  }
}

</style>
