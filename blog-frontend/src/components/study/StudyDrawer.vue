<template>
  <Teleport to="body">
    <Transition name="drawer-overlay">
      <div v-show="modelValue" class="drawer-overlay" @click="close"></div>
    </Transition>

    <Transition
      :name="slideTransitionName"
      @after-enter="handleAfterEnter"
      @after-leave="handleAfterLeave"
    >
      <aside
        v-show="modelValue"
        class="study-drawer"
        :class="`study-drawer--${position}`"
        :style="drawerStyle"
      >
        <LiquidGlass
          v-if="ui.liquidGlassEnabled"
          ref="glassRef"
          class="drawer-glass"
          :class="{ 'drawer-glass--webgl-visible': webglVisible }"
          :theme="ui.theme"
          :corner-radius="24"
          :blur-radius="ui.liquidGlassBlur"
          :glass-thickness="46"
          :highlight-width="3.5"
          ripple-trail
          @render-ready="handleRenderReady"
        >
          <div class="drawer-content">
            <button class="drawer-close" type="button" aria-label="关闭" @click="close">✕</button>
            <slot />
          </div>
        </LiquidGlass>

        <PanelFallbackGlass v-else tag="div" class="drawer-glass drawer-glass--fallback">
          <div class="drawer-content">
            <button class="drawer-close" type="button" aria-label="关闭" @click="close">✕</button>
            <slot />
          </div>
        </PanelFallbackGlass>
      </aside>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import LiquidGlass from '@/components/liquid-glass/LiquidGlass.vue'
import PanelFallbackGlass from '@/components/panels/PanelFallbackGlass.vue'
import { useUIStore } from '@/stores/ui'

const props = withDefaults(
  defineProps<{
    modelValue: boolean
    position?: 'left' | 'right'
    width?: string
  }>(),
  {
    position: 'left',
    width: '22rem',
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const ui = useUIStore()
const webglVisible = ref(false)
const webglReady = ref(false)
const handoffReady = ref(false)
const slideTransitionName = computed(() =>
  props.position === 'left' ? 'drawer-slide-left' : 'drawer-slide-right',
)
const glassRef = ref<{
  refreshRenderer: () => void
  prepareReveal: () => void
} | null>(null)

function prepareGlass() {
  webglVisible.value = !ui.liquidGlassEnabled
  webglReady.value = false
  handoffReady.value = false
  if (!ui.liquidGlassEnabled) return
  void nextTick(() => {
    if (!props.modelValue) return
    glassRef.value?.prepareReveal()
  })
}

function handleRenderReady() {
  if (!props.modelValue) return
  webglReady.value = true
  if (handoffReady.value) revealWebgl()
}

function revealWebgl() {
  if (!props.modelValue || !webglReady.value) return
  webglVisible.value = true
}

function handleAfterEnter() {
  handoffReady.value = false
  glassRef.value?.refreshRenderer()
  requestAnimationFrame(() => {
    if (!props.modelValue) return
    glassRef.value?.refreshRenderer()
    requestAnimationFrame(() => {
      if (!props.modelValue) return
      handoffReady.value = true
      revealWebgl()
    })
  })
}

function handleAfterLeave() {
  webglReady.value = false
  handoffReady.value = false
  webglVisible.value = !ui.liquidGlassEnabled
}

watch(
  () => props.modelValue,
  (open) => {
    if (open) prepareGlass()
    else {
      webglVisible.value = !ui.liquidGlassEnabled
      webglReady.value = false
      handoffReady.value = false
    }
  },
  { immediate: true },
)

const drawerStyle = computed(() => ({
  [props.position]: '0',
  width: props.width,
  maxWidth: 'calc(100vw - 3rem)',
}))

function close() {
  emit('update:modelValue', false)
}
</script>

<style scoped>
.drawer-overlay {
  position: fixed;
  inset: 0;
  z-index: 60;
  background: rgba(0, 0, 0, 0.32);
  backdrop-filter: blur(2px);
  -webkit-backdrop-filter: blur(2px);
}

.study-drawer {
  position: fixed;
  top: 0;
  bottom: 0;
  z-index: 61;
  padding: 0.75rem;
}

.drawer-glass {
  width: 100%;
  height: 100%;
  border-radius: 1.25rem;
  overflow: hidden;
}

.drawer-glass::before {
  position: absolute;
  inset: 0;
  z-index: 0;
  border-radius: inherit;
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  box-shadow:
    inset 0 1px 0 var(--glass-highlight),
    var(--glass-shadow);
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  content: '';
  pointer-events: none;
  opacity: 1;
}

.drawer-glass--webgl-visible::before {
  opacity: 0.35;
  transition: opacity 0.1s ease-out;
}

.drawer-glass :deep(.liquid-glass-canvas) {
  opacity: 0;
  transition: opacity 0.1s ease-out;
}

.drawer-glass--webgl-visible :deep(.liquid-glass-canvas--visible) {
  opacity: 1;
}

.drawer-glass--webgl-visible {
  pointer-events: auto;
}

.drawer-glass--fallback {
  transition:
    border-color 0.25s ease,
    box-shadow 0.25s ease;
}

.drawer-content {
  position: relative;
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 1.25rem;
  overflow: hidden;
}

.drawer-close {
  position: absolute;
  top: 0.85rem;
  right: 0.85rem;
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.08);
  color: var(--text-secondary);
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s ease;
  z-index: 2;
}

.drawer-close:hover {
  background: rgba(255, 255, 255, 0.14);
  color: var(--text-primary);
}

/* 遮罩淡入淡出 */
.drawer-overlay-enter-active,
.drawer-overlay-leave-active {
  transition: opacity 0.25s ease;
}

.drawer-overlay-enter-from,
.drawer-overlay-leave-to {
  opacity: 0;
}

/* 保留原生 Transition 的左右滑入，玻璃 canvas 在动画期间保持隐藏。 */
.drawer-slide-left-enter-active,
.drawer-slide-left-leave-active,
.drawer-slide-right-enter-active,
.drawer-slide-right-leave-active {
  transition: transform 0.3s cubic-bezier(0.22, 1, 0.36, 1);
}

.drawer-slide-left-enter-from,
.drawer-slide-left-leave-to {
  transform: translateX(-100%);
}

.drawer-slide-right-enter-from,
.drawer-slide-right-leave-to {
  transform: translateX(100%);
}
</style>
