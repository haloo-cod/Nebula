<script setup lang="ts">
import { computed, watch } from 'vue'
import { useUIStore } from '@/stores/ui'
import LiquidGlass from '@/components/liquid-glass/LiquidGlass.vue'
import PanelFallbackGlass from '@/components/panels/PanelFallbackGlass.vue'
import { useBackgroundCreditLayout } from '@/composables/useBackgroundCreditLayout'
import { useHangingSign } from '@/composables/useHangingSign'
import { isBackgroundSourceUrl } from '@/utils/backgroundSource'

const ui = useUIStore()
const text = computed(() => ui.currentBackground.sourceText?.trim() ?? '')
const url = computed(() => {
  const value = ui.currentBackground.sourceUrl?.trim() ?? ''
  return isBackgroundSourceUrl(value) ? value : ''
})
const enabled = computed(() => Boolean(text.value && ui.currentBackground.src && !ui.isMobile))
const { layout, pageVisible } = useBackgroundCreditLayout(enabled)
const active = computed(() => enabled.value && layout.value.visible && pageVisible.value)
const limit = computed(() => layout.value.maxAngle)
const anchor = computed(() => ({ x: layout.value.anchorX, y: layout.value.anchorY }))
const {
  angle,
  cardAngle,
  rope,
  dragging,
  onPointerDown,
  onPointerMove,
  onPointerUp,
  onClick,
  reset,
} = useHangingSign(active, limit, anchor)
const style = computed(() => ({
  left: `${layout.value.anchorX}px`,
  top: `${layout.value.anchorY}px`,
  '--credit-width': `${layout.value.width}px`,
  '--credit-height': `${layout.value.height}px`,
  '--credit-angle': `${angle.value}rad`,
  '--credit-card-angle': `${cardAngle.value}rad`,
  '--credit-card-x': `${rope.value.end.x}px`,
  '--credit-card-y': `${rope.value.end.y}px`,
}))

watch(() => ui.currentBackground.id ?? ui.currentBackground.src, reset)
</script>

<template>
  <aside
    v-if="active"
    class="background-credit"
    :class="{ 'background-credit--light': ui.theme === 'light' }"
    :style="style"
    aria-label="背景来源"
  >
    <div class="background-credit-anchor" aria-hidden="true"></div>
    <div class="background-credit-swing" :class="{ 'is-dragging': dragging }">
      <svg class="background-credit-rope" viewBox="-80 -5 160 116" aria-hidden="true">
        <path :d="rope.core" class="credit-rope-core" />
        <path :d="rope.core" class="credit-rope-highlight" />
      </svg>
      <component
        :is="url ? 'a' : 'div'"
        class="background-credit-card"
        :href="url || undefined"
        :target="url ? '_blank' : undefined"
        :rel="url ? 'noopener noreferrer' : undefined"
        :title="text"
        :aria-label="url ? `背景来源：${text}，在新标签页打开` : `背景来源：${text}`"
        draggable="false"
        @dragstart.prevent
        @pointerdown="onPointerDown"
        @pointermove="onPointerMove"
        @pointerup="onPointerUp"
        @pointercancel="onPointerUp"
        @lostpointercapture="onPointerUp"
        @click="onClick"
      >
        <component
          :is="ui.liquidGlassEnabled ? LiquidGlass : PanelFallbackGlass"
          class="background-credit-surface"
          :theme="ui.theme"
          :corner-radius="20"
          :blur-radius="ui.liquidGlassBlur"
          :sample-rotation="cardAngle"
          :realtime-offset="true"
        >
          <div class="background-credit-copy">
            <span class="background-credit-heading">背景来源</span>
            <span class="background-credit-text" translate="no">{{ text }}</span>
            <span class="background-credit-footer" aria-hidden="true">
              <span>{{ url ? '查看来源' : '致谢创作者' }}</span>
              <svg
                v-if="url"
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.6"
              >
                <path
                  d="M14 3h7v7M21 3l-11 11M10 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-5"
                />
              </svg>
            </span>
          </div>
        </component>
      </component>
    </div>
  </aside>
</template>

<style scoped src="@/assets/styles/background-credit.css"></style>
