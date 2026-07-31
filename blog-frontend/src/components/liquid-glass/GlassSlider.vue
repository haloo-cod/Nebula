<template>
  <!--
    GlassSlider — 自定义液态玻璃滑块
    替换原生 <input type="range">，使用 GlassKnob 当 thumb。
    支持键盘操作(方向键/Home/End)和无障碍属性。
  -->
  <div
    ref="rootRef"
    class="glass-slider"
    :class="{ 'glass-slider--disabled': disabled }"
    role="slider"
    :aria-valuenow="modelValue"
    :aria-valuemin="min"
    :aria-valuemax="max"
    :aria-disabled="disabled"
    tabindex="0"
    @keydown="onKeydown"
    @pointerdown="onTrackDown"
  >
    <!-- 轨道底色(凹槽) -->
    <div class="glass-slider__track">
      <!-- 已填充段(accent) -->
      <div class="glass-slider__fill" :style="{ width: fillPercent + '%' }"></div>
    </div>

    <!-- 玻璃珠 thumb -->
    <div
      class="glass-slider__thumb-wrap"
      :style="{ left: thumbLeft }"
      @pointerdown.stop="onThumbDown"
    >
      <GlassKnob
        :size="knobSize"
        shape="capsule"
        :width="knobWidth"
        :theme="theme"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * GlassSlider — 自定义液态玻璃滑块
 *
 * 完整替代 <input type="range">:
 * - thumb 是 GlassKnob(真 WebGL 折射 / CSS 磨砂降级)
 * - 支持拖拽、点击轨道跳转、键盘方向键/Home/End
 * - 无障碍: role=slider + aria-valuenow/min/max/disabled
 */
import { ref, computed } from 'vue'
import GlassKnob from '@/components/liquid-glass/GlassKnob.vue'

const props = withDefaults(
  defineProps<{
    modelValue: number
    min?: number
    max?: number
    step?: number
    disabled?: boolean
    theme?: 'light' | 'dark'
  }>(),
  {
    min: 0,
    max: 100,
    step: 1,
    disabled: false,
    theme: 'dark',
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: number]
}>()

const rootRef = ref<HTMLElement | null>(null)

// knob 胶囊形:高 18px 宽 28px,与层次A 原尺寸接近但更有体积感
const knobSize = 18
const knobWidth = 28

// ============================================================================
// 数值 → 显示换算
// ============================================================================

const range = computed(() => props.max - props.min)

/** 0~100 百分比(用于 fill 宽度和 thumb 定位) */
const fillPercent = computed(() => {
  if (range.value === 0) return 0
  return ((props.modelValue - props.min) / range.value) * 100
})

/**
 * thumb 左边缘位置(CSS left)。
 * knob 中心对齐当前值,两端各留半个 knob 宽避免溢出轨道。
 */
const thumbLeft = computed(() => {
  // 用 calc 让布局在不同宽度下自适应
  return `calc(${fillPercent.value}% - ${knobWidth / 2}px)`
})

// ============================================================================
// 值计算工具
// ============================================================================

/** 把像素 x 转换为 clamp 后的 step-aligned 值 */
function pixelToValue(clientX: number): number {
  const el = rootRef.value
  if (!el) return props.modelValue
  const rect = el.getBoundingClientRect()
  // 有效拖拽区域:轨道全宽
  const ratio = Math.min(1, Math.max(0, (clientX - rect.left) / rect.width))
  const raw = props.min + ratio * range.value
  // snap to step
  const stepped = Math.round(raw / props.step) * props.step
  return Math.min(props.max, Math.max(props.min, stepped))
}

function clampStep(v: number): number {
  const stepped = Math.round(v / props.step) * props.step
  return Math.min(props.max, Math.max(props.min, stepped))
}

// ============================================================================
// 拖拽:点击轨道 & 拖动 thumb
// ============================================================================

let dragging = false

function onTrackDown(e: PointerEvent) {
  if (props.disabled) return
  // 如果点在 thumb 上,交给 onThumbDown 处理
  const target = e.target as HTMLElement
  if (target.closest('.glass-slider__thumb-wrap')) return
  emit('update:modelValue', pixelToValue(e.clientX))
  startDrag(e)
}

function onThumbDown(e: PointerEvent) {
  if (props.disabled) return
  e.preventDefault()
  startDrag(e)
}

function startDrag(e: PointerEvent) {
  dragging = true
  ;(e.currentTarget as HTMLElement | null)?.setPointerCapture?.(e.pointerId)
  rootRef.value?.setPointerCapture(e.pointerId)

  const onMove = (ev: PointerEvent) => {
    if (!dragging) return
    emit('update:modelValue', pixelToValue(ev.clientX))
  }
  const onUp = () => {
    dragging = false
    window.removeEventListener('pointermove', onMove)
    window.removeEventListener('pointerup', onUp)
  }
  window.addEventListener('pointermove', onMove)
  window.addEventListener('pointerup', onUp)
}

// ============================================================================
// 键盘操作
// ============================================================================

function onKeydown(e: KeyboardEvent) {
  if (props.disabled) return
  const cur = props.modelValue
  const bigStep = Math.max(props.step, Math.round(range.value / 10))

  let next: number | null = null
  switch (e.key) {
    case 'ArrowRight':
    case 'ArrowUp':
      next = clampStep(cur + props.step)
      break
    case 'ArrowLeft':
    case 'ArrowDown':
      next = clampStep(cur - props.step)
      break
    case 'PageUp':
      next = clampStep(cur + bigStep)
      break
    case 'PageDown':
      next = clampStep(cur - bigStep)
      break
    case 'Home':
      next = props.min
      break
    case 'End':
      next = props.max
      break
  }
  if (next !== null) {
    e.preventDefault()
    emit('update:modelValue', next)
  }
}
</script>

<style scoped>
.glass-slider {
  position: relative;
  width: 100%;
  height: 28px; /* 可点击高度区域 */
  display: flex;
  align-items: center;
  cursor: pointer;
  outline: none;
  /* touch-action none 防止拖动时页面滚动 */
  touch-action: none;
}

.glass-slider--disabled {
  opacity: 0.4;
  cursor: not-allowed;
  pointer-events: none;
}

/* ——— 轨道 ——— */
.glass-slider__track {
  position: relative;
  width: 100%;
  height: 5px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.22);
  overflow: hidden;
}

/* 已填充段 */
.glass-slider__fill {
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(
    to right,
    rgba(96, 165, 250, 0.7),
    rgba(80, 145, 245, 0.5)
  );
  transition: width 0.05s linear;
  pointer-events: none;
}

/* ——— thumb 包裹层 ——— */
.glass-slider__thumb-wrap {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  /* 弹簧回弹曲线 */
  transition: left 0.05s linear;
  will-change: left;
  cursor: grab;
  /* 扩大触摸区 */
  padding: 6px 2px;
}

.glass-slider__thumb-wrap:active {
  cursor: grabbing;
}

/* focus 可访问性环 */
.glass-slider:focus-visible .glass-slider__thumb-wrap {
  outline: 2px solid rgba(147, 197, 253, 0.7);
  outline-offset: 2px;
  border-radius: 999px;
}

/* ======= 亮色主题 ======= */
[data-theme='light'] .glass-slider__track {
  background: rgba(0, 0, 0, 0.1);
  border-color: rgba(0, 0, 0, 0.1);
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.12);
}

[data-theme='light'] .glass-slider__fill {
  background: linear-gradient(
    to right,
    rgba(50, 100, 220, 0.6),
    rgba(60, 110, 230, 0.4)
  );
}
</style>
