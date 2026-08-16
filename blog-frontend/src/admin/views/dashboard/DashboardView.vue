<script setup lang="ts">
/**
 * 管理后台仪表盘：内容概览与访问分析。
 */
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  Document,
  ChatDotRound,
  Reading,
  Connection,
  EditPen,
  Upload,
  Picture,
  Refresh,
} from '@element-plus/icons-vue'
import { api } from '@/api/client'

interface Overview {
  today_pv: number
  today_uv: number
  yesterday_pv: number
  yesterday_uv: number
  total_pv: number
  total_uv: number
  page_views: number
  book_downloads: number
  zip_downloads: number
}

interface TrendItem {
  date: string
  pv: number
  uv: number
}

interface PageItem {
  path: string
  title: string
  pv: number
  uv: number
}

interface VisitorItem {
  id: number
  event_type: string
  path: string
  title: string
  ip_address: string
  user_agent: string
  referrer: string
  occurred_at: string
}

const overview = ref<Overview | null>(null)
const router = useRouter()
const trend = ref<TrendItem[]>([])
const pages = ref<PageItem[]>([])
const visitors = ref<VisitorItem[]>([])
const loading = ref(false)

const maxTrendValue = computed(() => Math.max(1, ...trend.value.map((item) => item.pv)))
const pvPoints = computed(() => makeChartPoints('pv'))
const uvPoints = computed(() => makeChartPoints('uv'))
const pvAreaPoints = computed(() => makeAreaPoints('pv'))
const uvAreaPoints = computed(() => makeAreaPoints('uv'))
const pvDots = computed(() => makeDots('pv'))
const uvDots = computed(() => makeDots('uv'))
const recentSevenDayPv = computed(() => trend.value.reduce((sum, item) => sum + item.pv, 0))
const recentSevenDayUv = computed(() => trend.value.reduce((sum, item) => sum + item.uv, 0))

/** 快捷操作跳转到对应的后台功能页。 */
function goToShortcut(path: string) {
  void router.push(path)
}

function makeChartPoints(key: 'pv' | 'uv'): string {
  if (trend.value.length === 0) return ''
  const width = 720
  const height = 220
  const step = trend.value.length === 1 ? 0 : width / (trend.value.length - 1)
  return trend.value
    .map((item, index) => {
      const x = index * step
      const y = height - (item[key] / maxTrendValue.value) * (height - 20) - 10
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(' ')
}

/** 折线下方闭合为面积填充区域（首尾接 x 轴底部）。 */
function makeAreaPoints(key: 'pv' | 'uv'): string {
  const line = makeChartPoints(key)
  if (!line) return ''
  return `0,220 ${line} 720,220`
}

/** 每个数据点的坐标，用于绘制圆点标记。 */
function makeDots(key: 'pv' | 'uv'): Array<{ x: number; y: number }> {
  if (trend.value.length === 0) return []
  const width = 720
  const height = 220
  const step = trend.value.length === 1 ? 0 : width / (trend.value.length - 1)
  return trend.value.map((item, index) => ({
    x: +(index * step).toFixed(1),
    y: +(height - (item[key] / maxTrendValue.value) * (height - 20) - 10).toFixed(1),
  }))
}

function formatDate(value: string): string {
  return value.slice(5).replace('-', '/')
}

function formatDateTime(value: string): string {
  // 后端时间均为 UTC，若字符串不带时区信息则补 Z
  const normalized = /[+\-]\d{2}:\d{2}$/.test(value) || value.endsWith('Z') ? value : value + 'Z'
  const date = new Date(normalized)
  return Number.isNaN(date.getTime()) ? value.replace('T', ' ').slice(0, 19) : date.toLocaleString()
}

function eventLabel(value: string): string {
  const labels: Record<string, string> = {
    page_view: '页面访问',
    book_open: '打开图书',
    book_download: '下载图书',
    file_download: '下载文件',
    zip_download: '下载 ZIP',
  }
  return labels[value] || value
}

async function loadAnalytics() {
  loading.value = true
  try {
    const [overviewData, trendData, pagesData, visitorsData] = await Promise.all([
      api.get<Overview>('/api/v1/analytics/overview', true),
      api.get<TrendItem[]>('/api/v1/analytics/trend', true),
      api.get<PageItem[]>('/api/v1/analytics/pages', true),
      api.get<{ items: VisitorItem[]; total: number }>(
        '/api/v1/analytics/visitors?page=1&page_size=10',
        true,
      ),
    ])
    overview.value = overviewData
    trend.value = trendData
    pages.value = pagesData
    visitors.value = visitorsData.items
  } catch {
    // 统计接口暂时不可用时保留已加载的数据。
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await loadAnalytics()
})
</script>

<template>
  <div class="dashboard-page">
    <section class="dashboard-intro">
      <div>
        <span class="dashboard-eyebrow">OVERVIEW</span>
        <h1>欢迎回来，管理员</h1>
        <p>这里是你的内容工作台，快速了解站点状态与最近动态。</p>
      </div>
      <el-button :icon="Refresh" :loading="loading" @click="loadAnalytics">刷新数据</el-button>
    </section>
    <!-- 统计卡片 -->
    <div class="stat-cards">
      <el-card shadow="hover" class="stat-card">
        <div class="stat-content">
          <div class="stat-icon">
            <el-icon><Document /></el-icon>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ overview?.today_pv ?? '--' }}</span>
            <span class="stat-label">今日浏览量（PV）</span>
          </div>
        </div>
      </el-card>

      <el-card shadow="hover" class="stat-card">
        <div class="stat-content">
          <div class="stat-icon">
            <el-icon><ChatDotRound /></el-icon>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ overview?.today_uv ?? '--' }}</span>
            <span class="stat-label">今日访客数（UV）</span>
          </div>
        </div>
      </el-card>

      <el-card shadow="hover" class="stat-card">
        <div class="stat-content">
          <div class="stat-icon">
            <el-icon><Reading /></el-icon>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ overview?.total_pv ?? '--' }}</span>
            <span class="stat-label">累计浏览量（PV）</span>
          </div>
        </div>
      </el-card>

      <el-card shadow="hover" class="stat-card">
        <div class="stat-content">
          <div class="stat-icon">
            <el-icon><Connection /></el-icon>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ overview?.total_uv ?? '--' }}</span>
            <span class="stat-label">累计访客数（UV）</span>
          </div>
        </div>
      </el-card>
    </div>

    <div class="analytics-header">
      <div>
        <span class="section-eyebrow">TRAFFIC</span>
        <h2>访问分析</h2>
        <span>
          最近 7 天浏览量（PV）{{ recentSevenDayPv }} · 访客数（UV）{{ recentSevenDayUv }}
        </span>
      </div>
    </div>

    <el-card shadow="never" class="chart-card">
      <template #header><span>最近 7 天访问趋势</span></template>
      <div v-if="trend.length" class="chart-wrap">
        <svg
          viewBox="0 0 720 260"
          preserveAspectRatio="xMidYMid meet"
          class="trend-chart"
          role="img"
          aria-label="最近七天访问趋势"
        >
          <defs>
            <linearGradient id="chartAreaPv" x1="0" y1="0" x2="0" y2="1">
              <stop
                offset="0%"
                style="stop-color: var(--admin-primary-color); stop-opacity: 0.22"
              />
              <stop offset="100%" style="stop-color: var(--admin-primary-color); stop-opacity: 0" />
            </linearGradient>
            <linearGradient id="chartAreaUv" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" style="stop-color: #e09b4b; stop-opacity: 0.16" />
              <stop offset="100%" style="stop-color: #e09b4b; stop-opacity: 0" />
            </linearGradient>
          </defs>
          <line
            v-for="level in [0, 1, 2, 3, 4]"
            :key="level"
            :x1="0"
            :x2="720"
            :y1="220 - level * 50"
            :y2="220 - level * 50"
            class="chart-grid"
          />
          <text
            v-for="level in [0, 1, 2, 3, 4]"
            :key="`value-${level}`"
            x="4"
            :y="224 - level * 50"
            class="chart-axis-label"
          >
            {{ Math.round((maxTrendValue * level) / 4) }}
          </text>
          <polygon :points="pvAreaPoints" class="chart-area chart-area-pv" />
          <polygon :points="uvAreaPoints" class="chart-area chart-area-uv" />
          <polyline :points="pvPoints" class="chart-line chart-line-pv" />
          <polyline :points="uvPoints" class="chart-line chart-line-uv" />
          <circle
            v-for="(dot, index) in pvDots"
            :key="`pv-dot-${index}`"
            :cx="dot.x"
            :cy="dot.y"
            r="3.5"
            class="chart-dot chart-dot-pv"
          />
          <circle
            v-for="(dot, index) in uvDots"
            :key="`uv-dot-${index}`"
            :cx="dot.x"
            :cy="dot.y"
            r="3.5"
            class="chart-dot chart-dot-uv"
          />
        </svg>
        <div class="chart-labels">
          <span v-for="item in trend" :key="item.date">{{ formatDate(item.date) }}</span>
        </div>
        <div class="chart-legend">
          <span><i class="legend-dot legend-pv"></i>浏览量（PV）</span>
          <span><i class="legend-dot legend-uv"></i>访客数（UV）</span>
        </div>
      </div>
      <el-empty v-else description="暂无访问数据，访问前台页面后会开始记录" />
    </el-card>

    <div class="analytics-grid">
      <el-card shadow="never" class="data-card">
        <template #header><span>热门页面</span></template>
        <el-table :data="pages" size="small" stripe>
          <el-table-column label="页面" min-width="180" show-overflow-tooltip>
            <template #default="{ row }">
              <span>{{ row.title }}</span
              ><small>{{ row.path }}</small>
            </template>
          </el-table-column>
          <el-table-column prop="pv" label="浏览量（PV）" width="110" />
          <el-table-column prop="uv" label="访客数（UV）" width="110" />
        </el-table>
        <el-empty v-if="pages.length === 0" description="暂无页面数据" :image-size="60" />
      </el-card>

      <el-card shadow="never" class="data-card">
        <template #header>
          <div class="card-header-with-action">
            <span>最近访问</span>
            <el-button link type="primary" @click="router.push('/admin/analytics/visitors')">
              查看全部
            </el-button>
          </div>
        </template>
        <el-table :data="visitors" size="small" stripe>
          <el-table-column label="时间" width="150">
            <template #default="{ row }">{{ formatDateTime(row.occurred_at) }}</template>
          </el-table-column>
          <el-table-column prop="ip_address" label="IP" width="130" />
          <el-table-column label="事件" min-width="110">
            <template #default="{ row }">{{ eventLabel(row.event_type) }}</template>
          </el-table-column>
          <el-table-column prop="path" label="页面" min-width="150" show-overflow-tooltip />
        </el-table>
        <el-empty v-if="visitors.length === 0" description="暂无访问记录" :image-size="60" />
      </el-card>
    </div>

    <!-- 快捷操作 -->
    <el-card shadow="never" class="quick-actions">
      <template #header>
        <span>快捷操作</span>
      </template>
      <div class="action-btns">
        <el-button type="primary" @click="goToShortcut('/admin/posts/new')">
          <el-icon><EditPen /></el-icon>写文章
        </el-button>
        <el-button @click="goToShortcut('/admin/moments')">
          <el-icon><ChatDotRound /></el-icon>发说说
        </el-button>
        <el-button @click="goToShortcut('/admin/books')">
          <el-icon><Upload /></el-icon>上传图书
        </el-button>
        <el-button @click="goToShortcut('/admin/files')">
          <el-icon><Picture /></el-icon>上传图片
        </el-button>
      </div>
    </el-card>

    <!-- 欢迎信息 -->
    <el-card shadow="never" class="welcome-card">
      <div class="welcome-content">
        <h2>欢迎使用博客管理后台</h2>
        <p>在这里你可以管理博客的所有内容：文章、说说、图书、相册、友链等。</p>
        <p class="tip">
          图书下载 {{ overview?.book_downloads ?? '--' }} 次，ZIP 下载
          {{ overview?.zip_downloads ?? '--' }} 次。
        </p>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.dashboard-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.dashboard-intro {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  padding: 4px 0 2px;
}

.dashboard-intro h1 {
  margin: 4px 0 6px;
  color: var(--admin-text-color, #18181b);
  font-size: clamp(24px, 3vw, 32px);
  font-weight: 700;
  letter-spacing: -0.035em;
  line-height: 1.15;
}

.dashboard-intro p,
.analytics-header span {
  margin: 0;
  color: var(--admin-text-secondary, #71717a);
  font-size: 13px;
}

.dashboard-eyebrow,
.section-eyebrow {
  color: var(--admin-primary-color);
  font-size: 10px;
  font-weight: 750;
  letter-spacing: 0.16em;
}

.stat-cards {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.stat-card {
  min-height: 128px;
  border-radius: 16px;
}

.stat-card :deep(.el-card__body) {
  height: 100%;
  padding: 20px;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 14px;
}

.stat-icon {
  display: grid;
  width: 46px;
  height: 46px;
  flex: 0 0 46px;
  place-items: center;
  border-radius: 13px;
  background: var(--admin-menu-active-bg);
  color: var(--admin-primary-color);
  font-size: 22px;
}

.stat-icon .el-icon {
  font-size: inherit;
}

.stat-info {
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.stat-value {
  color: var(--admin-text-color, #18181b);
  font-size: 30px;
  font-weight: 700;
  letter-spacing: -0.04em;
  line-height: 1;
}

.stat-label {
  color: var(--admin-text-secondary, #71717a);
  font-size: 12px;
}

.analytics-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.analytics-header h2 {
  margin: 4px 0 5px;
  color: var(--admin-text-color, #18181b);
  font-size: 20px;
}

.chart-card,
.data-card,
.quick-actions,
.welcome-card {
  border-radius: 16px;
}

.chart-wrap {
  position: relative;
  padding: 4px 0 28px;
}

.trend-chart {
  display: block;
  width: 100%;
  height: auto;
  aspect-ratio: 720 / 260;
  overflow: visible;
}

.chart-grid {
  stroke: var(--admin-border-color, #e4e4e7);
  stroke-dasharray: 4 5;
  stroke-width: 1;
}

.chart-axis-label {
  fill: var(--admin-text-secondary, #71717a);
  font-size: 11px;
  text-anchor: start;
}

.chart-line {
  fill: none;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 3;
  vector-effect: non-scaling-stroke;
}

.chart-line-pv {
  stroke: var(--admin-primary-color);
}

.chart-line-uv {
  stroke: #e09b4b;
}

.chart-area {
  stroke: none;
}

.chart-area-pv {
  fill: url(#chartAreaPv);
}

.chart-area-uv {
  fill: url(#chartAreaUv);
}

.chart-dot {
  stroke-width: 2;
  stroke: var(--admin-panel-bg, #ffffff);
  vector-effect: non-scaling-stroke;
}

.chart-dot-pv {
  fill: var(--admin-primary-color);
}

.chart-dot-uv {
  fill: #e09b4b;
}

.chart-labels,
.chart-legend {
  display: flex;
  justify-content: space-between;
  color: var(--admin-text-secondary, #71717a);
  font-size: 11px;
}

.chart-legend {
  justify-content: center;
  gap: 18px;
  margin-top: 10px;
  font-size: 12px;
}

.chart-legend span {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.legend-pv {
  background: var(--admin-primary-color);
}

.legend-uv {
  background: #e09b4b;
}

.analytics-grid {
  display: grid;
  grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.1fr);
  gap: 16px;
}

.data-card :deep(.el-table) {
  background: transparent;
}

.data-card :deep(.el-table small) {
  display: block;
  overflow: hidden;
  color: var(--admin-text-secondary, #71717a);
  font-size: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-header-with-action {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.action-btns {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.action-btns .el-button {
  width: 100%;
  margin: 0;
}

.welcome-content h2 {
  margin: 0 0 8px;
  color: var(--admin-text-color, #18181b);
  font-size: 18px;
}

.welcome-content p {
  margin: 0 0 4px;
  color: var(--admin-text-secondary, #71717a);
  font-size: 14px;
}

.welcome-content .tip {
  opacity: 0.7;
  font-style: italic;
}

@media (max-width: 1100px) {
  .stat-cards {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .analytics-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .dashboard-intro {
    align-items: stretch;
    flex-direction: column;
  }

  .dashboard-intro .el-button {
    align-self: flex-start;
  }

  .stat-cards,
  .action-btns {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .analytics-header {
    align-items: flex-start;
  }

  .chart-card :deep(.el-card__body) {
    padding: 12px;
  }
}
</style>
