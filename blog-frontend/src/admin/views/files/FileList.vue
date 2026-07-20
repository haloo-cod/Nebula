<script setup lang="ts">
/** 通用文件管理：上传、下载与删除后台资源。 */
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, Download, Refresh, Upload } from '@element-plus/icons-vue'
import { api, BASE_URL, getToken } from '@/api/client'
import { uploadFile, type UploadedFile } from '@/api/files'

/** 图床图片记录。 */
interface UploadedImage {
  id: number
  filename: string
  original_name: string
  url: string
  file_size: number
  width: number
  height: number
  mime_type: string
  created_at: string
}

/** 图书 ZIP 打包历史。 */
interface BookDownloadJob {
  id: number
  status: string
  total_books: number
  completed_books: number
  progress: number
  file_size: number
  error_message: string
  expires_at: string | null
  download_url: string | null
  created_at: string
}

const files = ref<UploadedFile[]>([])
const images = ref<UploadedImage[]>([])
const archives = ref<BookDownloadJob[]>([])
const activeTab = ref('files')
const loading = ref(false)
const uploading = ref(false)
const uploadProgress = ref(0)
const fileInput = ref<HTMLInputElement | null>(null)

function formatSize(size: number): string {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  if (size < 1024 * 1024 * 1024) return `${(size / 1024 / 1024).toFixed(1)} MB`
  return `${(size / 1024 / 1024 / 1024).toFixed(1)} GB`
}

function formatDateTime(value: string | null): string {
  if (!value) return '--'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value.replace('T', ' ').slice(0, 19)
  return date.toLocaleString()
}

async function loadFiles() {
  loading.value = true
  try {
    const response = await api.get<{ items: UploadedFile[]; total: number }>(
      '/api/v1/files?page=1&page_size=200',
      true,
    )
    files.value = response.items
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '加载文件失败')
  } finally {
    loading.value = false
  }
}

async function loadImages() {
  loading.value = true
  try {
    const response = await api.get<{ items: UploadedImage[]; total: number }>(
      '/api/v1/images?page=1&page_size=100',
      true,
    )
    images.value = response.items
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '加载图片失败')
  } finally {
    loading.value = false
  }
}

async function loadArchives() {
  loading.value = true
  try {
    const response = await api.get<{ items: BookDownloadJob[]; total: number }>(
      '/api/v1/books/download-jobs?page=1&page_size=100',
      true,
    )
    archives.value = response.items
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '加载图书归档失败')
  } finally {
    loading.value = false
  }
}

function openPicker() {
  if (!uploading.value) fileInput.value?.click()
}

async function handleUpload(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  uploading.value = true
  uploadProgress.value = 0
  try {
    if (activeTab.value === 'files') {
      await uploadFile(file, (percent) => (uploadProgress.value = percent))
      await loadFiles()
    } else {
      const formData = new FormData()
      formData.append('file', file)
      const response = await fetch(`${BASE_URL}/api/v1/images/upload`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${getToken() ?? ''}` },
        body: formData,
        credentials: 'include',
      })
      if (!response.ok) {
        const body = await response.json().catch(() => ({ detail: '图片上传失败' }))
        throw new Error(body.detail || '图片上传失败')
      }
      await loadImages()
    }
    ElMessage.success(activeTab.value === 'files' ? '文件上传成功' : '图片上传成功')
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '文件上传失败')
  } finally {
    uploading.value = false
    input.value = ''
  }
}

async function downloadFile(file: UploadedFile) {
  try {
    const response = await fetch(`${BASE_URL}${file.url}`, {
      headers: { Authorization: `Bearer ${getToken() ?? ''}` },
      credentials: 'include',
    })
    if (!response.ok) throw new Error('文件下载失败')
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = file.original_name
    anchor.click()
    URL.revokeObjectURL(url)
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '文件下载失败')
  }
}

async function removeFile(file: UploadedFile) {
  try {
    await ElMessageBox.confirm(`确定删除「${file.original_name}」吗？`, '确认删除', {
      type: 'warning',
    })
    await api.delete(`/api/v1/files/${file.id}`, true)
    ElMessage.success('文件已删除')
    await loadFiles()
  } catch {
    // 用户取消删除或请求失败。
  }
}

async function downloadImage(image: UploadedImage) {
  const response = await fetch(`${BASE_URL}${image.url}`)
  if (!response.ok) {
    ElMessage.error('图片下载失败')
    return
  }
  const url = URL.createObjectURL(await response.blob())
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = image.original_name
  anchor.click()
  URL.revokeObjectURL(url)
}

async function removeImage(image: UploadedImage) {
  try {
    await ElMessageBox.confirm(`确定删除「${image.original_name}」吗？`, '确认删除', {
      type: 'warning',
    })
    await api.delete(`/api/v1/images/${image.id}`, true)
    ElMessage.success('图片已删除')
    await loadImages()
  } catch (err: unknown) {
    if (err instanceof Error && 'status' in err && (err as { status?: number }).status === 409) {
      ElMessage.warning(err.message)
    }
  }
}

async function downloadArchive(job: BookDownloadJob) {
  if (!job.download_url) return
  try {
    const response = await fetch(`${BASE_URL}${job.download_url}`, {
      headers: { Authorization: `Bearer ${getToken() ?? ''}` },
      credentials: 'include',
    })
    if (!response.ok)
      throw new Error((await response.json().catch(() => ({}))).detail || '归档下载失败')
    const url = URL.createObjectURL(await response.blob())
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = 'starlit-books.zip'
    anchor.click()
    URL.revokeObjectURL(url)
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '归档下载失败')
  }
}

async function retryArchive(job: BookDownloadJob) {
  try {
    await api.post(`/api/v1/books/download-jobs/${job.id}/retry`, undefined, true)
    ElMessage.success('已重新创建打包任务')
    await loadArchives()
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '重新打包失败')
  }
}

async function removeArchive(job: BookDownloadJob) {
  try {
    await ElMessageBox.confirm(`确定删除归档任务 #${job.id} 吗？`, '确认删除', { type: 'warning' })
    await api.delete(`/api/v1/books/download-jobs/${job.id}`, true)
    ElMessage.success('归档已删除')
    await loadArchives()
  } catch {
    // 用户取消删除或请求失败。
  }
}

function archiveStatus(status: string): string {
  return (
    {
      pending: '等待中',
      running: '打包中',
      completed: '已完成',
      failed: '失败',
      expired: '已过期',
    }[status] || status
  )
}

function handleArchiveTab() {
  if (archives.value.length === 0) void loadArchives()
}

function handleTabChange(tab: string | number) {
  if (tab === 'images' && images.value.length === 0) void loadImages()
  if (tab === 'archives') handleArchiveTab()
}

onMounted(loadFiles)
</script>

<template>
  <div class="file-list-page">
    <div class="page-header">
      <div>
        <h2>文件与媒体</h2>
        <p>统一管理普通文件和图床图片，数据库仍保持分表。</p>
      </div>
      <div class="upload-actions">
        <el-progress v-if="uploading" :percentage="uploadProgress" :stroke-width="6" />
        <el-button
          type="primary"
          :icon="Upload"
          :loading="uploading"
          @click="openPicker"
          :disabled="activeTab === 'archives'"
        >
          {{ activeTab === 'files' ? '上传文件' : '上传图片' }}
        </el-button>
        <input ref="fileInput" type="file" class="file-input" @change="handleUpload" />
      </div>
    </div>

    <el-card shadow="never" class="table-card">
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane label="普通文件" name="files" />
        <el-tab-pane label="图片" name="images" />
        <el-tab-pane label="图书归档" name="archives" />
      </el-tabs>
      <el-table v-if="activeTab === 'files'" :data="files" v-loading="loading" stripe>
        <el-table-column
          prop="original_name"
          label="文件名"
          min-width="260"
          show-overflow-tooltip
        />
        <el-table-column prop="mime_type" label="类型" min-width="180" show-overflow-tooltip />
        <el-table-column label="大小" width="120">
          <template #default="{ row }">{{ formatSize(row.file_size) }}</template>
        </el-table-column>
        <el-table-column label="上传时间" width="140">
          <template #default="{ row }">{{ row.created_at?.slice(0, 10) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              :icon="Download"
              @click="downloadFile(row as UploadedFile)"
              >下载</el-button
            >
            <el-button type="danger" link :icon="Delete" @click="removeFile(row as UploadedFile)"
              >删除</el-button
            >
          </template>
        </el-table-column>
      </el-table>
      <el-table v-else-if="activeTab === 'images'" :data="images" v-loading="loading" stripe>
        <el-table-column label="预览" width="100">
          <template #default="{ row }">
            <img :src="`${BASE_URL}${row.url}`" :alt="row.original_name" class="image-preview" />
          </template>
        </el-table-column>
        <el-table-column
          prop="original_name"
          label="文件名"
          min-width="220"
          show-overflow-tooltip
        />
        <el-table-column label="尺寸" width="130">
          <template #default="{ row }">{{ row.width }} × {{ row.height }}</template>
        </el-table-column>
        <el-table-column label="大小" width="120">
          <template #default="{ row }">{{ formatSize(row.file_size) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="170" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              :icon="Download"
              @click="downloadImage(row as UploadedImage)"
              >下载</el-button
            >
            <el-button type="danger" link :icon="Delete" @click="removeImage(row as UploadedImage)"
              >删除</el-button
            >
          </template>
        </el-table-column>
      </el-table>
      <el-table v-else :data="archives" v-loading="loading" stripe>
        <el-table-column prop="id" label="任务" width="80" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag
              :type="
                row.status === 'completed' ? 'success' : row.status === 'failed' ? 'danger' : 'info'
              "
            >
              {{ archiveStatus(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="进度" width="150">
          <template #default="{ row }"
            >{{ row.completed_books }}/{{ row.total_books }}（{{ row.progress }}%）</template
          >
        </el-table-column>
        <el-table-column label="大小" width="120">
          <template #default="{ row }">{{ formatSize(row.file_size) }}</template>
        </el-table-column>
        <el-table-column label="过期时间" min-width="180">
          <template #default="{ row }">{{ formatDateTime(row.expires_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'completed'"
              type="primary"
              link
              :icon="Download"
              @click="downloadArchive(row as BookDownloadJob)"
              >下载</el-button
            >
            <el-button
              v-if="row.status === 'failed' || row.status === 'expired'"
              type="warning"
              link
              :icon="Refresh"
              @click="retryArchive(row as BookDownloadJob)"
              >重试</el-button
            >
            <el-button
              type="danger"
              link
              :icon="Delete"
              @click="removeArchive(row as BookDownloadJob)"
              >删除</el-button
            >
          </template>
        </el-table-column>
      </el-table>
      <el-empty
        v-if="
          !loading &&
          (activeTab === 'files'
            ? files.length
            : activeTab === 'images'
              ? images.length
              : archives.length) === 0
        "
        :description="
          activeTab === 'files' ? '暂无文件' : activeTab === 'images' ? '暂无图片' : '暂无图书归档'
        "
      />
    </el-card>
  </div>
</template>

<style scoped>
.file-list-page {
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
h2 {
  margin: 0;
  color: var(--admin-text-color);
  font-size: 20px;
}
p {
  margin: 6px 0 0;
  color: var(--admin-text-secondary);
  font-size: 13px;
}
.upload-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}
.upload-actions .el-progress {
  width: 150px;
}
.file-input {
  display: none;
}
.table-card {
  background: var(--admin-panel-bg);
}
.image-preview {
  width: 64px;
  height: 44px;
  object-fit: cover;
  border-radius: 4px;
}
@media (max-width: 640px) {
  .page-header {
    align-items: flex-start;
    flex-direction: column;
  }
  .upload-actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
