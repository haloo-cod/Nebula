<template>
  <div class="schedule-panel">
    <h2 class="panel-title">今日日程</h2>
    <p class="panel-desc">安排今天的节奏，时间可以留白。</p>

    <!-- 添加表单 -->
    <form class="schedule-form" @submit.prevent="handleAdd">
      <input
        v-model="newTitle"
        class="panel-input"
        type="text"
        placeholder="今天要做什么？"
        maxlength="60"
      />
      <div class="schedule-form-row">
        <label class="form-field">
          <span>开始</span>
          <input v-model="newStart" class="panel-time" type="time" />
        </label>
        <label class="form-field">
          <span>结束</span>
          <input v-model="newEnd" class="panel-time" type="time" />
        </label>
      </div>
      <button class="panel-submit" type="submit" :disabled="!newTitle.trim()">添加日程</button>
    </form>

    <!-- 列表 -->
    <div class="schedule-list">
      <ScheduleCard
        v-for="item in sortedSchedule"
        :key="item.id"
        :item="item"
        @delete="$emit('delete', item.id)"
        @toggle="$emit('toggle', item.id)"
      />
      <div v-if="sortedSchedule.length === 0" class="panel-empty">还没有日程，规划一下今天吧。</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import ScheduleCard from './ScheduleCard.vue'
import type { ScheduleItem } from '@/types'

const props = defineProps<{
  schedule: ScheduleItem[]
}>()

const emit = defineEmits<{
  add: [item: Omit<ScheduleItem, 'id' | 'createdAt' | 'isCompleted'>]
  delete: [id: string]
  toggle: [id: string]
}>()

const newTitle = ref('')
const newStart = ref('')
const newEnd = ref('')

const sortedSchedule = computed(() => {
  return [...props.schedule].sort((a, b) => {
    const timeA = a.startTime || '99:99'
    const timeB = b.startTime || '99:99'
    return timeA.localeCompare(timeB)
  })
})

function handleAdd() {
  const title = newTitle.value.trim()
  if (!title) return
  emit('add', {
    title,
    startTime: newStart.value || undefined,
    endTime: newEnd.value || undefined,
  })
  newTitle.value = ''
  newStart.value = ''
  newEnd.value = ''
}
</script>

<style scoped>
.schedule-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-width: 0;
  overflow-y: auto;
}

.panel-title {
  margin: 0 0 0.25rem;
  color: var(--text-primary);
  font-size: 1.15rem;
  font-weight: 700;
}

.panel-desc {
  margin: 0 0 1rem;
  color: var(--text-secondary);
  font-size: 0.78rem;
  line-height: 1.5;
}

.schedule-form {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  margin-bottom: 1rem;
  flex-shrink: 0;
}

.panel-input {
  width: 100%;
  padding: 0.55rem 0.8rem;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 0.75rem;
  background: rgba(255, 255, 255, 0.06);
  color: var(--text-primary);
  font-size: 0.85rem;
  outline: none;
  transition: border-color 0.2s ease;
}

.panel-input:focus {
  border-color: rgba(140, 185, 255, 0.45);
}

.panel-input::placeholder {
  color: var(--text-muted);
}

.schedule-form-row {
  display: flex;
  gap: 0.6rem;
}

.form-field {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.45rem 0.6rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 0.65rem;
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-secondary);
  font-size: 0.75rem;
}

.panel-time {
  flex: 1;
  padding: 0.2rem 0.3rem;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 0.4rem;
  background: rgba(255, 255, 255, 0.06);
  color: var(--text-primary);
  font-size: 0.78rem;
}

.panel-submit {
  padding: 0.55rem 1rem;
  border: 1px solid rgba(140, 185, 255, 0.35);
  border-radius: 0.75rem;
  background: rgba(100, 150, 255, 0.15);
  color: rgba(180, 210, 255, 0.95);
  font-size: 0.82rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.panel-submit:hover:not(:disabled) {
  background: rgba(100, 150, 255, 0.25);
}

.panel-submit:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.schedule-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
  padding-right: 0.25rem;
}

.panel-empty {
  text-align: center;
  padding: 2rem 0;
  color: var(--text-muted);
  font-size: 0.8rem;
}
</style>
