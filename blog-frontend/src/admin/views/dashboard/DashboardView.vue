<script setup lang="ts">
/**
 * 管理后台仪表盘 — 方案 A（纸墨刊物）与方案 B（星夜曜石暗色）统一实现
 * 展示一体式 4 格 KPI 指标带、平滑双折线趋势图、快捷创作清单、热门页面与最近访客。
 */
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight, Refresh } from '@element-plus/icons-vue'
import { api } from '@/api/client'
import AdminPageHeader from '@/admin/components/AdminPageHeader.vue'

/** 站点访问概览统计 */
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

/** 单日访问趋势点 */
interface TrendItem {
  date: string
  pv: number
  uv: number
}

/** 热门页面条目 */
interface PageItem {
  path: string
  title: string
  pv: number
  uv: number
}

/** 访客日志条目 */
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

/** 图表二维坐标点 */
interface ChartPoint {
  x: number
  y: number
}

const CHART_WIDTH = 680
const CHART_HEIGHT = 210
const CHART_PAD_TOP = 16
const CHART_PAD_BOTTOM = 10
const CHART_PAD_X = 12

const router = useRouter()
const overview = ref<Overview | null>(null)
const trend = ref<TrendItem[]>([])
const pages = ref<PageItem[]>([])
const visitors = ref<VisitorItem[]>([])
const loading = ref(false)
const hoveredIndex = ref<number | null>(null)

const maxTrendValue = computed(() => Math.max(4, ...trend.value.map((item) => item.pv)))
const maxPagePv = computed(() => Math.max(1, ...pages.value.map((item) => item.pv)))
const recentSevenDayPv = computed(() => trend.value.reduce((sum, item) => sum + item.pv, 0))
const recentSevenDayUv = computed(() => trend.value.reduce((sum, item) => sum + item.uv, 0))

const pvPoints = computed(() => buildPoints('pv'))
const uvPoints = computed(() => buildPoints('uv'))
const pvLinePath = computed(() => buildSmoothPath(pvPoints.value))
const uvLinePath = computed(() => buildSmoothPath(uvPoints.value))
const pvAreaPath = computed(() => buildAreaPath(pvPoints.value, pvLinePath.value))
const uvAreaPath = computed(() => buildAreaPath(uvPoints.value, uvLinePath.value))

const activeTrend = computed(() =>
  hoveredIndex.value !== null ? (trend.value[hoveredIndex.value] ?? null) : null,
)
const activePoint = computed(() =>
  hoveredIndex.value !== null ? (pvPoints.value[hoveredIndex.value] ?? null) : null,
)

const shortcuts = [
  { label: '写新文章', desc: '打开 Markdown 编辑器', path: '/admin/posts/new' },
  { label: '发布说说', desc: '记录一条此刻心情', path: '/admin/moments' },
  { label: '上传图书', desc: '导入 EPUB 到书库', path: '/admin/books' },
  { label: '媒体与文件库', desc: '浏览本地与 R2 资源', path: '/admin/files' },
]

/** 计算较昨日变化文本与正负态 */
function calcDelta(today: number | undefined, yesterday: number | undefined): {
  text: string
  tone: 'up' | 'down' | 'flat'
} | null {
  if (today === undefined || yesterday === undefined) return null
  if (yesterday === 0) {
    return today > 0 ? { text: `+${today}`, tone: 'up' } : { text: '0%', tone: 'flat' }
  }
  const pct = Math.round(((today - yesterday) / yesterday) * 100)
  if (pct > 0) return { text: `+${pct}%`, tone: 'up' }
  if (pct < 0) return { text: `${pct}%`, tone: 'down' }
  return { text: '0%', tone: 'flat' }
}

const pvDelta = computed(() => calcDelta(overview.value?.today_pv, overview.value?.yesterday_pv))
const uvDelta = computed(() => calcDelta(overview.value?.today_uv, overview.value?.yesterday_uv))

function formatNumber(value: number | undefined): string {
  if (value === undefined) return '--'
  return value.toLocaleString('zh-CN')
}

function buildPoints(key: 'pv' | 'uv'): ChartPoint[] {
  const count = trend.value.length
  if (count === 0) return []
  const usableW = CHART_WIDTH - CHART_PAD_X * 2
  const usableH = CHART_HEIGHT - CHART_PAD_TOP - CHART_PAD_BOTTOM
  const step = count === 1 ? 0 : usableW / (count - 1)
  return trend.value.map((item, index) => ({
    x: +(CHART_PAD_X + index * step).toFixed(1),
    y: +(
      CHART_PAD_TOP +
      usableH -
      (item[key] / maxTrendValue.value) * usableH
    ).toFixed(1),
  }))
}

/** 用 Catmull-Rom 近似三次贝塞尔生成平滑曲线路径 */
function buildSmoothPath(points: ChartPoint[]): string {
  if (points.length === 0) return ''
  if (points.length === 1) return `M ${points[0].x} ${points[0].y}`
  let d = `M ${points[0].x} ${points[0].y}`
  for (let i = 0; i < points.length - 1; i++) {
    const p0 = points[Math.max(0, i - 1)]
    const p1 = points[i]
    const p2 = points[i + 1]
    const p3 = points[Math.min(points.length - 1, i + 2)]
    const cp1x = p1.x + (p2.x - p0.x) / 6
    const cp1y = Math.min(CHART_HEIGHT - CHART_PAD_BOTTOM, Math.max(CHART_PAD_TOP, p1.y + (p2.y - p0.y) / 6))
    const cp2x = p2.x - (p3.x - p1.x) / 6
    const cp2y = Math.min(CHART_HEIGHT - CHART_PAD_BOTTOM, Math.max(CHART_PAD_TOP, p2.y - (p3.y - p1.y) / 6))
    d += ` C ${cp1x.toFixed(1)} ${cp1y.toFixed(1)}, ${cp2x.toFixed(1)} ${cp2y.toFixed(1)}, ${p2.x} ${p2.y}`
  }
  return d
}

function buildAreaPath(points: ChartPoint[], linePath: string): string {
  if (points.length < 2 || !linePath) return ''
  const baseline = CHART_HEIGHT - CHART_PAD_BOTTOM
  const first = points[0]
  const last = points[points.length - 1]
  return `${linePath} L ${last.x} ${baseline} L ${first.x} ${baseline} Z`
}

function formatDate(value: string): string {
  return value.slice(5).replace('-', '/')
}

function formatShortTime(value: string): string {
  const normalized = /[+\-]\d{2}:\d{2}$/.test(value) || value.endsWith('Z') ? value : value + 'Z'
  const date = new Date(normalized)
  if (Number.isNaN(date.getTime())) return value.slice(11, 16)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', hour12: false })
}

function eventLabel(value: string): string {
  const labels: Record<string, string> = {
    page_view: '浏览',
    book_open: '阅读',
    book_download: '图书下载',
    file_download: '文件下载',
    zip_download: 'ZIP 下载',
  }
  return labels[value] || value
}

function goToShortcut(path: string) {
  void router.push(path)
}

async function loadAnalytics() {
  loading.value = true
  try {
    const [overviewData, trendData, pagesData, visitorsData] = await Promise.all([
      api.get<Overview>('/api/v1/analytics/overview', true),
      api.get<TrendItem[]>('/api/v1/analytics/trend', true),
      api.get<PageItem[]>('/api/v1/analytics/pages', true),
      api.get<{ items: VisitorItem[]; total: number }>(
        '/api/v1/analytics/visitors?page=1&page_size=8',
        true,
      ),
    ])
    overview.value = overviewData
    trend.value = trendData
    pages.value = pagesData
    visitors.value = visitorsData.items
  } catch {
    // 统计接口异常时保留已加载数据
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void loadAnalytics()
})
</script>

<template>
  <div class="admin-page dashboard-page">
    <AdminPageHeader
      eyebrow="OVERVIEW"
      title="内容工作台"
      subtitle="欢迎回来，在这里快速掌握站点访问趋势与近期动态。"
    >
      <template #actions>
        <el-button :icon="Refresh" :loading="loading" @click="loadAnalytics">刷新</el-button>
      </template>
    </AdminPageHeader>

    <!-- 一体式 4 格 KPI 指标带 -->
    <section class="admin-surface kpi-strip" aria-label="核心访问指标">
      <div class="kpi-cell">
        <span class="kpi-label">今日浏览 PV</span>
        <div class="kpi-value-row">
          <strong class="kpi-value admin-mono">{{ formatNumber(overview?.today_pv) }}</strong>
          <span v-if="pvDelta" class="kpi-delta" :class="`is-${pvDelta.tone}`">{{ pvDelta.text }}</span>
        </div>
      </div>
      <div class="kpi-cell">
        <span class="kpi-label">今日访客 UV</span>
        <div class="kpi-value-row">
          <strong class="kpi-value admin-mono">{{ formatNumber(overview?.today_uv) }}</strong>
          <span v-if="uvDelta" class="kpi-delta" :class="`is-${uvDelta.tone}`">{{ uvDelta.text }}</span>
        </div>
      </div>
      <div class="kpi-cell">
        <span class="kpi-label">累计浏览 PV</span>
        <div class="kpi-value-row">
          <strong class="kpi-value admin-mono">{{ formatNumber(overview?.total_pv) }}</strong>
        </div>
      </div>
      <div class="kpi-cell">
        <span class="kpi-label">累计访客 UV</span>
        <div class="kpi-value-row">
          <strong class="kpi-value admin-mono">{{ formatNumber(overview?.total_uv) }}</strong>
        </div>
      </div>
    </section>

    <!-- 2:1 非对称主区：访问趋势 + 快捷创作 -->
    <section class="dashboard-main-grid">
      <article class="admin-surface panel-card">
        <header class="panel-head">
          <div>
            <h2>最近 7 天访问趋势</h2>
            <p class="panel-sub admin-mono">
              PV {{ recentSevenDayPv.toLocaleString('zh-CN') }} · UV
              {{ recentSevenDayUv.toLocaleString('zh-CN') }}
            </p>
          </div>
          <div class="chart-legend">
            <span><i class="legend-dot is-pv"></i>PV</span>
            <span><i class="legend-dot is-uv"></i>UV</span>
          </div>
        </header>

        <div v-if="trend.length" class="chart-body" @mouseleave="hoveredIndex = null">
          <div
            v-if="activeTrend && activePoint"
            class="chart-tooltip admin-mono"
            :style="{ left: `${Math.min(82, Math.max(18, (activePoint.x / CHART_WIDTH) * 100))}%` }"
          >
            <span>{{ formatDate(activeTrend.date) }}</span>
            <strong>PV {{ activeTrend.pv }}</strong>
            <small>UV {{ activeTrend.uv }}</small>
          </div>

          <svg
            :viewBox="`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`"
            preserveAspectRatio="none"
            class="trend-svg"
            role="img"
            aria-label="最近七天访问趋势"
          >
            <defs>
              <linearGradient id="editorialAreaPv" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" style="stop-color: var(--admin-primary-color); stop-opacity: 0.2" />
                <stop offset="100%" style="stop-color: var(--admin-primary-color); stop-opacity: 0" />
              </linearGradient>
              <linearGradient id="editorialAreaUv" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" style="stop-color: var(--admin-chart-secondary); stop-opacity: 0.16" />
                <stop offset="100%" style="stop-color: var(--admin-chart-secondary); stop-opacity: 0" />
              </linearGradient>
            </defs>

            <line
              v-for="level in [0, 1, 2, 3]"
              :key="level"
              :x1="CHART_PAD_X"
              :x2="CHART_WIDTH - CHART_PAD_X"
              :y1="CHART_PAD_TOP + ((CHART_HEIGHT - CHART_PAD_TOP - CHART_PAD_BOTTOM) * level) / 3"
              :y2="CHART_PAD_TOP + ((CHART_HEIGHT - CHART_PAD_TOP - CHART_PAD_BOTTOM) * level) / 3"
              class="chart-grid"
            />

            <line
              v-if="activePoint"
              :x1="activePoint.x"
              :x2="activePoint.x"
              :y1="CHART_PAD_TOP"
              :y2="CHART_HEIGHT - CHART_PAD_BOTTOM"
              class="chart-guide"
            />

            <path v-if="pvAreaPath" :d="pvAreaPath" fill="url(#editorialAreaPv)" />
            <path v-if="uvAreaPath" :d="uvAreaPath" fill="url(#editorialAreaUv)" />
            <path v-if="pvLinePath" :d="pvLinePath" class="chart-line is-pv" />
            <path v-if="uvLinePath" :d="uvLinePath" class="chart-line is-uv" />

            <circle
              v-for="(pt, idx) in pvPoints"
              :key="`pv-${idx}`"
              :cx="pt.x"
              :cy="pt.y"
              :r="hoveredIndex === idx ? 5 : 3"
              class="chart-dot is-pv"
            />
            <circle
              v-for="(pt, idx) in uvPoints"
              :key="`uv-${idx}`"
              :cx="pt.x"
              :cy="pt.y"
              :r="hoveredIndex === idx ? 4.5 : 2.5"
              class="chart-dot is-uv"
            />

            <rect
              v-for="(pt, idx) in pvPoints"
              :key="`hit-${idx}`"
              :x="pt.x - CHART_WIDTH / Math.max(trend.length * 2, 2)"
              :y="0"
              :width="CHART_WIDTH / Math.max(trend.length, 1)"
              :height="CHART_HEIGHT"
              fill="transparent"
              style="cursor: pointer"
              @mouseenter="hoveredIndex = idx"
            />
          </svg>

          <div class="chart-dates admin-mono">
            <span
              v-for="(item, idx) in trend"
              :key="item.date"
              :class="{ 'is-hovered': hoveredIndex === idx }"
            >
              {{ formatDate(item.date) }}
            </span>
          </div>
        </div>
        <el-empty v-else description="暂无访问数据，浏览前台后将自动记录" :image-size="64" />
      </article>

      <aside class="admin-surface panel-card shortcut-card">
        <header class="panel-head">
          <h2>快捷创作</h2>
        </header>
        <div class="shortcut-list">
          <button
            v-for="item in shortcuts"
            :key="item.path"
            type="button"
            class="shortcut-row"
            @click="goToShortcut(item.path)"
          >
            <span class="shortcut-copy">
              <strong>{{ item.label }}</strong>
              <small>{{ item.desc }}</small>
            </span>
            <el-icon class="shortcut-arrow"><ArrowRight /></el-icon>
          </button>
        </div>
        <footer class="shortcut-footer">
          <span>资源下载</span>
          <strong class="admin-mono">
            图书 {{ overview?.book_downloads ?? '--' }} · ZIP {{ overview?.zip_downloads ?? '--' }}
          </strong>
        </footer>
      </aside>
    </section>

    <!-- 底层双列数据表：热门页面 + 最近访客 -->
    <section class="dashboard-bottom-grid">
      <article class="admin-surface panel-card">
        <header class="panel-head">
          <h2>热门页面</h2>
        </header>
        <div v-if="pages.length" class="mini-table-wrap">
          <table class="editorial-table">
            <thead>
              <tr>
                <th>页面</th>
                <th class="num-col">PV</th>
                <th class="num-col">UV</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in pages.slice(0, 6)" :key="row.path">
                <td class="page-cell">
                  <div class="page-title-line">{{ row.title || row.path }}</div>
                  <div class="page-path-line admin-mono">{{ row.path }}</div>
                  <div class="page-bar-track">
                    <span
                      class="page-bar-fill"
                      :style="{ width: `${Math.max(4, Math.round((row.pv / maxPagePv) * 100))}%` }"
                    ></span>
                  </div>
                </td>
                <td class="num-col admin-mono">{{ row.pv }}</td>
                <td class="num-col admin-mono muted-num">{{ row.uv }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <el-empty v-else description="暂无热门页面数据" :image-size="56" />
      </article>

      <article class="admin-surface panel-card">
        <header class="panel-head">
          <h2>最近访客</h2>
          <el-button link type="primary" size="small" @click="router.push('/admin/analytics/visitors')">
            查看全部
          </el-button>
        </header>
        <div v-if="visitors.length" class="mini-table-wrap">
          <table class="editorial-table">
            <thead>
              <tr>
                <th>时间</th>
                <th>事件</th>
                <th>路径</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in visitors.slice(0, 6)" :key="row.id">
                <td class="admin-mono time-col">{{ formatShortTime(row.occurred_at) }}</td>
                <td><span class="event-pill">{{ eventLabel(row.event_type) }}</span></td>
                <td class="path-col admin-mono" :title="row.path">{{ row.path }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <el-empty v-else description="暂无访问记录" :image-size="56" />
      </article>
    </section>
  </div>
</template>

<style scoped>
.kpi-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.kpi-cell {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 20px 24px;
  border-right: 1px solid var(--admin-border-color);
}

.kpi-cell:last-child {
  border-right: 0;
}

.kpi-label {
  color: var(--admin-text-secondary);
  font-size: 12.5px;
  font-weight: 500;
}

.kpi-value-row {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.kpi-value {
  color: var(--admin-text-color);
  font-size: clamp(24px, 2.4vw, 30px);
  font-weight: 700;
  letter-spacing: -0.03em;
  line-height: 1.1;
}

.kpi-delta {
  font-family: var(--admin-font-mono);
  font-size: 12px;
  font-weight: 600;
}

.kpi-delta.is-up {
  color: var(--admin-success-color);
}

.kpi-delta.is-down {
  color: var(--admin-danger-color);
}

.kpi-delta.is-flat {
  color: var(--admin-text-muted);
}

.dashboard-main-grid {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(260px, 1fr);
  gap: 18px;
}

.dashboard-bottom-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.panel-card {
  display: flex;
  flex-direction: column;
  padding: 18px 20px;
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.panel-head h2 {
  margin: 0;
  color: var(--admin-text-color);
  font-size: 15px;
  font-weight: 650;
}

.panel-sub {
  margin: 3px 0 0;
  color: var(--admin-text-muted);
  font-size: 12px;
}

.chart-legend {
  display: inline-flex;
  align-items: center;
  gap: 14px;
  color: var(--admin-text-secondary);
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

.legend-dot.is-pv {
  background: var(--admin-primary-color);
}

.legend-dot.is-uv {
  background: var(--admin-chart-secondary);
}

.chart-body {
  position: relative;
}

.chart-tooltip {
  position: absolute;
  top: 4px;
  transform: translateX(-50%);
  z-index: 2;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 5px 10px;
  border: 1px solid var(--admin-border-color);
  border-radius: 8px;
  background: var(--admin-panel-bg);
  box-shadow: var(--admin-shadow-hover);
  font-size: 11.5px;
  color: var(--admin-text-secondary);
  pointer-events: none;
}

.chart-tooltip strong {
  color: var(--admin-primary-color);
}

.chart-tooltip small {
  color: var(--admin-chart-secondary);
  font-size: 11.5px;
}

.trend-svg {
  display: block;
  width: 100%;
  height: 210px;
  overflow: visible;
}

.chart-grid {
  stroke: var(--admin-border-color);
  stroke-dasharray: 3 4;
  stroke-width: 1;
}

.chart-guide {
  stroke: var(--admin-border-strong);
  stroke-dasharray: 3 3;
  stroke-width: 1;
}

.chart-line {
  fill: none;
  stroke-width: 2.2;
  stroke-linecap: round;
  vector-effect: non-scaling-stroke;
}

.chart-line.is-pv {
  stroke: var(--admin-primary-color);
}

.chart-line.is-uv {
  stroke: var(--admin-chart-secondary);
}

.chart-dot {
  stroke: var(--admin-panel-bg);
  stroke-width: 2;
  transition: r 120ms ease;
}

.chart-dot.is-pv {
  fill: var(--admin-primary-color);
}

.chart-dot.is-uv {
  fill: var(--admin-chart-secondary);
}

.chart-dates {
  display: flex;
  justify-content: space-between;
  padding: 8px 6px 0;
  color: var(--admin-text-muted);
  font-size: 11px;
}

.chart-dates .is-hovered {
  color: var(--admin-text-color);
  font-weight: 600;
}

.shortcut-card {
  justify-content: space-between;
}

.shortcut-list {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.shortcut-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  width: 100%;
  padding: 11px 6px;
  border: 0;
  border-bottom: 1px solid var(--admin-border-color);
  background: transparent;
  color: var(--admin-text-color);
  text-align: left;
  cursor: pointer;
  transition: background-color 140ms ease;
}

.shortcut-row:last-child {
  border-bottom: 0;
}

.shortcut-row:hover {
  background: var(--admin-panel-subtle);
}

.shortcut-copy {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.shortcut-copy strong {
  font-size: 13.5px;
  font-weight: 600;
}

.shortcut-copy small {
  color: var(--admin-text-muted);
  font-size: 11.5px;
}

.shortcut-arrow {
  color: var(--admin-text-muted);
  font-size: 13px;
}

.shortcut-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--admin-border-color);
  color: var(--admin-text-secondary);
  font-size: 12px;
}

.shortcut-footer strong {
  color: var(--admin-text-color);
  font-weight: 600;
}

.mini-table-wrap {
  overflow-x: auto;
}

.editorial-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.editorial-table th {
  padding: 0 6px 10px;
  border-bottom: 1px solid var(--admin-border-color);
  color: var(--admin-text-muted);
  font-size: 11.5px;
  font-weight: 600;
  text-align: left;
}

.editorial-table td {
  padding: 10px 6px;
  border-bottom: 1px solid var(--admin-border-color);
  color: var(--admin-text-color);
  vertical-align: middle;
}

.editorial-table tr:last-child td {
  border-bottom: 0;
}

.editorial-table .num-col {
  width: 64px;
  text-align: right;
  font-weight: 600;
}

.muted-num {
  color: var(--admin-text-secondary);
  font-weight: 500;
}

.page-cell {
  max-width: 280px;
}

.page-title-line {
  font-weight: 550;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.page-path-line {
  margin-top: 2px;
  color: var(--admin-text-muted);
  font-size: 11.5px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.page-bar-track {
  height: 3px;
  margin-top: 6px;
  border-radius: 999px;
  background: var(--admin-fill-bg);
  overflow: hidden;
}

.page-bar-fill {
  display: block;
  height: 100%;
  border-radius: 999px;
  background: var(--admin-primary-color);
  opacity: 0.72;
}

.time-col {
  width: 66px;
  color: var(--admin-text-secondary);
  font-size: 12px;
}

.event-pill {
  display: inline-flex;
  align-items: center;
  height: 22px;
  padding: 0 8px;
  border-radius: 6px;
  background: var(--admin-fill-bg);
  color: var(--admin-text-secondary);
  font-size: 11.5px;
  white-space: nowrap;
}

.path-col {
  max-width: 240px;
  color: var(--admin-text-secondary);
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 1080px) {
  .kpi-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .kpi-cell:nth-child(2) {
    border-right: 0;
  }

  .kpi-cell:nth-child(1),
  .kpi-cell:nth-child(2) {
    border-bottom: 1px solid var(--admin-border-color);
  }

  .dashboard-main-grid,
  .dashboard-bottom-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .kpi-cell {
    padding: 15px 16px;
  }
}
</style>
