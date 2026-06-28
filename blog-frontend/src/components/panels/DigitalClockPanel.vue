<template>
  <div class="clock-panel" :class="`clock-panel--${ui.theme}`" translate="no">
    <div class="clock-main">
      <span class="clock-hour">{{ hour }}</span>
      <span class="clock-colon">:</span>
      <span class="clock-minute">{{ minute }}</span>
      <span class="clock-colon">:</span>
      <span class="clock-second">{{ second }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useUIStore } from '@/stores/ui'

const ui = useUIStore()

const now = ref(new Date())
let timer: ReturnType<typeof setInterval> | null = null

function pad(value: number): string {
  return String(value).padStart(2, '0')
}

const hour = computed(() => pad(now.value.getHours()))
const minute = computed(() => pad(now.value.getMinutes()))
const second = computed(() => pad(now.value.getSeconds()))

onMounted(() => {
  timer = setInterval(() => {
    now.value = new Date()
  }, 1000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
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

.clock-panel {
  width: 100%;
  height: 100%;
  padding: 0.4rem 0.6rem;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
}

.clock-main {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.05em;
  width: 100%;
  height: 100%;
  font-family: 'DS-DIGIT', 'SFMono-Regular', 'Cascadia Mono', 'Cascadia Code', 'Consolas', monospace;
  color: var(--clock-main-color);
  text-shadow:
    0 0 12px rgba(170, 225, 255, 0.22),
    0 0 24px rgba(110, 205, 255, 0.1),
    0 2px 14px rgba(0, 0, 0, 0.2);
}

.clock-hour,
.clock-minute,
.clock-second,
.clock-colon {
  font-size: clamp(2.4rem, 5.5vw, 4.2rem);
  line-height: 1;
  font-weight: 400;
  letter-spacing: 0.02em;
  font-variant-numeric: tabular-nums;
}

.clock-colon {
  color: var(--clock-accent-color);
  transform: translateY(-0.02em);
}

.clock-panel--dark {
  --clock-main-color: rgba(232, 245, 255, 0.98);
  --clock-accent-color: rgba(176, 224, 255, 0.94);
}

.clock-panel--light {
  --clock-main-color: rgba(249, 241, 228, 0.98);
  --clock-accent-color: rgba(237, 223, 202, 0.96);
}
</style>
