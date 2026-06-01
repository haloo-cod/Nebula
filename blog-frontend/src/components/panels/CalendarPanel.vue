<template>
  <GlassPanel :flat="flat" class="calendar-panel">
    <!-- 头部：年月 + 切换 -->
    <div class="cal-header">
      <button class="cal-nav" @click="prevMonth" aria-label="上个月">‹</button>
      <div class="cal-title">
        <span class="cal-ym">{{ viewYear }}年{{ viewMonth }}月</span>
        <button class="cal-today-btn" v-if="!isCurrentMonth" @click="goToday">回今天</button>
      </div>
      <button class="cal-nav" @click="nextMonth" aria-label="下个月">›</button>
    </div>

    <!-- 星期表头 -->
    <div class="cal-grid cal-weekdays">
      <span
        v-for="(w, i) in weekLabels"
        :key="w"
        class="cal-weekday"
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
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import GlassPanel from './GlassPanel.vue'
import { getSolarTerms, getHolidays, pickMonthHolidays } from '@/data/calendar'

defineProps({
  flat: { type: Boolean, default: false },
})

const weekLabels = ['日', '一', '二', '三', '四', '五', '六']

const now = new Date()
const todayKey = `${now.getFullYear()}-${now.getMonth() + 1}-${now.getDate()}`

const viewYear = ref(now.getFullYear())
const viewMonth = ref(now.getMonth() + 1) // 1-12

const solarTerms = ref({}) // { day: '节气' }
const holidays = ref({}) // { day: { name, isOff, isWork } }

const isCurrentMonth = computed(
  () => viewYear.value === now.getFullYear() && viewMonth.value === now.getMonth() + 1,
)

const cells = computed(() => {
  const year = viewYear.value
  const month = viewMonth.value
  const firstWeekday = new Date(year, month - 1, 1).getDay() // 0=周日
  const daysInMonth = new Date(year, month, 0).getDate()
  const list = []
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

function cellTitle(cell) {
  const parts = []
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
  /* 宽度跟随右列（20%），如需更宽可在 index.vue 调整列宽 */
  min-height: 0;
}

/* 头部 */
.cal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.cal-title {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.15rem;
}

.cal-ym {
  font-size: 0.95rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.92);
  letter-spacing: 0.02em;
}

.cal-today-btn {
  font-size: 0.65rem;
  color: rgba(255, 255, 255, 0.55);
  background: rgba(255, 255, 255, 0.08);
  border: none;
  border-radius: 0.4rem;
  padding: 0.05rem 0.4rem;
  cursor: pointer;
  transition:
    color 0.2s ease,
    background 0.2s ease;
}

.cal-today-btn:hover {
  color: rgba(255, 255, 255, 0.9);
  background: rgba(255, 255, 255, 0.16);
}

.cal-nav {
  font-size: 1.25rem;
  line-height: 1;
  color: rgba(255, 255, 255, 0.55);
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 0 0.35rem;
  border-radius: 0.4rem;
  transition:
    color 0.2s ease,
    background 0.2s ease;
}

.cal-nav:hover {
  color: rgba(255, 255, 255, 0.95);
  background: rgba(255, 255, 255, 0.1);
}

/* 网格 */
.cal-grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 0.15rem;
}

/* 关键：grid 子项默认 min-width:auto，长文本（如"劳动节"）会撑破列宽导致溢出 */
.cal-grid > * {
  min-width: 0;
}

.cal-weekdays {
  margin-bottom: 0.3rem;
}

.cal-weekday {
  text-align: center;
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.4);
  padding: 0.2rem 0;
}

.cal-weekday.is-weekend {
  color: rgba(255, 180, 180, 0.55);
}

/* 日期格子 */
.cal-cell {
  position: relative;
  aspect-ratio: 1 / 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 0.5rem;
  transition: background 0.2s ease;
  min-width: 0;
  overflow: hidden;
  padding: 0 1px;
}

.cal-cell:not(.is-empty):hover {
  background: rgba(255, 255, 255, 0.07);
}

.cal-cell.is-empty {
  pointer-events: none;
}

.cal-num {
  font-size: 0.85rem;
  line-height: 1;
  color: rgba(255, 255, 255, 0.85);
}

.cal-cell.is-weekend .cal-num {
  color: rgba(255, 190, 190, 0.85);
}

.cal-sub {
  font-size: 0.55rem;
  line-height: 1.1;
  margin-top: 0.1rem;
  color: rgba(140, 200, 255, 0.85);
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
  background: rgba(120, 170, 255, 0.22);
  box-shadow: inset 0 0 0 1px rgba(140, 190, 255, 0.5);
}

.cal-cell.is-today .cal-num {
  color: #fff;
  font-weight: 700;
}

/* 放假/补班角标 */
.cal-tag {
  position: absolute;
  top: 1px;
  right: 2px;
  font-size: 0.5rem;
  line-height: 1;
  padding: 0.05rem 0.12rem;
  border-radius: 0.2rem;
  color: #fff;
  background: rgba(80, 190, 120, 0.85); /* 休 */
}

.cal-tag-work {
  background: rgba(220, 130, 90, 0.85); /* 班 */
}

/* 放假日数字微调色，增强可读性 */
.cal-cell.is-off .cal-num {
  color: rgba(150, 235, 180, 0.95);
}
</style>
