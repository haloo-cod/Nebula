<script setup lang="ts">
/** 管理后台访问记录页面，原始 IP 仅对管理员展示。 */
import { onMounted, ref } from 'vue'
import { Search, Refresh } from '@element-plus/icons-vue'
import { api } from '@/api/client'
import AdminPageHeader from '@/admin/components/AdminPageHeader.vue'

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
  const normalized = /[+\-]\d{2}:\d{2}$/.test(value) || value.endsWith('Z') ? value : value + 'Z'
  const date = new Date(normalized)
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
  <div class="admin-page">
    <AdminPageHeader
      eyebrow="ANALYTICS"
      title="访问记录"
      :count="`${total} 条`"
      subtitle="按 IP 与事件类型检索站点访问日志与请求来源。"
    >
      <template #actions>
        <el-button :icon="Refresh" :loading="loading" @click="loadVisitors">刷新</el-button>
      </template>
    </AdminPageHeader>

    <div class="admin-toolbar">
      <div class="admin-toolbar-group">
        <el-input
          v-model="ip"
          clearable
          placeholder="精确匹配访客 IP..."
          style="width: 220px"
          @keyup.enter="search"
        />
        <el-select v-model="eventType" style="width: 150px" @change="search">
          <el-option
            v-for="option in eventOptions"
            :key="option.value"
            :label="option.label"
            :value="option.value"
          />
        </el-select>
        <el-button type="primary" :icon="Search" @click="search">查询</el-button>
        <el-button v-if="ip || eventType" @click="reset">重置</el-button>
      </div>
    </div>

    <el-card shadow="never" class="table-card">
      <el-table v-loading="loading" :data="rows">
        <el-table-column prop="occurred_at" label="时间" width="175">
          <template #default="{ row }">
            <span class="admin-mono">{{ formatDateTime(row.occurred_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="ip_address" label="IP 地址" width="150">
          <template #default="{ row }">
            <span class="admin-mono">{{ row.ip_address }}</span>
          </template>
        </el-table-column>
        <el-table-column label="事件" width="110">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ eventLabel(row.event_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="页面" min-width="220" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="visitor-title">{{ row.title || row.path }}</span>
            <small class="visitor-path admin-mono">{{ row.path }}</small>
          </template>
        </el-table-column>
        <el-table-column prop="referrer" label="来源" min-width="180" show-overflow-tooltip />
        <el-table-column prop="user_agent" label="User-Agent" min-width="220" show-overflow-tooltip />
      </el-table>
      <el-empty v-if="!loading && rows.length === 0" description="暂无访问记录" :image-size="72" />
      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
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
.visitor-title {
  display: block;
  font-weight: 550;
}

.visitor-path {
  display: block;
  overflow: hidden;
  color: var(--admin-text-muted);
  font-size: 11.5px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
