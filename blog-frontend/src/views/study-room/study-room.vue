<template>
  <PageBackground>
    <div class="relative flex flex-col items-center justify-start pt-24 md:pt-0 w-full">
      <div class="study-wrapper">
        <GlassPanel class="study-panel">
          <div class="study-header">
            <p class="study-kicker">Study Room</p>
            <h1 class="study-title">自习室</h1>
            <p class="study-desc">静下心来，和一段专注的时光相处。</p>
          </div>

          <!-- 番茄钟 -->
          <div class="pomodoro-section">
            <div class="pomodoro-tabs">
              <button
                v-for="opt in timerPresets"
                :key="opt.label"
                class="pomodoro-tab"
                :class="{ active: selectedPreset === opt.minutes }"
                @click="selectPreset(opt.minutes)"
              >
                {{ opt.label }}
              </button>
            </div>

            <div class="pomodoro-display">
              <span class="pomodoro-time">{{ formattedTime }}</span>
            </div>

            <div class="pomodoro-controls">
              <button class="pomodoro-btn" @click="toggleTimer">
                {{ isRunning ? '暂停' : '开始' }}
              </button>
              <button class="pomodoro-btn pomodoro-btn--ghost" @click="resetTimer">
                重置
              </button>
            </div>

            <p v-if="timerState === 'focus'" class="pomodoro-tip">专注中，别分心。</p>
            <p v-else-if="timerState === 'break'" class="pomodoro-tip">休息一下，起来走走。</p>
            <p v-else class="pomodoro-tip">选择一个时段，点击开始。</p>
          </div>

          <!-- 完成记录 -->
          <div v-if="completedSessions > 0" class="record-section">
            <p class="record-text">
              今日已完成 <span class="record-num">{{ completedSessions }}</span> 个番茄钟
            </p>
          </div>
        </GlassPanel>
      </div>
    </div>
  </PageBackground>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'
import PageBackground from '@/components/PageBackground.vue'
import GlassPanel from '@/components/panels/GlassPanel.vue'

/** 番茄钟预设 */
interface TimerPreset {
  label: string
  minutes: number
}

type TimerState = 'idle' | 'focus' | 'break'

const timerPresets: TimerPreset[] = [
  { label: '25 分钟', minutes: 25 },
  { label: '45 分钟', minutes: 45 },
  { label: '15 分钟', minutes: 15 },
]

const selectedPreset = ref(25)
const remainingSeconds = ref(25 * 60)
const isRunning = ref(false)
const timerState = ref<TimerState>('idle')
const completedSessions = ref(0)
let timerInterval: ReturnType<typeof setInterval> | null = null

const formattedTime = computed(() => {
  const mins = Math.floor(remainingSeconds.value / 60)
  const secs = remainingSeconds.value % 60
  return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
})

function selectPreset(minutes: number) {
  if (isRunning.value) return
  selectedPreset.value = minutes
  remainingSeconds.value = minutes * 60
  timerState.value = 'idle'
}

function toggleTimer() {
  if (isRunning.value) {
    stopTimer()
  } else {
    startTimer()
  }
}

function startTimer() {
  if (timerState.value === 'idle') {
    timerState.value = 'focus'
  }
  isRunning.value = true
  timerInterval = setInterval(() => {
    if (remainingSeconds.value <= 0) {
      handleTimerEnd()
      return
    }
    remainingSeconds.value -= 1
  }, 1000)
}

function stopTimer() {
  isRunning.value = false
  if (timerInterval) {
    clearInterval(timerInterval)
    timerInterval = null
  }
}

function handleTimerEnd() {
  stopTimer()
  if (timerState.value === 'focus') {
    completedSessions.value += 1
    timerState.value = 'break'
    remainingSeconds.value = 5 * 60
  } else {
    timerState.value = 'idle'
    remainingSeconds.value = selectedPreset.value * 60
  }
}

function resetTimer() {
  stopTimer()
  remainingSeconds.value = selectedPreset.value * 60
  timerState.value = 'idle'
}

onUnmounted(() => {
  stopTimer()
})
</script>

<style scoped>
.study-wrapper {
  position: relative;
  z-index: 10;
  width: 100%;
  max-width: 42rem;
  margin: 4rem auto 0;
  padding-left: 1rem;
  padding-right: 1rem;
}

.study-panel {
  min-height: 60vh;
}

.study-header {
  margin-bottom: 2rem;
}

.study-kicker {
  margin-bottom: 0.25rem;
  color: rgba(160, 205, 255, 0.7);
  font-size: 0.72rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.study-title {
  color: rgba(255, 255, 255, 0.92);
  font-size: 1.45rem;
  font-weight: 700;
  letter-spacing: 0.06em;
}

.study-desc {
  margin-top: 0.45rem;
  color: rgba(255, 255, 255, 0.48);
  font-size: 0.86rem;
}

/* 番茄钟 */
.pomodoro-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
}

.pomodoro-tabs {
  display: flex;
  gap: 0.5rem;
}

.pomodoro-tab {
  padding: 0.45rem 1.2rem;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.82rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.pomodoro-tab:hover {
  border-color: rgba(140, 185, 255, 0.35);
  color: rgba(255, 255, 255, 0.85);
}

.pomodoro-tab.active {
  border-color: rgba(140, 185, 255, 0.5);
  background: rgba(100, 150, 255, 0.15);
  color: rgba(180, 210, 255, 1);
}

.pomodoro-display {
  padding: 2rem 0;
}

.pomodoro-time {
  font-size: 4rem;
  font-weight: 200;
  color: rgba(255, 255, 255, 0.92);
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.04em;
}

.pomodoro-controls {
  display: flex;
  gap: 0.75rem;
}

.pomodoro-btn {
  padding: 0.6rem 2rem;
  border-radius: 999px;
  border: 1px solid rgba(140, 185, 255, 0.35);
  background: rgba(100, 150, 255, 0.12);
  color: rgba(180, 210, 255, 0.9);
  font-size: 0.88rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.pomodoro-btn:hover {
  background: rgba(100, 150, 255, 0.22);
  border-color: rgba(140, 185, 255, 0.5);
}

.pomodoro-btn--ghost {
  border-color: rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.04);
  color: rgba(255, 255, 255, 0.5);
}

.pomodoro-btn--ghost:hover {
  border-color: rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.75);
}

.pomodoro-tip {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.35);
  margin: 0;
}

/* 记录 */
.record-section {
  margin-top: 2rem;
  text-align: center;
}

.record-text {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.45);
  margin: 0;
}

.record-num {
  color: rgba(160, 210, 255, 0.8);
  font-weight: 600;
}

@media (min-width: 768px) {
  .study-wrapper {
    margin-top: 100px;
  }
}

@media (max-width: 767px) {
  .study-wrapper {
    margin-top: 6rem;
  }

  .pomodoro-time {
    font-size: 3rem;
  }
}
</style>
