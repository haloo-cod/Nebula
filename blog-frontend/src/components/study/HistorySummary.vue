<template>
  <LiquidGlass
    v-if="ui.liquidGlassEnabled"
    class="history-summary"
    :theme="ui.theme"
    :corner-radius="16"
    :blur-radius="ui.liquidGlassBlur"
    :glass-thickness="32"
    :highlight-width="2.5"
    ripple-trail
  >
    <HistorySummaryContent :today="todayRecord" :total-pomodoros="totalPomodoros" :total-minutes="totalMinutes" />
  </LiquidGlass>

  <PanelFallbackGlass v-else tag="div" class="history-summary history-summary--fallback">
    <HistorySummaryContent :today="todayRecord" :total-pomodoros="totalPomodoros" :total-minutes="totalMinutes" />
  </PanelFallbackGlass>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import LiquidGlass from '@/components/liquid-glass/LiquidGlass.vue'
import PanelFallbackGlass from '@/components/panels/PanelFallbackGlass.vue'
import HistorySummaryContent from './HistorySummaryContent.vue'
import { useUIStore } from '@/stores/ui'
import type { StudyHistoryRecord } from '@/types'

const props = defineProps<{
  history: StudyHistoryRecord[]
}>()

const ui = useUIStore()

const todayRecord = computed(() => {
  const today = new Date().toISOString().slice(0, 10)
  return props.history.find((r) => r.date === today)
})

const totalPomodoros = computed(() =>
  props.history.reduce((sum, r) => sum + r.completedPomodoros, 0),
)

const totalMinutes = computed(() =>
  props.history.reduce((sum, r) => sum + r.totalFocusMinutes, 0),
)
</script>

<style scoped>
.history-summary {
  width: 100%;
  border-radius: 1rem;
}

.history-summary--fallback {
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.history-summary--fallback:hover {
  border-color: rgba(140, 185, 255, 0.3);
}
</style>
