<script setup lang="ts">
/**
 * R2 迁移管理面板
 * 展示各表迁移状态统计，支持按表查看待迁移资源并批量迁移到 R2。
 */
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { resolveUrl, api } from '@/api/client'
import {
  getMigrationStatus,
  migrateFiles,
  migrateImages,
  migrateBackgrounds,
  migrateBooks,
  type MigrationStatus,
  type MigrateResponse,
} from '@/api/r2Migration'
import { fetchImages } from '@/api/images'
import { fetchFiles } from '@/api/files'

/** 图床图片记录（迁移面板只用到部分字段） */
interface MigrationImage {
  id: number
  filename: string
  original_name: string
  url: string
  file_size: number
  width: number
  height: number
  created_at: string
}

/** 通用文件记录（迁移面板只用到部分字段） */
interface MigrationFile {
  id: number
  filename: string
  original_name: string
  url: string
  file_size: number
  mime_type: string
  created_at: string
}

/** 背景记录（迁移面板只用到部分字段；仅视频背景会出现在迁移列表） */
interface MigrationBackground {
  id: number
  url: string
  media_type: 'image' | 'video'
  mime_type?: string
  file_size?: number
  theme: string
  device: string
  created_at: string
  storage_backend?: string
}

/** 图书记录（迁移面板只用到部分字段） */
interface MigrationBook {
  id: number
  slug: string
  title: string
  author: string
  cover_url: string
  file_size?: number
  created_at: string
  storage_backend?: string
}

/** 当前迁移 tab 对应的资源类型 */
type ResourceType = 'images' | 'files' | 'backgrounds' | 'books'

const loading = ref(false)
const migrating = ref(false)
const status = ref<MigrationStatus | null>(null)
const activeTab = ref<ResourceType>('images')

// 待迁移列表状态（按 tab 独立缓存）
const pendingLists = reactive<{
  images: MigrationImage[]
  files: MigrationFile[]
  backgrounds: MigrationBackground[]
  books: MigrationBook[]
}>({
  images: [],
  files: [],
  backgrounds: [],
  books: [],
})
const listLoading = ref(false)
const selectedImageIds = ref<number[]>([])
const selectedFileIds = ref<number[]>([])
const selectedBackgroundIds = ref<number[]>([])
const selectedBookIds = ref<number[]>([])

const pendingImages = computed(() => pendingLists.images)
const pendingFiles = computed(() => pendingLists.files)
const pendingBackgrounds = computed(() => pendingLists.backgrounds)
const pendingBooks = computed(() => pendingLists.books)
/** 当前 tab 展示的待迁移列表。 */
const currentPendingList = computed(() => {
  switch (activeTab.value) {
    case 'images':
      return pendingImages.value
    case 'files':
      return pendingFiles.value
    case 'backgrounds':
      return pendingBackgrounds.value
    case 'books':
      return pendingBooks.value
  }
})
/** 各 tab 的空态文案。 */
const emptyDescriptions: Record<ResourceType, string> = {
  images: '没有待迁移的本地图片',
  files: '没有待迁移的本地文件',
  backgrounds: '没有待迁移的本地背景视频',
  books: '没有待迁移的本地图书',
}
const selectedCount = computed(() => {
  switch (activeTab.value) {
    case 'images':
      return selectedImageIds.value.length
    case 'files':
      return selectedFileIds.value.length
    case 'backgrounds':
      return selectedBackgroundIds.value.length
    case 'books':
      return selectedBookIds.value.length
  }
})

const statusCards = computed(() => {
  if (!status.value) return []
  return [
    { key: 'images', title: '图床图片', ...status.value.images },
    { key: 'files', title: '通用文件', ...status.value.files },
    { key: 'backgrounds', title: '背景视频', ...status.value.backgrounds },
    { key: 'books', title: '图书 EPUB', ...status.value.books },
  ]
})

function formatSize(size: number): string {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

/** 加载迁移状态统计。 */
async function loadStatus() {
  loading.value = true
  try {
    status.value = await getMigrationStatus()
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '加载迁移状态失败')
  } finally {
    loading.value = false
  }
}

/** 加载当前 tab 的待迁移（local）资源列表。 */
async function loadPendingList() {
  listLoading.value = true
  selectedImageIds.value = []
  selectedFileIds.value = []
  selectedBackgroundIds.value = []
  selectedBookIds.value = []
  try {
    if (activeTab.value === 'images') {
      // 待迁移 = storage_backend 为 local 的图片，取前 100 条
      const res = await fetchImages(1, 100, 'local')
      pendingLists.images = res.items
    } else if (activeTab.value === 'files') {
      pendingLists.files = await fetchFiles(1, 100, 'local')
    } else if (activeTab.value === 'backgrounds') {
      // 仅视频背景由本面板迁移；图片背景随图床图片迁移
      const res = await api.get<{ items: MigrationBackground[]; total: number }>(
        '/api/v1/backgrounds',
        true,
      )
      pendingLists.backgrounds = res.items.filter(
        (item) => item.media_type === 'video' && item.storage_backend !== 'r2',
      )
    } else {
      const res = await api.get<{ items: MigrationBook[]; total: number }>(
        '/api/v1/books?page=1&page_size=100&storage_backend=local',
        true,
      )
      pendingLists.books = res.items
    }
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '加载待迁移列表失败')
  } finally {
    listLoading.value = false
  }
}

/** tab 切换时按需加载对应列表。 */
function handleTabChange(tab: string | number) {
  if (tab === 'images' && pendingLists.images.length === 0) void loadPendingList()
  if (tab === 'files' && pendingLists.files.length === 0) void loadPendingList()
  if (tab === 'backgrounds' && pendingLists.backgrounds.length === 0) void loadPendingList()
  if (tab === 'books' && pendingLists.books.length === 0) void loadPendingList()
}

/** 迁移结果统一提示。 */
function reportMigrationResult(result: MigrateResponse, label: string) {
  if (result.failed_count === 0) {
    ElMessage.success(`${label}迁移完成：${result.success_count} 项成功`)
  } else {
    const detail = result.errors.slice(0, 3).join('；')
    ElMessage.warning(
      `${label}迁移：${result.success_count} 项成功，${result.failed_count} 项失败${detail ? `（${detail}…）` : ''}`,
    )
  }
}

/** 批量迁移选中的图片到 R2。 */
async function handleMigrateImages() {
  if (!selectedImageIds.value.length) {
    ElMessage.warning('请先勾选要迁移的图片')
    return
  }
  migrating.value = true
  try {
    const result = await migrateImages(selectedImageIds.value)
    reportMigrationResult(result, '图片')
    await Promise.all([loadStatus(), loadPendingList()])
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '图片迁移失败')
  } finally {
    migrating.value = false
  }
}

/** 批量迁移选中的文件到 R2。 */
async function handleMigrateFiles() {
  if (!selectedFileIds.value.length) {
    ElMessage.warning('请先勾选要迁移的文件')
    return
  }
  migrating.value = true
  try {
    const result = await migrateFiles(selectedFileIds.value)
    reportMigrationResult(result, '文件')
    await Promise.all([loadStatus(), loadPendingList()])
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '文件迁移失败')
  } finally {
    migrating.value = false
  }
}

/** 批量迁移选中的背景视频到 R2。 */
async function handleMigrateBackgrounds() {
  if (!selectedBackgroundIds.value.length) {
    ElMessage.warning('请先勾选要迁移的背景视频')
    return
  }
  migrating.value = true
  try {
    const result = await migrateBackgrounds(selectedBackgroundIds.value)
    reportMigrationResult(result, '背景视频')
    await Promise.all([loadStatus(), loadPendingList()])
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '背景视频迁移失败')
  } finally {
    migrating.value = false
  }
}

/** 批量迁移选中的图书 EPUB 到 R2。 */
async function handleMigrateBooks() {
  if (!selectedBookIds.value.length) {
    ElMessage.warning('请先勾选要迁移的图书')
    return
  }
  migrating.value = true
  try {
    const result = await migrateBooks(selectedBookIds.value)
    reportMigrationResult(result, '图书')
    await Promise.all([loadStatus(), loadPendingList()])
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '图书迁移失败')
  } finally {
    migrating.value = false
  }
}

/** 当前 tab 的中文标签。 */
const tabLabels: Record<ResourceType, string> = {
  images: '图片',
  files: '文件',
  backgrounds: '背景视频',
  books: '图书',
}

/** 确认后批量迁移当前 tab 选中的资源。 */
async function handleMigrate() {
  const label = tabLabels[activeTab.value]
  try {
    await ElMessageBox.confirm(
      `确定将选中的 ${selectedCount.value} 个${label}迁移到 R2？迁移后新地址由 R2 提供。`,
      '确认迁移',
      { type: 'warning' },
    )
  } catch {
    return // 用户取消
  }
  if (activeTab.value === 'images') await handleMigrateImages()
  else if (activeTab.value === 'files') await handleMigrateFiles()
  else if (activeTab.value === 'backgrounds') await handleMigrateBackgrounds()
  else await handleMigrateBooks()
}

onMounted(async () => {
  await loadStatus()
  // 默认 tab 直接加载待迁移图片
  void loadPendingList()
})
</script>

<template>
  <div class="r2-migration-page">
    <div class="page-header">
      <div>
        <h2>R2 存储迁移</h2>
        <p>将本地存储的图片、文件、背景视频和图书 EPUB 批量迁移到 Cloudflare R2 对象存储。</p>
      </div>
      <el-button :icon="Refresh" :loading="loading" @click="loadStatus">刷新状态</el-button>
    </div>

    <el-alert
      v-if="status && !status.r2_enabled"
      title="R2 未启用"
      description="后端未开启 R2（检查环境变量 R2_ENABLED 与密钥配置），迁移功能暂不可用。"
      type="warning"
      show-icon
      :closable="false"
    />

    <!-- 迁移状态统计卡片 -->
    <div v-loading="loading" class="status-grid">
      <el-card v-for="card in statusCards" :key="card.key" shadow="never" class="status-card">
        <div class="status-card-title">{{ card.title }}</div>
        <el-progress
          :percentage="card.total ? Math.round((card.migrated / card.total) * 100) : 100"
          :stroke-width="10"
          :status="card.pending === 0 ? 'success' : undefined"
        />
        <div class="status-card-meta">
          <span>已迁移 {{ card.migrated }} / {{ card.total }}</span>
          <span :class="{ pending: card.pending > 0 }">待迁移 {{ card.pending }}</span>
        </div>
      </el-card>
    </div>

    <!-- 待迁移列表 -->
    <el-card shadow="never" class="table-card">
      <template #header>
        <div class="table-card-header">
          <el-tabs v-model="activeTab" @tab-change="handleTabChange">
            <el-tab-pane label="待迁移图片" name="images" />
            <el-tab-pane label="待迁移文件" name="files" />
            <el-tab-pane label="待迁移背景视频" name="backgrounds" />
            <el-tab-pane label="待迁移图书" name="books" />
          </el-tabs>
          <div class="table-actions">
            <el-button :disabled="listLoading" @click="loadPendingList">刷新列表</el-button>
            <el-button
              type="primary"
              :loading="migrating"
              :disabled="!status?.r2_enabled || selectedCount === 0"
              @click="handleMigrate"
            >
              迁移选中（{{ selectedCount }}）
            </el-button>
          </div>
        </div>
      </template>

      <el-table
        v-if="activeTab === 'images'"
        :data="pendingImages"
        v-loading="listLoading"
        stripe
        @selection-change="(rows: MigrationImage[]) => (selectedImageIds = rows.map((r) => r.id))"
      >
        <el-table-column type="selection" width="50" />
        <el-table-column label="预览" width="90">
          <template #default="{ row }">
            <img :src="resolveUrl(row.url)" :alt="row.original_name" class="image-preview" />
          </template>
        </el-table-column>
        <el-table-column prop="original_name" label="文件名" min-width="200" show-overflow-tooltip />
        <el-table-column prop="mime_type" label="类型" min-width="120" show-overflow-tooltip />
        <el-table-column label="尺寸" width="120">
          <template #default="{ row }">{{ row.width }} × {{ row.height }}</template>
        </el-table-column>
        <el-table-column label="大小" width="100">
          <template #default="{ row }">{{ formatSize(row.file_size) }}</template>
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" width="110">
          <template #default="{ row }">{{ row.created_at?.slice(0, 10) }}</template>
        </el-table-column>
      </el-table>

      <el-table
        v-else-if="activeTab === 'files'"
        :data="pendingFiles"
        v-loading="listLoading"
        stripe
        @selection-change="(rows: MigrationFile[]) => (selectedFileIds = rows.map((r) => r.id))"
      >
        <el-table-column type="selection" width="50" />
        <el-table-column prop="original_name" label="文件名" min-width="240" show-overflow-tooltip />
        <el-table-column prop="mime_type" label="类型" min-width="160" show-overflow-tooltip />
        <el-table-column label="大小" width="110">
          <template #default="{ row }">{{ formatSize(row.file_size) }}</template>
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" width="110">
          <template #default="{ row }">{{ row.created_at?.slice(0, 10) }}</template>
        </el-table-column>
      </el-table>

      <el-table
        v-else-if="activeTab === 'backgrounds'"
        :data="pendingBackgrounds"
        v-loading="listLoading"
        stripe
        @selection-change="
          (rows: MigrationBackground[]) => (selectedBackgroundIds = rows.map((r) => r.id))
        "
      >
        <el-table-column type="selection" width="50" />
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column label="分组" width="130">
          <template #default="{ row }">
            {{ row.theme === 'dark' ? '暗色' : '亮色' }} ·
            {{ row.device === 'desktop' ? '桌面' : '移动' }}
          </template>
        </el-table-column>
        <el-table-column prop="url" label="视频地址" min-width="240" show-overflow-tooltip />
        <el-table-column prop="mime_type" label="类型" min-width="140" show-overflow-tooltip />
        <el-table-column label="大小" width="110">
          <template #default="{ row }">{{ formatSize(row.file_size ?? 0) }}</template>
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" width="110">
          <template #default="{ row }">{{ row.created_at?.slice(0, 10) }}</template>
        </el-table-column>
      </el-table>

      <el-table
        v-else
        :data="pendingBooks"
        v-loading="listLoading"
        stripe
        @selection-change="(rows: MigrationBook[]) => (selectedBookIds = rows.map((r) => r.id))"
      >
        <el-table-column type="selection" width="50" />
        <el-table-column label="封面" width="80">
          <template #default="{ row }">
            <img v-if="row.cover_url" :src="resolveUrl(row.cover_url)" class="book-preview" alt="" />
          </template>
        </el-table-column>
        <el-table-column prop="title" label="书名" min-width="180" show-overflow-tooltip />
        <el-table-column prop="author" label="作者" min-width="120" show-overflow-tooltip />
        <el-table-column prop="slug" label="Slug" min-width="140" show-overflow-tooltip />
        <el-table-column prop="created_at" label="上传时间" width="110">
          <template #default="{ row }">{{ row.created_at?.slice(0, 10) }}</template>
        </el-table-column>
      </el-table>

      <el-empty
        v-if="!listLoading && currentPendingList.length === 0"
        :description="emptyDescriptions[activeTab]"
      />
    </el-card>
  </div>
</template>

<style scoped>
.r2-migration-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}
.page-header h2 {
  margin: 0;
  color: var(--admin-text-color);
  font-size: 20px;
}
.page-header p {
  margin: 4px 0 0;
  color: var(--admin-text-secondary);
  font-size: 13px;
}
.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
  min-height: 120px;
}
.status-card {
  border-radius: 12px;
}
.status-card-title {
  margin-bottom: 12px;
  font-weight: 600;
  color: var(--admin-text-color);
}
.status-card-meta {
  display: flex;
  justify-content: space-between;
  margin-top: 10px;
  font-size: 12px;
  color: var(--admin-text-secondary);
}
.status-card-meta .pending {
  color: var(--el-color-warning);
}
.table-card {
  border-radius: 12px;
}
.table-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
}
.table-card-header :deep(.el-tabs) {
  flex: 1;
  min-width: 220px;
}
.table-card-header :deep(.el-tabs__header) {
  margin-bottom: 0;
}
.table-actions {
  display: flex;
  gap: 8px;
}
.image-preview {
  width: 64px;
  height: 44px;
  object-fit: cover;
  border-radius: 4px;
}
.book-preview {
  width: 36px;
  height: 50px;
  object-fit: cover;
  border-radius: 3px;
}
</style>
