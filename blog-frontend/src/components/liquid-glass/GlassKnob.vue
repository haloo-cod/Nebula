<template>
  <!--
    GlassKnob — 圆形/胶囊形液态玻璃珠
    liquidGlassEnabled 开启时用真 WebGL 折射;关闭时回退 CSS 玻璃珠。
  -->
  <div
    class="glass-knob"
    :class="[`glass-knob--${shape}`, { 'glass-knob--fallback': !useGlass }]"
    :style="{ width: size + 'px', height: size + 'px' }"
  >
    <LiquidGlass
      v-if="useGlass"
      class="glass-knob__gl"
      :corner-radius="cornerRadius"
      :theme="theme"
      :blur-radius="0"
      :allow-reveal="false"
      :realtime-offset="true"
    />
  </div>
</template>

<script setup lang="ts">
/**
 * GlassKnob — 通用玻璃珠组件
 *
 * 用于开关 thumb 和滑块 thumb。内部挂一个小尺寸 LiquidGlass,
 * liquidGlassEnabled 关闭时自动降级为 CSS 径向渐变高光珠。
 */
import { computed } from 'vue'
import LiquidGlass from '@/components/liquid-glass/LiquidGlass.vue'
import { useUIStore } from '@/stores/ui'

const props = withDefaults(
  defineProps<{
    /** 珠子直径(px),默认 22 */
    size?: number
    /** 形状:'circle' = 正圆 / 'capsule' = 胶囊(宽高可不等) */
    shape?: 'circle' | 'capsule'
    /** 显式宽度(胶囊形时使用),不传时等于 size */
    width?: number
    /** 当前主题 */
    theme?: 'light' | 'dark'
  }>(),
  {
    size: 22,
    shape: 'circle',
    theme: 'dark',
  },
)

const ui = useUIStore()

/** 只有 liquidGlassEnabled 开启才渲染真 WebGL */
const useGlass = computed(() => ui.liquidGlassEnabled)

/** 圆角半径:圆形/胶囊均用最大值让它完全圆 */
const cornerRadius = computed(() => {
  const w = props.width ?? props.size
  const h = props.size
  return Math.min(w, h) / 2
})
</script>

<style scoped>
.glass-knob {
  position: relative;
  flex-shrink: 0;
  border-radius: 50%;
  overflow: hidden;
  pointer-events: none; /* 交互由父级按钮/容器处理 */
}

.glass-knob--capsule {
  border-radius: 999px;
}

/* WebGL 玻璃层铺满 */
.glass-knob__gl {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  border-radius: inherit;
}

/* ============================================
   CSS 降级玻璃珠(liquidGlassEnabled 关闭时)
   使用 backdrop-filter 真模糊 + 高光边
   ============================================ */
.glass-knob--fallback {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(6px) saturate(1.4);
  -webkit-backdrop-filter: blur(6px) saturate(1.4);
  border: 1px solid rgba(255, 255, 255, 0.35);
  box-shadow:
    inset 0 1px 1px rgba(255, 255, 255, 0.55),
    inset 0 -1px 1px rgba(0, 0, 0, 0.1),
    0 2px 6px rgba(0, 0, 0, 0.2);
}

[data-theme='light'] .glass-knob--fallback {
  background: rgba(255, 255, 255, 0.55);
  border-color: rgba(255, 255, 255, 0.7);
  box-shadow:
    inset 0 1px 1px rgba(255, 255, 255, 0.85),
    0 1px 4px rgba(0, 0, 0, 0.14);
}
</style>
