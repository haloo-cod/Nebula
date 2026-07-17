<template>
  <div class="history-content">
    <div class="history-item">
      <span class="history-value">{{ today?.completedPomodoros ?? 0 }}</span>
      <span class="history-label">今日番茄钟</span>
    </div>
    <div class="history-item">
      <span class="history-value">{{ todayMinutes }}</span>
      <span class="history-label">今日专注(分钟)</span>
    </div>
    <div class="history-item">
      <span class="history-value">{{ totalPomodoros }}</span>
      <span class="history-label">累计番茄钟</span>
    </div>
    <div class="history-item">
      <span class="history-value">{{ totalMinutes }}</span>
      <span class="history-label">累计专注(分钟)</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { StudyHistoryRecord } from '@/types'

const props = defineProps<{
  today?: StudyHistoryRecord
  totalPomodoros: number
  totalMinutes: number
}>()

const todayMinutes = computed(() => props.today?.totalFocusMinutes ?? 0)
</script>

<style scoped>
.history-content {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
  padding: 1rem;
}

.history-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
  padding: 0.6rem;
  border-radius: 0.75rem;
  background: rgba(255, 255, 255, 0.05);
}

.history-value {
  color: var(--text-primary);
  font-size: 1.4rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.history-label {
  color: var(--text-muted);
  font-size: 0.68rem;
  text-align: center;
}
</style>
