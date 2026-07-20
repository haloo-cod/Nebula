<script setup lang="ts">
/** 管理后台访问记录页面，原始 IP 仅对管理员展示。 */
import { onMounted, ref } from 'vue'
import { Search, Refresh } from '@element-plus/icons-vue'
import { api } from '@/api/client'

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

interface VisitorResponse {
  items: VisitorItem[]
  total: number
}

const rows = ref<VisitorItem[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(30)
const total = ref(0)
const ip = ref('')
const eventType = ref('')

const eventOptions = [
  { label: '全部事件', value: '' },
  { label: '页面访问', value: 'page_view' },
  { label: '打开图书', value: 'book_open' },
  { label: '下载图书', value: 'book_download' },
  { label: '下载文件', value: 'file_download' },
  { label: '下载 ZIP', value: 'zip_download' },
]

function eventLabel(value: string): string {
  return eventOptions.find((option) => option.value === value)?.label ?? value
}

function formatDateTime(value: string): string {
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value.replace('T', ' ').slice(0, 19) : date.toLocaleString()
}

async function loadVisitors() {
  loading.value = true
  const params = new URLSearchParams({
    page: String(page.value),
    page_size: String(pageSize.value),
  })
  if (ip.value.trim()) params.set('ip', ip.value.trim())
  if (eventType.value) params.set('event_type', eventType.value)
  try {
    const data = await api.get<VisitorResponse>(`/api/v1/analytics/visitors?${params}`, true)
    rows.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function search() {
  page.value = 1
  void loadVisitors()
}

function reset() {
  ip.value = ''
  eventType.value = ''
  search()
}

onMounted(() => void loadVisitors())
</script>

<template>
  <div class="visitor-page">
    <div class="page-header">
      <div>
        <h2>访问记录</h2>
        <p>查看访问事件、访客 IP 和请求来源。</p>
      </div>
      <el-button :icon="Refresh" :loading="loading" @click="loadVisitors">刷新</el-button>
    </div>

    <el-card shadow="never" class="filter-card">
      <el-form inline @submit.prevent="search">
        <el-form-item label="IP 地址">
          <el-input v-model="ip" clearable placeholder="精确匹配 IP" @keyup.enter="search" />
        </el-form-item>
        <el-form-item label="事件类型">
          <el-select v-model="eventType" style="width: 150px">
            <el-option
              v-for="option in eventOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="search">查询</el-button>
          <el-button @click="reset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never" class="table-card">
      <el-table v-loading="loading" :data="rows" stripe>
        <el-table-column prop="occurred_at" label="时间" width="180">
          <template #default="{ row }">{{ formatDateTime(row.occurred_at) }}</template>
        </el-table-column>
        <el-table-column prop="ip_address" label="IP 地址" width="150" />
        <el-table-column label="事件" width="110">
          <template #default="{ row }">{{ eventLabel(row.event_type) }}</template>
        </el-table-column>
        <el-table-column label="页面" min-width="220" show-overflow-tooltip>
          <template #default="{ row }">
            <span>{{ row.title || row.path }}</span>
            <small>{{ row.path }}</small>
          </template>
        </el-table-column>
        <el-table-column prop="referrer" label="来源" min-width="180" show-overflow-tooltip />
        <el-table-column
          prop="user_agent"
          label="User-Agent"
          min-width="240"
          show-overflow-tooltip
        />
      </el-table>
      <el-empty v-if="!loading && rows.length === 0" description="暂无访问记录" :image-size="80" />
      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          background
          layout="total, sizes, prev, pager, next"
          :total="total"
          @current-change="loadVisitors"
          @size-change="search"
        />
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.visitor-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header,
.card-header-with-action {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.page-header h2 {
  margin: 0 0 6px;
  color: var(--admin-text-color, #303133);
  font-size: 20px;
}

.page-header p {
  margin: 0;
  color: var(--admin-text-secondary, #909399);
  font-size: 13px;
}

.filter-card,
.table-card {
  border-radius: 12px;
}

.filter-card :deep(.el-form-item) {
  margin-bottom: 0;
}

.table-card small {
  display: block;
  overflow: hidden;
  color: var(--admin-text-secondary, #909399);
  font-size: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

@media (max-width: 700px) {
  .page-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .pagination-wrap {
    justify-content: center;
    overflow-x: auto;
  }
}
</style>
