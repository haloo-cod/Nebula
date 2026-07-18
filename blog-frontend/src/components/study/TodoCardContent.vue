<template>
  <div class="todo-card-content">
    <div class="todo-main">
      <button
        class="todo-check"
        type="button"
        :aria-label="todo.isCompleted ? '标记未完成' : '标记完成'"
        @click.stop="$emit('toggle', todo.id)"
      >
        <span v-if="todo.isCompleted">✓</span>
      </button>

      <div class="todo-info">
        <h4 class="todo-title" :class="{ 'todo-title--completed': todo.isCompleted }">
          {{ todo.title }}
        </h4>
        <div class="todo-meta">
          <span class="todo-time">专注 {{ todo.durationMinutes }} 分钟</span>
          <span class="todo-break">休息 {{ todo.breakMinutes }} 分钟</span>
          <span v-if="todo.todayCompleted > 0" class="todo-today">今日 {{ todo.todayCompleted }} 个</span>
          <span v-else-if="todo.completedPomodoros > 0" class="todo-total">累计 {{ todo.completedPomodoros }} 个</span>
        </div>
      </div>
    </div>

    <div class="todo-actions">
      <button
        class="todo-delete"
        type="button"
        aria-label="删除"
        @click.stop="$emit('delete', todo.id)"
      >
        🗑
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { StudyTodo } from '@/types'

defineProps<{
  todo: StudyTodo
}>()

defineEmits<{
  delete: [id: string]
  toggle: [id: string]
}>()
</script>

<style scoped>
.todo-card-content {
  display: flex;
  align-items: stretch;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  min-width: 0;
  height: 100%;
}

.todo-main {
  display: flex;
  gap: 0.75rem;
  min-width: 0;
  flex: 1;
}

.todo-check {
  flex-shrink: 0;
  width: 1.4rem;
  height: 1.4rem;
  margin-top: 0.15rem;
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

.todo-check:hover {
  background: rgba(255, 255, 255, 0.14);
  border-color: rgba(140, 185, 255, 0.45);
}

.todo-info {
  min-width: 0;
  flex: 1;
}

.todo-title {
  margin: 0;
  color: var(--text-primary);
  font-size: 1rem;
  font-weight: 600;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.todo-title--completed {
  text-decoration: line-through;
  color: var(--text-muted);
}

.todo-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  margin-top: 0.55rem;
}

.todo-time,
.todo-break,
.todo-today,
.todo-total {
  padding: 0.18rem 0.55rem;
  border-radius: 999px;
  font-size: 0.75rem;
  white-space: nowrap;
}

.todo-time {
  background: rgba(140, 185, 255, 0.22);
  color: rgba(220, 235, 255, 1);
}

.todo-break {
  background: rgba(255, 200, 100, 0.2);
  color: rgba(255, 230, 160, 1);
}

.todo-today {
  background: rgba(110, 230, 170, 0.12);
  color: rgba(150, 245, 200, 0.9);
}

.todo-total {
  background: rgba(255, 255, 255, 0.08);
  color: var(--text-muted);
}

.todo-actions {
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
}

.todo-delete {
  width: 1.6rem;
  height: 1.6rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.08);
  color: var(--text-muted);
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.todo-delete:hover {
  background: rgba(255, 100, 100, 0.15);
  color: rgba(255, 140, 140, 0.9);
}
</style>

<!-- Light 主题适配：meta 标签在亮色背景下可读（非 scoped，需祖先选择器穿透到 html） -->
<style>
[data-theme='light'] .todo-card-content .todo-time {
  background: rgba(60, 120, 220, 0.12);
  color: rgba(40, 80, 160, 1);
}

[data-theme='light'] .todo-card-content .todo-break {
  background: rgba(200, 140, 30, 0.12);
  color: rgba(160, 100, 20, 1);
}

[data-theme='light'] .todo-card-content .todo-today {
  background: rgba(30, 160, 100, 0.12);
  color: rgba(20, 120, 70, 1);
}

[data-theme='light'] .todo-card-content .todo-total {
  background: rgba(0, 0, 0, 0.06);
  color: rgba(80, 80, 80, 1);
}
</style>
