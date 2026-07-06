<template>
  <GlassPanel :flat="flat" class="calendar-panel" :class="calendarThemeClass" v-if="!flat">
    <!-- 头部：年月 + 切换 -->
    <div class="cal-header">
      <button class="cal-nav" @click="prevMonth" aria-label="上个月">
        <SvgIcon name="arrow_back_ios" />
      </button>
      <div class="cal-title">
        <span class="cal-ym">{{ viewYear }}年{{ viewMonth }}月</span>
        <button class="cal-today-btn" v-if="!isCurrentMonth" @click="goToday">回今天</button>
      </div>
      <button class="cal-nav" @click="nextMonth" aria-label="下个月">
        <SvgIcon name="arrow_forward_ios" />
      </button>
    </div>

    <!-- 星期表头 -->
    <div class="cal-grid cal-weekdays">
      <span
        v-for="(w, i) in weekLabels"
        :key="w"
        class="cal-weekday glass-subtle"
        :class="{ 'is-weekend': i === 0 || i === 6 }"
        >{{ w }}</span
      >
    </div>

    <!-- 日期格子 -->
    <div class="cal-grid cal-days">
      <div
        v-for="(cell, idx) in cells"
        :key="idx"
        class="cal-cell"
        :class="{
          'is-empty': !cell,
          'is-today': cell && cell.isToday,
          'is-weekend': cell && cell.isWeekend,
          'is-off': cell && cell.holiday && cell.holiday.isOff,
          'is-work': cell && cell.holiday && cell.holiday.isWork,
        }"
        :title="cell ? cellTitle(cell) : ''"
      >
        <template v-if="cell">
          <span class="cal-num">{{ cell.day }}</span>
          <span class="cal-sub" v-if="cell.label">{{ cell.label }}</span>
          <span class="cal-tag" v-if="cell.holiday && cell.holiday.isOff">休</span>
          <span class="cal-tag cal-tag-work" v-else-if="cell.holiday && cell.holiday.isWork"
            >班</span
          >
        </template>
      </div>
    </div>
  </GlassPanel>
  <template v-else>
    <div class="cal-content-flat" :class="calendarThemeClass">
      <!-- 头部：年月 + 切换 -->
      <div class="cal-header">
        <button class="cal-nav" @click="prevMonth" aria-label="上个月">
          <SvgIcon name="arrow_back_ios" />
        </button>
        <div class="cal-title">
          <span class="cal-ym">{{ viewYear }}年{{ viewMonth }}月</span>
          <button class="cal-today-btn" v-if="!isCurrentMonth" @click="goToday">回今天</button>
        </div>
        <button class="cal-nav" @click="nextMonth" aria-label="下个月">
          <SvgIcon name="arrow_forward_ios" />
        </button>
      </div>

      <!-- 星期表头 -->
      <div class="cal-grid cal-weekdays">
        <span
          v-for="(w, i) in weekLabels"
          :key="w"
          class="cal-weekday glass-subtle"
          :class="{ 'is-weekend': i === 0 || i === 6 }"
          >{{ w }}</span
        >
      </div>

      <!-- 日期格子 -->
      <div class="cal-grid cal-days">
        <div
          v-for="(cell, idx) in cells"
          :key="idx"
          class="cal-cell"
          :class="{
            'is-empty': !cell,
            'is-today': cell && cell.isToday,
            'is-weekend': cell && cell.isWeekend,
            'is-off': cell && cell.holiday && cell.holiday.isOff,
            'is-work': cell && cell.holiday && cell.holiday.isWork,
          }"
          :title="cell ? cellTitle(cell) : ''"
        >
          <template v-if="cell">
            <span class="cal-num">{{ cell.day }}</span>
            <span class="cal-sub" v-if="cell.label">{{ cell.label }}</span>
            <span class="cal-tag" v-if="cell.holiday && cell.holiday.isOff">休</span>
            <span class="cal-tag cal-tag-work" v-else-if="cell.holiday && cell.holiday.isWork"
              >班</span
            >
          </template>
        </div>
      </div>
    </div>
  </template>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import GlassPanel from './GlassPanel.vue'
import SvgIcon from '@/components/SvgIcon.vue'
import { getSolarTerms, getHolidays, pickMonthHolidays } from '@/data/calendar'
import { useUIStore } from '@/stores/ui'
import type { HolidayDay } from '@/types'

withDefaults(defineProps<{ flat?: boolean }>(), {
  flat: false,
})

const ui = useUIStore()

/** 单个日期格子的数据(null 表示月初的占位空格) */
interface DayCell {
  day: number // 日期数字
  isToday: boolean // 是否今天
  isWeekend: boolean // 是否周末
  holiday: HolidayDay | null // 节假日信息(无则为 null)
  label: string // 副标题(节气优先,其次节假日名)
  term: string | undefined // 当天节气名
}

const weekLabels = ['日', '一', '二', '三', '四', '五', '六']

const now = new Date()
const todayKey = `${now.getFullYear()}-${now.getMonth() + 1}-${now.getDate()}`

const viewYear = ref(now.getFullYear())
const viewMonth = ref(now.getMonth() + 1) // 1-12

const solarTerms = ref<Record<number, string>>({}) // { day: '节气' }
const holidays = ref<Record<number, HolidayDay>>({}) // { day: { name, isOff, isWork } }

const isCurrentMonth = computed(
  () => viewYear.value === now.getFullYear() && viewMonth.value === now.getMonth() + 1,
)

const calendarThemeClass = computed(() => `calendar-panel--${ui.theme}`)

const cells = computed<(DayCell | null)[]>(() => {
  const year = viewYear.value
  const month = viewMonth.value
  const firstWeekday = new Date(year, month - 1, 1).getDay() // 0=周日
  const daysInMonth = new Date(year, month, 0).getDate()
  const list: (DayCell | null)[] = []
  for (let i = 0; i < firstWeekday; i++) list.push(null)
  for (let day = 1; day <= daysInMonth; day++) {
    const weekday = new Date(year, month - 1, day).getDay()
    const holiday = holidays.value[day] || null
    // 副标题优先级：节气 > 节假日名
    const term = solarTerms.value[day]
    const label = term || (holiday ? holiday.name : '')
    list.push({
      day,
      isToday: `${year}-${month}-${day}` === todayKey,
      isWeekend: weekday === 0 || weekday === 6,
      holiday,
      label,
      term,
    })
  }
  return list
})

function cellTitle(cell: DayCell): string {
  const parts: string[] = []
  if (cell.term) parts.push(`节气：${cell.term}`)
  if (cell.holiday)
    parts.push(cell.holiday.isOff ? `放假：${cell.holiday.name}` : `补班：${cell.holiday.name}`)
  return parts.join('  ')
}

function prevMonth() {
  if (viewMonth.value === 1) {
    viewMonth.value = 12
    viewYear.value -= 1
  } else {
    viewMonth.value -= 1
  }
}

function nextMonth() {
  if (viewMonth.value === 12) {
    viewMonth.value = 1
    viewYear.value += 1
  } else {
    viewMonth.value += 1
  }
}

function goToday() {
  viewYear.value = now.getFullYear()
  viewMonth.value = now.getMonth() + 1
}

async function loadMonth() {
  // 节气：本地同步计算
  solarTerms.value = getSolarTerms(viewYear.value, viewMonth.value)
  // 节假日：在线 API（按年缓存），失败降级为空
  const yearData = await getHolidays(viewYear.value)
  // 防止快速切换时的竞态：再次确认年份未变
  holidays.value = pickMonthHolidays(yearData, viewMonth.value)
}

watch([viewYear, viewMonth], loadMonth)
onMounted(loadMonth)
</script>

<style scoped>
.calendar-panel {
  min-height: 0;
}

/* flat 模式下（包在 LiquidGlass 里），内容需要内边距 */
.cal-content-flat {
  position: relative;
  overflow: hidden;
  padding: 0.6rem;
  height: 100%;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  min-height: 0;
  border-radius: 0.85rem;
  color: var(--cal-text);
}

.cal-content-flat::before {
  content: '';
  position: absolute;
  inset: 0;
  z-index: 0;
  border-radius: inherit;
  background: var(--cal-readability-bg);
  backdrop-filter: blur(4px) saturate(1.04) brightness(var(--cal-backdrop-brightness));
  -webkit-backdrop-filter: blur(4px) saturate(1.04) brightness(var(--cal-backdrop-brightness));
  pointer-events: none;
}

.cal-content-flat > * {
  position: relative;
  z-index: 1;
}

.calendar-panel,
.cal-content-flat {
  --cal-text: rgba(240, 246, 255, 0.94);
  --cal-muted: rgba(226, 236, 255, 0.72);
  --cal-weekend: rgba(255, 172, 184, 0.92);
  --cal-sub: rgba(152, 220, 255, 0.9);
  --cal-readability-bg: rgba(10, 16, 34, 0.14);
  --cal-backdrop-brightness: 0.94;
  --cal-weekday-bg: rgba(255, 255, 255, 0.045);
  --cal-weekday-border: rgba(255, 255, 255, 0.06);
  --cal-nav-bg: rgba(255, 255, 255, 0.08);
  --cal-nav-hover-bg: rgba(255, 255, 255, 0.16);
  --cal-nav-border: rgba(255, 255, 255, 0.14);
  --cal-today-bg: rgba(120, 170, 255, 0.24);
  --cal-today-ring: rgba(150, 205, 255, 0.56);
  --cal-shadow: 0 1px 2px rgba(0, 0, 0, 0.28);
}

.calendar-panel--light {
  --cal-text: rgba(35, 43, 62, 0.88);
  --cal-muted: rgba(54, 65, 86, 0.68);
  --cal-weekend: rgba(145, 64, 83, 0.82);
  --cal-sub: rgba(24, 93, 128, 0.86);
  --cal-readability-bg: rgba(255, 255, 255, 0.16);
  --cal-backdrop-brightness: 1;
  --cal-weekday-bg: rgba(255, 255, 255, 0.16);
  --cal-weekday-border: rgba(44, 62, 96, 0.08);
  --cal-nav-bg: rgba(255, 255, 255, 0.24);
  --cal-nav-hover-bg: rgba(255, 255, 255, 0.42);
  --cal-nav-border: rgba(44, 62, 96, 0.1);
  --cal-today-bg: rgba(238, 111, 103, 0.36);
  --cal-today-ring: rgba(255, 239, 226, 0.58);
  --cal-shadow: 0 1px 1px rgba(255, 255, 255, 0.28);
}

.calendar-panel--dark {
  --cal-readability-bg: rgba(10, 16, 34, 0.18);
  --cal-backdrop-brightness: 0.9;
}

/* 头部 */
.cal-header {
  display: grid;
  grid-template-columns: 2.5rem minmax(0, 1fr) 2.5rem;
  align-items: center;
  gap: 0.5rem;
  margin: 0 0.2rem 0.5rem;
}

.cal-title {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.15rem;
  min-width: 0;
}

.cal-ym {
  font-size: 1.16rem;
  font-weight: 700;
  color: var(--cal-text);
  letter-spacing: 0.01em;
  text-shadow: var(--cal-shadow);
}

.cal-today-btn {
  font-size: 0.72rem;
  color: var(--cal-muted);
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 0.35rem;
  padding: 0.08rem 0.42rem;
  cursor: pointer;
  transition:
    color 0.2s ease,
    background 0.2s ease;
}

.cal-today-btn:hover {
  color: var(--cal-text);
  background: rgba(255, 255, 255, 0.2);
}

.cal-nav {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.35rem;
  height: 2.35rem;
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-color: var(--cal-nav-border);
  border-radius: 0.78rem;
  background: var(--cal-nav-bg);
  color: var(--cal-muted);
  cursor: pointer;
  padding: 0;
  transition:
    color 0.2s ease,
    background 0.2s ease,
    border-color 0.2s ease,
    transform 0.2s ease;
}

.cal-nav :deep(.svg-icon) {
  width: 1.25rem;
  height: 1.25rem;
}

.cal-nav:first-child :deep(.svg-icon) {
  transform: translateX(2px);
}

.cal-nav:hover {
  color: var(--cal-text);
  border-color: rgba(180, 215, 255, 0.3);
  background: var(--cal-nav-hover-bg);
  transform: translateY(-1px);
}

/* 网格 */
.cal-grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 0.1rem;
}

.cal-days {
  flex: 1 1 auto;
  grid-auto-rows: minmax(36px, 1fr);
  min-height: 0;
}

/* 关键：grid 子项默认 min-width:auto，长文本（如"劳动节"）会撑破列宽导致溢出 */
.cal-grid > * {
  min-width: 0;
}

.cal-weekdays {
  flex: 0 0 auto;
  margin-bottom: 0.18rem;
}

.cal-weekday {
  text-align: center;
  font-size: 0.86rem;
  font-weight: 700;
  color: var(--cal-muted);
  padding: 0 0.1rem;
  height: 34px;
  width: 100%;
  border: 1px solid var(--cal-weekday-border);
  border-radius: 0.42rem;
  background: var(--cal-weekday-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 0;
}

.cal-weekday.is-weekend {
  color: var(--cal-weekend);
}

/* 日期格子 */
.cal-cell {
  position: relative;
  min-height: 36px;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 0.3rem;
  transition: background 0.2s ease;
  min-width: 0;
  overflow: visible;
  padding: 0 1px;
}

.cal-cell:not(.is-empty):hover {
  background: rgba(255, 255, 255, 0.11);
}

.cal-cell.is-empty {
  pointer-events: none;
}

.cal-num {
  font-size: 1.03rem;
  font-weight: 700;
  line-height: 1;
  color: var(--cal-text);
  text-shadow: var(--cal-shadow);
}

.cal-cell.is-weekend .cal-num {
  color: var(--cal-weekend);
}

.cal-sub {
  font-size: 0.68rem;
  font-weight: 700;
  line-height: 1.1;
  margin-top: 0.05rem;
  color: var(--cal-sub);
  text-shadow: var(--cal-shadow);
  width: 100%;
  box-sizing: border-box;
  padding: 0 1px;
  text-align: center;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 今天 */
.cal-cell.is-today {
  background: var(--cal-today-bg);
  box-shadow:
    inset 0 0 0 1px var(--cal-today-ring),
    0 0 12px rgba(255, 126, 102, 0.16);
}

.cal-cell.is-today .cal-num {
  color: #fff;
  font-weight: 800;
}

/* 放假/补班角标 */
.cal-tag {
  position: absolute;
  top: 0;
  right: 1px;
  font-size: 0.5rem;
  line-height: 1;
  padding: 0.04rem 0.1rem;
  border-radius: 0.15rem;
  color: #fff;
  background: rgba(80, 190, 120, 0.85); /* 休 */
}

.cal-tag-work {
  background: rgba(220, 130, 90, 0.85); /* 班 */
}

/* 放假日数字微调色，增强可读性 */
.cal-cell.is-off .cal-num {
  color: rgba(150, 235, 180, 1);
}
</style>
