<template>
  <LiquidGlass
    v-if="ui.liquidGlassEnabled"
    class="schedule-card"
    :class="{ 'schedule-card--completed': item.isCompleted }"
    :theme="ui.theme"
    :corner-radius="14"
    :blur-radius="ui.liquidGlassBlur"
    :glass-thickness="30"
    :highlight-width="2.5"
    ripple-trail
  >
    <ScheduleCardContent
      :item="item"
      @delete="$emit('delete', item.id)"
      @toggle="$emit('toggle', item.id)"
    />
  </LiquidGlass>

  <PanelFallbackGlass
    v-else
    tag="div"
    class="schedule-card schedule-card--fallback"
    :class="{ 'schedule-card--completed': item.isCompleted }"
  >
    <ScheduleCardContent
      :item="item"
      @delete="$emit('delete', item.id)"
      @toggle="$emit('toggle', item.id)"
    />
  </PanelFallbackGlass>
</template>

<script setup lang="ts">
import LiquidGlass from '@/components/liquid-glass/LiquidGlass.vue'
import PanelFallbackGlass from '@/components/panels/PanelFallbackGlass.vue'
import ScheduleCardContent from './ScheduleCardContent.vue'
import { useUIStore } from '@/stores/ui'
import type { ScheduleItem } from '@/types'

const ui = useUIStore()

defineProps<{
  item: ScheduleItem
}>()

defineEmits<{
  delete: [id: string]
  toggle: [id: string]
}>()
</script>

<style scoped>
.schedule-card {
  position: relative;
  width: 100%;
  height: 4.5rem;
  min-height: 4.5rem;
  flex-shrink: 0;
  border-radius: 0.9rem;
  transition:
    transform 0.2s ease,
    filter 0.2s ease;
}

.schedule-card:hover {
  transform: translateY(-2px);
}

.schedule-card--completed {
  opacity: 0.55;
}

.schedule-card--fallback {
  height: 4.5rem !important;
  min-height: 4.5rem !important;
  flex: none !important;
  background: rgba(255, 255, 255, 0.08) !important;
  backdrop-filter: blur(12px) !important;
  -webkit-backdrop-filter: blur(12px) !important;
  border: 1px solid rgba(255, 255, 255, 0.15) !important;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.12),
    0 4px 12px rgba(0, 0, 0, 0.12) !important;
  transition:
    transform 0.2s ease,
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.schedule-card--fallback:hover {
  border-color: rgba(140, 185, 255, 0.3) !important;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.18),
    0 8px 24px rgba(80, 120, 200, 0.12) !important;
}
</style>
