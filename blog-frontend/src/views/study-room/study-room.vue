<template>
  <PageBackground>
    <div class="study-page">
      <!-- 左右抽屉开关 -->
      <button class="drawer-trigger drawer-trigger--left" type="button" aria-label="打开待办清单" @click="leftOpen = true">
        <SvgIcon name="arrow_forward_ios" class="trigger-icon" />
      </button>
      <button class="drawer-trigger drawer-trigger--right" type="button" aria-label="打开今日日程" @click="rightOpen = true">
        <SvgIcon name="arrow_back_ios" class="trigger-icon" />
      </button>

      <!-- 中央番茄钟面板 -->
      <div class="study-wrapper">
        <!-- 页面头部：定位到玻璃面板左上方 -->
        <header class="study-header">
          <span class="study-kicker">Study Room</span>
          <h1 class="study-title">自习室</h1>
          <p class="study-desc">静下心来，和一段专注的时光相处。</p>
        </header>

        <LiquidGlass
          v-if="ui.liquidGlassEnabled"
          class="study-glass"
          :theme="ui.theme"
          :corner-radius="28"
          :blur-radius="ui.liquidGlassBlur"
          :glass-thickness="48"
          :highlight-width="3.5"
          ripple-trail
        >
          <StudyRoomContent
            :mode="mode"
            :active-todo="activeTodo"
            :formatted-time="formattedTime"
            :is-running="isRunning"
            :is-flashing="isFlashing"
            @toggle="toggleTimer"
            @reset="resetTimer"
          />
        </LiquidGlass>

        <PanelFallbackGlass v-else tag="div" class="study-glass study-glass--fallback">
          <StudyRoomContent
            :mode="mode"
            :active-todo="activeTodo"
            :formatted-time="formattedTime"
            :is-running="isRunning"
            :is-flashing="isFlashing"
            @toggle="toggleTimer"
            @reset="resetTimer"
          />
        </PanelFallbackGlass>
      </div>

      <!-- 历史摘要 -->
      <div class="history-wrapper">
        <HistorySummary :history="history" />
      </div>
    </div>

    <!-- 左抽屉：待办 -->
    <StudyDrawer v-model="leftOpen" position="left">
      <TodoPanel
        :todos="todos"
        :active-id="activeTodoId"
        @add="addTodo"
        @select="selectTodo"
        @delete="deleteTodo"
        @toggle="toggleTodo"
      />
    </StudyDrawer>

    <!-- 右抽屉：日程 -->
    <StudyDrawer v-model="rightOpen" position="right">
      <SchedulePanel
        :schedule="schedule"
        @add="addSchedule"
        @delete="deleteSchedule"
        @toggle="toggleSchedule"
      />
    </StudyDrawer>
  </PageBackground>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import PageBackground from '@/components/PageBackground.vue'
import LiquidGlass from '@/components/liquid-glass/LiquidGlass.vue'
import PanelFallbackGlass from '@/components/panels/PanelFallbackGlass.vue'
import SvgIcon from '@/components/SvgIcon.vue'
import StudyDrawer from '@/components/study/StudyDrawer.vue'
import TodoPanel from '@/components/study/TodoPanel.vue'
import SchedulePanel from '@/components/study/SchedulePanel.vue'
import HistorySummary from '@/components/study/HistorySummary.vue'
import StudyRoomContent from './StudyRoomContent.vue'
import { useUIStore } from '@/stores/ui'
import type { StudyTodo, ScheduleItem, StudyHistoryRecord } from '@/types'

const ui = useUIStore()

// localStorage keys
const STORAGE_KEYS = {
  todos: 'starlit-study-todos',
  schedule: 'starlit-study-schedule',
  history: 'starlit-study-history',
  lastDate: 'starlit-study-last-date',
}

// State
const todos = ref<StudyTodo[]>([])
const schedule = ref<ScheduleItem[]>([])
const history = ref<StudyHistoryRecord[]>([])
const activeTodoId = ref<string | null>(null)
const leftOpen = ref(false)
const rightOpen = ref(false)
const mode = ref<'focus' | 'break'>('focus')
const isFlashing = ref(false)
let timerInterval: ReturnType<typeof setInterval> | null = null

// Active todo
const activeTodo = computed(() => todos.value.find((t) => t.id === activeTodoId.value))

// Time display
const displaySeconds = computed(() => {
  if (activeTodo.value) return activeTodo.value.remainingSeconds
  return 25 * 60
})

const formattedTime = computed(() => {
  const total = displaySeconds.value
  const hours = Math.floor(total / 3600)
  const mins = Math.floor((total % 3600) / 60)
  const secs = total % 60
  const parts = [
    String(mins).padStart(2, '0'),
    String(secs).padStart(2, '0'),
  ]
  if (hours > 0) parts.unshift(String(hours).padStart(2, '0'))
  return parts.join(':')
})

const isRunning = computed(() => activeTodo.value?.isRunning ?? false)

// Provide data and methods to child content component
// Utility: generate id
function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
}

/**
 * 获取"逻辑日期"：凌晨 4:00 前算前一天
 * 这样深夜学习不会被意外重置日程和计数
 */
function getLogicalDate(): string {
  const now = new Date()
  if (now.getHours() < 4) {
    now.setDate(now.getDate() - 1)
  }
  return now.toISOString().slice(0, 10)
}

// Load from localStorage
function loadFromStorage() {
  try {
    const storedTodos = localStorage.getItem(STORAGE_KEYS.todos)
    const storedSchedule = localStorage.getItem(STORAGE_KEYS.schedule)
    const storedHistory = localStorage.getItem(STORAGE_KEYS.history)
    const lastDate = localStorage.getItem(STORAGE_KEYS.lastDate)
    const today = getLogicalDate()

    if (storedHistory) history.value = JSON.parse(storedHistory) as StudyHistoryRecord[]

    if (storedTodos) {
      todos.value = JSON.parse(storedTodos) as StudyTodo[]
      // 日期不同 → 新的一天，先结算历史再重置每日计数
      if (lastDate !== today) {
        // 结算：把昨日的 todayCompleted 写入历史（补偿未被 recordFocus 覆盖的情况）
        if (lastDate) {
          const totalPomodoros = todos.value.reduce((sum, t) => sum + t.todayCompleted, 0)
          const totalMinutes = todos.value.reduce((sum, t) => sum + t.todayCompleted * t.durationMinutes, 0)
          if (totalPomodoros > 0) {
            const existing = history.value.find((h) => h.date === lastDate)
            if (!existing) {
              history.value.push({
                date: lastDate,
                completedPomodoros: totalPomodoros,
                totalFocusMinutes: totalMinutes,
              })
            }
          }
        }
        // 重置每日计数
        todos.value = todos.value.map((t) => ({ ...t, todayCompleted: 0, isRunning: false }))
      }
    }

    if (storedSchedule) {
      schedule.value = JSON.parse(storedSchedule) as ScheduleItem[]
      // 新一天，日程完成状态重置
      if (lastDate !== today) {
        schedule.value = schedule.value.map((s) => ({ ...s, isCompleted: false }))
      }
    }

    localStorage.setItem(STORAGE_KEYS.lastDate, today)
  } catch (err) {
    console.warn('[study-room] 读取本地数据失败:', err)
  }
}

// Save to localStorage
function saveToStorage() {
  try {
    localStorage.setItem(STORAGE_KEYS.todos, JSON.stringify(todos.value))
    localStorage.setItem(STORAGE_KEYS.schedule, JSON.stringify(schedule.value))
    localStorage.setItem(STORAGE_KEYS.history, JSON.stringify(history.value))
  } catch (err) {
    console.warn('[study-room] 保存本地数据失败:', err)
  }
}

// Watch and persist
watch([todos, schedule, history], saveToStorage, { deep: true })

// Timer logic
function startTimer() {
  if (!activeTodo.value) return
  stopTimer()
  activeTodo.value.isRunning = true
  timerInterval = setInterval(() => {
    const todo = activeTodo.value
    if (!todo || !todo.isRunning) return

    if (todo.remainingSeconds > 0) {
      todo.remainingSeconds -= 1
      return
    }

    handleTimerEnd()
  }, 1000)
}

function stopTimer() {
  if (activeTodo.value) activeTodo.value.isRunning = false
  if (timerInterval) {
    clearInterval(timerInterval)
    timerInterval = null
  }
}

function toggleTimer() {
  if (isRunning.value) stopTimer()
  else startTimer()
}

function resetTimer() {
  stopTimer()
  if (!activeTodo.value) return
  if (mode.value === 'break') {
    activeTodo.value.remainingSeconds = activeTodo.value.breakMinutes * 60
  } else {
    activeTodo.value.remainingSeconds = activeTodo.value.durationMinutes * 60
  }
  isFlashing.value = false
}

function handleTimerEnd() {
  stopTimer()
  isFlashing.value = true
  const todo = activeTodo.value
  if (!todo) return

  if (mode.value === 'focus') {
    // Update todo stats
    todo.completedPomodoros += 1
    todo.todayCompleted += 1

    // Update history
    recordFocus(todo.durationMinutes)

    // Auto switch to break
    mode.value = 'break'
    todo.remainingSeconds = todo.breakMinutes * 60

    // Start break after a short delay
    window.setTimeout(() => {
      isFlashing.value = false
      startTimer()
    }, 1500)
  } else {
    // Break ends, back to focus
    mode.value = 'focus'
    todo.remainingSeconds = todo.durationMinutes * 60

    window.setTimeout(() => {
      isFlashing.value = false
    }, 1500)
  }
}

function recordFocus(minutes: number) {
  const today = getLogicalDate()
  const record = history.value.find((h) => h.date === today)
  if (record) {
    record.completedPomodoros += 1
    record.totalFocusMinutes += minutes
  } else {
    history.value.push({
      date: today,
      completedPomodoros: 1,
      totalFocusMinutes: minutes,
    })
  }
}

// Todo CRUD
function addTodo(payload: Omit<StudyTodo, 'id' | 'createdAt' | 'completedPomodoros' | 'todayCompleted' | 'isRunning' | 'isCompleted'>) {
  const todo: StudyTodo = {
    ...payload,
    id: generateId(),
    completedPomodoros: 0,
    todayCompleted: 0,
    isRunning: false,
    isCompleted: false,
    createdAt: new Date().toISOString(),
  }
  todos.value.push(todo)
  if (!activeTodoId.value) activeTodoId.value = todo.id
}

function selectTodo(id: string) {
  stopTimer()
  activeTodoId.value = id
  const todo = activeTodo.value
  if (todo) {
    mode.value = 'focus'
    todo.remainingSeconds = todo.durationMinutes * 60
  }
}

function deleteTodo(id: string) {
  todos.value = todos.value.filter((t) => t.id !== id)
  if (activeTodoId.value === id) {
    activeTodoId.value = todos.value[0]?.id ?? null
  }
}

function toggleTodo(id: string) {
  const todo = todos.value.find((t) => t.id === id)
  if (!todo) return
  todo.isCompleted = !todo.isCompleted
  if (todo.isCompleted && activeTodoId.value === id && isRunning.value) {
    stopTimer()
  }
}

// Schedule CRUD
function addSchedule(payload: Omit<ScheduleItem, 'id' | 'createdAt' | 'isCompleted'>) {
  const item: ScheduleItem = {
    ...payload,
    id: generateId(),
    isCompleted: false,
    createdAt: new Date().toISOString(),
  }
  schedule.value.push(item)
}

function deleteSchedule(id: string) {
  schedule.value = schedule.value.filter((s) => s.id !== id)
}

function toggleSchedule(id: string) {
  const item = schedule.value.find((s) => s.id === id)
  if (item) item.isCompleted = !item.isCompleted
}

// Lifecycle
onMounted(() => {
  loadFromStorage()
  if (todos.value.length > 0 && !activeTodoId.value) {
    activeTodoId.value = todos.value[0].id
  }
})

onUnmounted(() => {
  stopTimer()
})
</script>

<style scoped>
@font-face {
  font-family: 'DS-DIGIT';
  src: url('@/assets/front/DS-DIGIT.TTF') format('truetype');
  font-weight: normal;
  font-style: normal;
  font-display: swap;
}

.study-page {
  position: relative;
  z-index: 10;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  min-height: 100vh;
  padding: 6rem 1rem 2rem;
}

.study-header {
  position: absolute;
  top: 0.5rem;
  right: calc(100% + 1.5rem);
  text-align: left;
  white-space: nowrap;
}

.study-kicker {
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: rgba(160, 205, 255, 0.7);
}

.study-title {
  margin: 0.4rem 0 0;
  color: var(--text-primary);
  font-size: clamp(1.7rem, 3vw, 2.6rem);
  font-weight: 700;
  letter-spacing: 0.08em;
}

.study-desc {
  margin: 0.5rem 0 0;
  color: var(--text-secondary);
  font-size: 0.9rem;
  line-height: 1.7;
}

.drawer-trigger {
  position: fixed;
  top: 50%;
  transform: translateY(-50%);
  z-index: 55;
  width: 2.6rem;
  height: 2.6rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(255, 255, 255, 0.62);
  border-radius: 0.6rem;
  background: rgba(255, 255, 255, 0.42);
  backdrop-filter: blur(16px) saturate(1.14);
  -webkit-backdrop-filter: blur(16px) saturate(1.14);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.56),
    0 4px 12px rgba(85, 109, 124, 0.14);
  color: rgba(45, 42, 36, 0.8);
  cursor: pointer;
  transition: all 0.2s ease;
}

.drawer-trigger:hover {
  background: rgba(255, 255, 255, 0.62);
  border-color: rgba(140, 185, 255, 0.7);
}

.drawer-trigger--left {
  left: 1rem;
}

.drawer-trigger--right {
  right: 1rem;
}

.trigger-icon {
  width: 1.15rem;
  height: 1.15rem;
}

.study-wrapper {
  position: relative;
  width: 100%;
  max-width: 42rem;
}

.study-glass {
  width: 100%;
  min-height: 60vh;
  border-radius: 1.5rem;
  overflow: hidden;
}

.study-glass--fallback {
  transition: border-color 0.25s ease, box-shadow 0.25s ease;
}

.history-wrapper {
  width: 100%;
  max-width: 42rem;
  margin-top: 1rem;
}

@media (max-width: 767px) {
  .study-page {
    padding-top: 5rem;
  }

  .study-header {
    position: static;
    margin-bottom: 1.2rem;
    text-align: center;
    white-space: normal;
  }

  .drawer-trigger {
    width: 2.3rem;
    height: 2.3rem;
    border-radius: 0.55rem;
  }

  .drawer-trigger--left {
    left: 0.5rem;
  }

  .drawer-trigger--right {
    right: 0.5rem;
  }
}
</style>
