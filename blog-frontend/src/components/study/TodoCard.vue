<template>
  <div class="todo-card-wrapper">
    <!-- 右上角 badge：进行中 与 累计 互斥，只显示一个 -->
    <span v-if="isActive" class="todo-active-badge">进行中</span>
    <span v-else-if="todo.completedPomodoros > 0 && todo.todayCompleted === 0" class="todo-total-badge">
      累计 {{ todo.completedPomodoros }} 个
    </span>

    <LiquidGlass
      v-if="ui.liquidGlassEnabled"
      class="todo-card"
      :class="{ 'todo-card--active': isActive, 'todo-card--completed': todo.isCompleted }"
      :theme="ui.theme"
      :corner-radius="16"
      :blur-radius="ui.liquidGlassBlur"
      :glass-thickness="34"
      :highlight-width="2.5"
      ripple-trail
      @click="$emit('select', todo.id)"
    >
      <TodoCardContent :todo="todo" @delete="$emit('delete', todo.id)" @toggle="$emit('toggle', todo.id)" />
    </LiquidGlass>

    <PanelFallbackGlass
      v-else
      tag="div"
      class="todo-card todo-card--fallback"
      :class="{ 'todo-card--active': isActive, 'todo-card--completed': todo.isCompleted }"
      @click="$emit('select', todo.id)"
    >
      <TodoCardContent :todo="todo" @delete="$emit('delete', todo.id)" @toggle="$emit('toggle', todo.id)" />
    </PanelFallbackGlass>
  </div>
</template>

<script setup lang="ts">
import LiquidGlass from '@/components/liquid-glass/LiquidGlass.vue'
import PanelFallbackGlass from '@/components/panels/PanelFallbackGlass.vue'
import TodoCardContent from './TodoCardContent.vue'
import { useUIStore } from '@/stores/ui'
import type { StudyTodo } from '@/types'

const ui = useUIStore()

defineProps<{
  todo: StudyTodo
  isActive: boolean
}>()

defineEmits<{
  select: [id: string]
  delete: [id: string]
  toggle: [id: string]
}>()
</script>

<style scoped>
.todo-card-wrapper {
  position: relative;
  width: 100%;
  height: 5.5rem;
  flex-shrink: 0;
}

.todo-active-badge {
  position: absolute;
  top: 0.55rem;
  right: 0.85rem;
  z-index: 2;
  padding: 0.18rem 0.5rem;
  border-radius: 999px;
  background: rgba(140, 185, 255, 0.18);
  border: 1px solid rgba(140, 185, 255, 0.35);
  color: rgba(180, 210, 255, 0.95);
  font-size: 0.65rem;
  font-weight: 600;
  pointer-events: none;
}

.todo-total-badge {
  position: absolute;
  top: 0.55rem;
  right: 0.85rem;
  z-index: 2;
  padding: 0.18rem 0.5rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: var(--text-muted);
  font-size: 0.65rem;
  font-weight: 600;
  pointer-events: none;
}

.todo-card {
  position: relative;
  width: 100%;
  height: 100%;
  border-radius: 1rem;
  cursor: pointer;
  transition:
    transform 0.2s ease,
    filter 0.2s ease;
}

.todo-card:hover {
  transform: translateY(-2px);
}

.todo-card--active {
  border: 1px solid rgba(140, 185, 255, 0.45);
}

.todo-card--completed {
  opacity: 0.55;
}

.todo-card--fallback {
  height: 100% !important;
  min-height: 0 !important;
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

.todo-card--fallback:hover {
  border-color: rgba(140, 185, 255, 0.35) !important;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.2),
    0 8px 24px rgba(80, 120, 200, 0.15) !important;
}
</style>
