<template>
  <div class="study-content">
    <!-- 当前任务 -->
    <div class="active-task">
      <span class="active-task-label">当前任务</span>
      <p class="active-task-title">{{ activeTodo?.title ?? '暂无待办' }}</p>
      <span v-if="mode === 'break'" class="active-task-mode">休息中</span>
    </div>

    <!-- 倒计时 -->
    <div class="timer-section">
      <div class="timer-display" :class="{ 'timer-flash': isFlashing }">
        <span class="timer-time">{{ formattedTime }}</span>
      </div>

      <div class="timer-controls">
        <button class="timer-btn" type="button" @click="$emit('toggle')">
          {{ isRunning ? '暂停' : '开始' }}
        </button>
        <button class="timer-btn timer-btn--ghost" type="button" @click="$emit('reset')">
          重置
        </button>
      </div>
    </div>

    <!-- 提示 -->
    <p class="study-tip">
      <template v-if="isFlashing">时间到！</template>
      <template v-else-if="mode === 'break'">休息一下，起来走走。</template>
      <template v-else-if="isRunning">专注中，别分心。</template>
      <template v-else>选择一个待办，点击开始。</template>
    </p>
  </div>
</template>

<script setup lang="ts">
import type { StudyTodo } from '@/types'

const props = defineProps<{
  mode: 'focus' | 'break'
  activeTodo: StudyTodo | undefined
  formattedTime: string
  isRunning: boolean
  isFlashing: boolean
}>()

defineEmits<{
  toggle: []
  reset: []
}>()
</script>

<style scoped>
.study-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 2rem 1.5rem;
  min-height: inherit;
}

.active-task {
  margin-bottom: 1.5rem;
  padding: 0.75rem 1.5rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.14);
  max-width: 90%;
}

.active-task-label {
  display: block;
  color: var(--text-secondary);
  font-size: 0.72rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  margin-bottom: 0.2rem;
}

.active-task-title {
  margin: 0;
  color: var(--text-primary);
  font-size: 1.1rem;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.active-task-mode {
  display: inline-block;
  margin-top: 0.25rem;
  padding: 0.12rem 0.55rem;
  border-radius: 999px;
  background: rgba(255, 200, 100, 0.14);
  color: rgba(255, 220, 140, 0.95);
  font-size: 0.7rem;
}

.timer-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

.timer-display {
  padding: 1.5rem 0;
}

.timer-time {
  font-family: 'DS-DIGIT', 'SFMono-Regular', 'Cascadia Mono', 'Cascadia Code', 'Consolas', monospace;
  font-size: 5rem;
  font-weight: 400;
  color: var(--text-primary);
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.04em;
  line-height: 1;
}

.timer-flash .timer-time {
  color: #ff6b6b;
  animation: flash-red 0.6s ease-in-out infinite alternate;
}

@keyframes flash-red {
  from {
    opacity: 1;
    text-shadow: 0 0 20px rgba(255, 107, 107, 0.5);
  }
  to {
    opacity: 0.5;
    text-shadow: 0 0 40px rgba(255, 107, 107, 0.9);
  }
}

.timer-controls {
  display: flex;
  gap: 0.75rem;
}

.timer-btn {
  padding: 0.65rem 2.2rem;
  border-radius: 999px;
  border: 1px solid rgba(140, 185, 255, 0.35);
  background: rgba(100, 150, 255, 0.12);
  color: rgba(180, 210, 255, 0.9);
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.timer-btn:hover {
  background: rgba(100, 150, 255, 0.22);
  border-color: rgba(140, 185, 255, 0.5);
}

.timer-btn--ghost {
  border-color: rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.04);
  color: rgba(255, 255, 255, 0.5);
}

.timer-btn--ghost:hover {
  border-color: rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.75);
}

.study-tip {
  margin: 0;
  font-size: 0.85rem;
  color: var(--text-secondary);
  min-height: 1.4em;
}

@media (max-width: 767px) {
  .timer-time {
    font-size: 3.6rem;
  }

  .study-content {
    padding: 1.5rem 1rem;
  }
}
</style>
