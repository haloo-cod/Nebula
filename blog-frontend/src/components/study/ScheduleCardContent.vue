<template>
  <div class="schedule-card-content">
    <div class="schedule-main">
      <button
        class="schedule-check"
        type="button"
        :aria-label="item.isCompleted ? '标记未完成' : '标记完成'"
        @click.stop="$emit('toggle', item.id)"
      >
        <span v-if="item.isCompleted">✓</span>
      </button>

      <div class="schedule-info">
        <h4 class="schedule-title" :class="{ 'schedule-title--completed': item.isCompleted }">
          {{ item.title }}
        </h4>
        <p v-if="item.startTime || item.endTime" class="schedule-time">
          {{ formatTimeRange(item.startTime, item.endTime) }}
        </p>
      </div>
    </div>

    <button
      class="schedule-delete"
      type="button"
      aria-label="删除"
      @click.stop="$emit('delete', item.id)"
    >
      🗑
    </button>
  </div>
</template>

<script setup lang="ts">
import type { ScheduleItem } from '@/types'

defineProps<{
  item: ScheduleItem
}>()

defineEmits<{
  delete: [id: string]
  toggle: [id: string]
}>()

function formatTimeRange(start?: string, end?: string): string {
  if (start && end) return `${start} – ${end}`
  if (start) return `${start} 开始`
  if (end) return `至 ${end}`
  return ''
}
</script>

<style scoped>
.schedule-card-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  min-width: 0;
  height: 100%;
}

.schedule-main {
  display: flex;
  gap: 0.75rem;
  min-width: 0;
  flex: 1;
  align-items: center;
}

.schedule-check {
  flex-shrink: 0;
  width: 1.4rem;
  height: 1.4rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(255, 255, 255, 0.25);
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.06);
  color: var(--text-primary);
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.schedule-check:hover {
  background: rgba(255, 255, 255, 0.14);
  border-color: rgba(140, 185, 255, 0.45);
}

.schedule-info {
  min-width: 0;
  flex: 1;
}

.schedule-title {
  margin: 0;
  color: var(--text-primary);
  font-size: 0.9rem;
  font-weight: 600;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.schedule-title--completed {
  text-decoration: line-through;
  color: var(--text-muted);
}

.schedule-time {
  margin: 0.2rem 0 0;
  color: var(--text-secondary);
  font-size: 0.72rem;
}

.schedule-delete {
  width: 1.6rem;
  height: 1.6rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 50%;
  background: transparent;
  color: var(--text-muted);
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.schedule-delete:hover {
  background: rgba(255, 100, 100, 0.15);
  color: rgba(255, 140, 140, 0.9);
}
</style>
