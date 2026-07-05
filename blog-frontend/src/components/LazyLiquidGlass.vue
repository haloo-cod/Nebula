<template>
  <div
    ref="rootRef"
    class="lazy-liquid-glass"
    :class="{
      'lazy-liquid-glass--active': shouldRenderLiquidGlass,
      'lazy-liquid-glass--fallback': !shouldRenderLiquidGlass,
    }"
  >
    <LiquidGlass
      v-if="shouldRenderLiquidGlass"
      class="lazy-liquid-glass__effect"
      :corner-radius="cornerRadius"
      :blur-radius="blurRadius"
      :glass-thickness="glassThickness"
      :ior="ior"
      :highlight-width="highlightWidth"
      :overlay-color="overlayColor"
      :allow-reveal="allowReveal"
      :realtime-offset="realtimeOffset"
      :theme="theme"
    >
      <slot />
    </LiquidGlass>
    <div v-else class="lazy-liquid-glass__fallback">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import LiquidGlass from '@/components/LiquidGlass.vue'
import { useUIStore } from '@/stores/ui'

const MAX_ACTIVE_LIQUID_GLASS = 6
const pendingActivations: Array<() => void> = []
let activeLiquidGlassCount = 0

function removePendingActivation(activation: () => void) {
  const index = pendingActivations.indexOf(activation)
  if (index >= 0) pendingActivations.splice(index, 1)
}

function flushPendingActivations() {
  while (activeLiquidGlassCount < MAX_ACTIVE_LIQUID_GLASS && pendingActivations.length > 0) {
    const activate = pendingActivations.shift()
    if (activate) activate()
  }
}

const props = withDefaults(
  defineProps<{
    cornerRadius?: number
    blurRadius?: number
    glassThickness?: number
    ior?: number
    highlightWidth?: number
    overlayColor?: [number, number, number]
    allowReveal?: boolean
    realtimeOffset?: boolean
    theme?: 'light' | 'dark'
    rootMargin?: string
  }>(),
  {
    cornerRadius: 16,
    blurRadius: 0,
    glassThickness: 41,
    ior: 1.1,
    highlightWidth: 3.5,
    overlayColor: (): [number, number, number] => [0.85, 0.9, 1.0],
    allowReveal: true,
    realtimeOffset: false,
    theme: 'dark',
    rootMargin: '360px',
  },
)

const ui = useUIStore()
const rootRef = ref<HTMLElement | null>(null)
const nearViewport = ref(false)
const hasGlassSlot = ref(false)
let observer: IntersectionObserver | null = null

const shouldRenderLiquidGlass = computed(() => ui.liquidGlassEnabled && nearViewport.value && hasGlassSlot.value)

function releaseGlassSlot() {
  if (!hasGlassSlot.value) return
  hasGlassSlot.value = false
  activeLiquidGlassCount = Math.max(0, activeLiquidGlassCount - 1)
  flushPendingActivations()
}

function activateGlassSlot() {
  if (!nearViewport.value || hasGlassSlot.value) return
  activeLiquidGlassCount += 1
  hasGlassSlot.value = true
}

function requestGlassSlot() {
  removePendingActivation(activateGlassSlot)
  if (!ui.liquidGlassEnabled || !nearViewport.value || hasGlassSlot.value) return
  if (activeLiquidGlassCount < MAX_ACTIVE_LIQUID_GLASS) {
    activateGlassSlot()
    return
  }
  pendingActivations.push(activateGlassSlot)
}

function updateViewportState(isNear: boolean) {
  nearViewport.value = isNear
  if (isNear) {
    requestGlassSlot()
    return
  }
  removePendingActivation(activateGlassSlot)
  releaseGlassSlot()
}

watch(
  () => ui.liquidGlassEnabled,
  (enabled) => {
    if (enabled) {
      requestGlassSlot()
      return
    }
    removePendingActivation(activateGlassSlot)
    releaseGlassSlot()
  },
)

onMounted(() => {
  if (!rootRef.value) return
  observer = new IntersectionObserver(
    ([entry]) => {
      updateViewportState(entry.isIntersecting)
    },
    { root: null, rootMargin: props.rootMargin, threshold: 0.01 },
  )
  observer.observe(rootRef.value)
})

onUnmounted(() => {
  observer?.disconnect()
  removePendingActivation(activateGlassSlot)
  releaseGlassSlot()
})
</script>

<style scoped>
.lazy-liquid-glass,
.lazy-liquid-glass__effect,
.lazy-liquid-glass__fallback {
  width: 100%;
  height: 100%;
}

.lazy-liquid-glass {
  display: block;
}

.lazy-liquid-glass__fallback {
  border-radius: inherit;
  overflow: hidden;
}

.lazy-liquid-glass--fallback .lazy-liquid-glass__fallback {
  background: transparent;
}
</style>
