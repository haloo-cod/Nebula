<template>
  <div class="todo-panel">
    <h2 class="panel-title">待办清单</h2>
    <p class="panel-desc">每个待办都有独立的专注与休息倒计时。</p>

    <!-- 添加表单 -->
    <form class="todo-form" @submit.prevent="handleAdd">
      <input
        v-model="newTitle"
        class="panel-input"
        type="text"
        placeholder="要做点什么？"
        maxlength="60"
      />
      <div class="todo-form-row">
        <label class="form-field">
          <span>专注</span>
          <input
            v-model.number="newDuration"
            class="panel-number"
            type="number"
            min="1"
            max="180"
          />
          <span>分钟</span>
        </label>
        <label class="form-field">
          <span>休息</span>
          <input v-model.number="newBreak" class="panel-number" type="number" min="1" max="60" />
          <span>分钟</span>
        </label>
      </div>
      <button class="panel-submit" type="submit" :disabled="!newTitle.trim()">添加待办</button>
    </form>

    <!-- 列表 -->
    <div class="todo-list">
      <TodoCard
        v-for="todo in todos"
        :key="todo.id"
        :todo="todo"
        :is-active="todo.id === activeId"
        @select="$emit('select', todo.id)"
        @delete="$emit('delete', todo.id)"
        @toggle="$emit('toggle', todo.id)"
      />
      <div v-if="todos.length === 0" class="panel-empty">还没有待办，添加一个吧。</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import TodoCard from './TodoCard.vue'
import type { StudyTodo } from '@/types'

const props = defineProps<{
  todos: StudyTodo[]
  activeId: string | null
}>()

const emit = defineEmits<{
  add: [
    todo: Omit<
      StudyTodo,
      'id' | 'createdAt' | 'completedPomodoros' | 'todayCompleted' | 'isRunning' | 'isCompleted'
    >,
  ]
  select: [id: string]
  delete: [id: string]
  toggle: [id: string]
}>()

const newTitle = ref('')
const newDuration = ref(25)
const newBreak = ref(5)

function handleAdd() {
  const title = newTitle.value.trim()
  if (!title) return
  emit('add', {
    title,
    durationMinutes: Math.max(1, newDuration.value),
    breakMinutes: Math.max(1, newBreak.value),
    remainingSeconds: Math.max(1, newDuration.value) * 60,
  })
  newTitle.value = ''
  newDuration.value = 25
  newBreak.value = 5
}
</script>

<style scoped>
.todo-panel {
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

.todo-form {
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

.todo-form-row {
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

.panel-number {
  width: 3rem;
  padding: 0.2rem 0.3rem;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 0.4rem;
  background: rgba(255, 255, 255, 0.06);
  color: var(--text-primary);
  font-size: 0.8rem;
  text-align: center;
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

.todo-list {
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

<!-- Light 主题适配：按钮在亮色背景下可读 -->
<style>
[data-theme='light'] .todo-panel .panel-submit {
  background: rgba(50, 100, 220, 0.12);
  border-color: rgba(50, 100, 220, 0.35);
  color: rgba(30, 70, 180, 1);
}

[data-theme='light'] .todo-panel .panel-submit:hover:not(:disabled) {
  background: rgba(50, 100, 220, 0.2);
}
</style>
