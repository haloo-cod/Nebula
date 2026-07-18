<template>
  <div class="about-activity">
    <!-- 热力图 -->
    <div class="heatmap-section">
      <h3 class="heatmap-title">
        <span class="heatmap-icon">📊</span>
        {{ totalContributions }} contributions in the last year
      </h3>

      <div class="heatmap-wrapper">
        <!-- 星期标签 -->
        <div class="heatmap-weekdays">
          <span></span>
          <span>Mon</span>
          <span></span>
          <span>Wed</span>
          <span></span>
          <span>Fri</span>
          <span></span>
        </div>

        <!-- 热力图网格 -->
        <div class="heatmap-scroll">
          <!-- 月份标签 -->
          <div class="heatmap-months">
            <span
              v-for="(month, idx) in monthLabels"
              :key="idx"
              class="month-label"
              :style="{ gridColumn: month.col }"
            >
              {{ month.name }}
            </span>
          </div>

          <!-- 格子 -->
          <div class="heatmap-grid">
            <div
              v-for="(day, idx) in heatmapDays"
              :key="idx"
              class="heatmap-cell"
              :class="getCellClass(day.count)"
              :title="`${day.date}: ${day.count} 次更新`"
            ></div>
          </div>
        </div>
      </div>

      <!-- 图例 -->
      <div class="heatmap-legend">
        <span>Less</span>
        <span class="legend-cell legend-0"></span>
        <span class="legend-cell legend-1"></span>
        <span class="legend-cell legend-2"></span>
        <span class="legend-cell legend-3"></span>
        <span class="legend-cell legend-4"></span>
        <span>More</span>
      </div>
    </div>

    <!-- 时间线 -->
    <div class="timeline-section">
      <div
        v-for="act in recentActivities"
        :key="act.id"
        class="timeline-item"
      >
        <div class="timeline-dot"></div>
        <RouterLink :to="act.url" class="timeline-card">
          <div class="timeline-card-head">
            <img :src="avatar" alt="author" class="timeline-avatar" />
            <span class="timeline-author">{{ profile.name }}</span>
            <span class="timeline-type">发布了 {{ act.type }}</span>
          </div>
          <div class="timeline-card-body">
            <span class="timeline-title">《{{ act.title }}》</span>
            <span class="timeline-date">{{ act.date }}</span>
          </div>
        </RouterLink>
      </div>

      <div v-if="recentActivities.length === 0" class="timeline-empty">
        暂无活动记录
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import { getPosts } from '@/data/posts'
import { avatar, profile } from '@/data/profile'
import type { ActivityRecord } from '@/types'

// 从 getPosts() 生成活动记录
const activities = computed<ActivityRecord[]>(() => {
  const posts = getPosts()
  return posts
    .filter((p) => !p.draft && p.date)
    .map((p) => ({
      id: p.slug,
      type: '文章' as const,
      title: p.title,
      date: p.date,
      url: `/post/${p.slug}`,
    }))
    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
})

// 最近的活动（时间线显示前 15 条）
const recentActivities = computed(() => activities.value.slice(0, 15))

// 总贡献数
const totalContributions = computed(() => activities.value.length)

// 热力图数据：过去 365 天每天的发文数
const activityMap = computed(() => {
  const map: Record<string, number> = {}
  activities.value.forEach((a) => {
    // 提取日期部分（YYYY-MM-DD）
    const dateKey = a.date.slice(0, 10)
    if (dateKey) {
      map[dateKey] = (map[dateKey] || 0) + 1
    }
  })
  return map
})

// 生成 365 天日期列表（从最早的周日开始，到今天结束）
const heatmapDays = computed(() => {
  const today = new Date()
  const endDate = new Date(today.getFullYear(), today.getMonth(), today.getDate())
  const startDate = new Date(endDate)
  startDate.setDate(endDate.getDate() - 364)
  // 回退到最近的周日
  startDate.setDate(startDate.getDate() - startDate.getDay())

  const days: { date: string; count: number }[] = []
  const curr = new Date(startDate)

  while (curr <= endDate) {
    const dateKey = formatDateKey(curr)
    days.push({
      date: dateKey,
      count: activityMap.value[dateKey] || 0,
    })
    curr.setDate(curr.getDate() + 1)
  }
  return days
})

// 月份标签
const monthLabels = computed(() => {
  const labels: { name: string; col: number }[] = []
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
  let lastMonth = -1

  for (let i = 0; i < heatmapDays.value.length; i++) {
    const d = new Date(heatmapDays.value[i].date)
    const month = d.getMonth()
    if (month !== lastMonth) {
      // 计算所在的列（周数）
      const weekCol = Math.floor(i / 7) + 1
      labels.push({ name: months[month], col: weekCol })
      lastMonth = month
    }
  }
  return labels
})

/** 格式化日期为 YYYY-MM-DD */
function formatDateKey(d: Date): string {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

/** 根据次数返回颜色 class */
function getCellClass(count: number): string {
  if (count === 0) return 'cell-0'
  if (count === 1) return 'cell-1'
  if (count === 2) return 'cell-2'
  if (count === 3) return 'cell-3'
  return 'cell-4'
}
</script>

<style scoped>
.about-activity {
  padding: 0 1.5rem 1.5rem;
}

/* ===== 热力图 ===== */
.heatmap-section {
  margin-bottom: 2.5rem;
  padding: 1.25rem;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 1.25rem;
}

.heatmap-title {
  margin: 0 0 1rem;
  color: var(--text-primary);
  font-size: 0.92rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.heatmap-icon {
  font-size: 1rem;
}

.heatmap-wrapper {
  display: flex;
  gap: 0.4rem;
}

.heatmap-weekdays {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding-top: 1.2rem;
}

.heatmap-weekdays span {
  height: 11px;
  font-size: 0.6rem;
  color: var(--text-muted);
  display: flex;
  align-items: center;
}

.heatmap-scroll {
  flex: 1;
  overflow-x: auto;
  padding-bottom: 0.5rem;
}

.heatmap-months {
  display: grid;
  grid-template-columns: repeat(53, 11px);
  gap: 3px;
  margin-bottom: 4px;
  height: 1rem;
}

.month-label {
  font-size: 0.6rem;
  color: var(--text-muted);
  white-space: nowrap;
}

.heatmap-grid {
  display: grid;
  grid-template-rows: repeat(7, 11px);
  grid-auto-flow: column;
  grid-auto-columns: 11px;
  gap: 3px;
}

.heatmap-cell {
  width: 11px;
  height: 11px;
  border-radius: 3px;
  transition: all 0.2s ease;
}

.heatmap-cell:hover {
  outline: 2px solid rgba(140, 185, 255, 0.5);
  outline-offset: 1px;
}

.cell-0 { background: rgba(255, 255, 255, 0.06); }
.cell-1 { background: rgba(74, 222, 128, 0.3); }
.cell-2 { background: rgba(74, 222, 128, 0.5); }
.cell-3 { background: rgba(34, 197, 94, 0.7); }
.cell-4 { background: rgba(22, 163, 74, 0.9); }

.heatmap-legend {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.3rem;
  margin-top: 0.75rem;
  font-size: 0.6rem;
  color: var(--text-muted);
}

.legend-cell {
  width: 11px;
  height: 11px;
  border-radius: 3px;
}

.legend-0 { background: rgba(255, 255, 255, 0.06); }
.legend-1 { background: rgba(74, 222, 128, 0.3); }
.legend-2 { background: rgba(74, 222, 128, 0.5); }
.legend-3 { background: rgba(34, 197, 94, 0.7); }
.legend-4 { background: rgba(22, 163, 74, 0.9); }

/* ===== 时间线 ===== */
.timeline-section {
  position: relative;
  padding-left: 1.5rem;
  border-left: 2px solid rgba(140, 185, 255, 0.15);
}

.timeline-item {
  position: relative;
  margin-bottom: 1rem;
}

.timeline-dot {
  position: absolute;
  left: -1.85rem;
  top: 50%;
  transform: translateY(-50%);
  width: 0.75rem;
  height: 0.75rem;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  border: 2px solid rgba(140, 185, 255, 0.6);
  transition: transform 0.2s ease;
}

.timeline-item:hover .timeline-dot {
  transform: translateY(-50%) scale(1.3);
}

.timeline-card {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.85rem 1rem;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 1rem;
  text-decoration: none;
  transition: all 0.2s ease;
}

.timeline-card:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(140, 185, 255, 0.25);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.timeline-card-head {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.timeline-avatar {
  width: 1.5rem;
  height: 1.5rem;
  border-radius: 50%;
  object-fit: cover;
}

.timeline-author {
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--text-primary);
}

.timeline-type {
  font-size: 0.72rem;
  font-weight: 600;
  color: rgba(140, 185, 255, 0.8);
}

.timeline-card-body {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.timeline-title {
  font-size: 0.88rem;
  font-weight: 700;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
  flex: 1;
}

.timeline-card:hover .timeline-title {
  color: rgba(140, 185, 255, 0.95);
}

.timeline-date {
  font-size: 0.68rem;
  color: var(--text-muted);
  font-family: monospace;
  white-space: nowrap;
  flex-shrink: 0;
  padding: 0.15rem 0.4rem;
  background: rgba(255, 255, 255, 0.04);
  border-radius: 0.3rem;
}

.timeline-empty {
  text-align: center;
  padding: 2rem 0;
  color: var(--text-muted);
  font-size: 0.82rem;
}

@media (min-width: 768px) {
  .about-activity {
    padding: 0 2.5rem 2rem;
  }

  .heatmap-section {
    padding: 1.5rem;
  }
}
</style>

<!-- Light 主题适配 -->
<style>
[data-theme='light'] .about-activity .heatmap-section {
  background: rgba(0, 0, 0, 0.02);
  border-color: rgba(0, 0, 0, 0.06);
}

[data-theme='light'] .about-activity .cell-0 {
  background: rgba(0, 0, 0, 0.05);
}

[data-theme='light'] .about-activity .legend-0 {
  background: rgba(0, 0, 0, 0.05);
}

[data-theme='light'] .about-activity .timeline-section {
  border-left-color: rgba(50, 100, 220, 0.2);
}

[data-theme='light'] .about-activity .timeline-dot {
  border-color: rgba(50, 100, 220, 0.6);
  background: rgba(50, 100, 220, 0.05);
}

[data-theme='light'] .about-activity .timeline-card {
  background: rgba(0, 0, 0, 0.02);
  border-color: rgba(0, 0, 0, 0.06);
}

[data-theme='light'] .about-activity .timeline-card:hover {
  background: rgba(0, 0, 0, 0.04);
  border-color: rgba(50, 100, 220, 0.25);
}

[data-theme='light'] .about-activity .timeline-type {
  color: rgba(40, 80, 160, 0.8);
}

[data-theme='light'] .about-activity .timeline-card:hover .timeline-title {
  color: rgba(40, 80, 160, 1);
}
</style>
