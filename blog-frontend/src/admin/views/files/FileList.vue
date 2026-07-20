<script setup lang="ts">
/** 通用文件管理：上传、下载与删除后台资源。 */
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, Download, Refresh, Upload } from '@element-plus/icons-vue'
import { api, BASE_URL, getToken, resolveUrl } from '@/api/client'
import { uploadFiles, type UploadedFile } from '@/api/files'
import { downloadWithProgress } from '@/utils/download'

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
const uploadStatus = ref('')
const fileInput = ref<HTMLInputElement | null>(null)
const downloading = ref(false)
const downloadProgress = ref(0)
const downloadStatus = ref('')

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

async function copyUrl(url: string) {
  try {
    await navigator.clipboard.writeText(resolveUrl(url))
    ElMessage.success('URL 已复制')
  } catch {
    ElMessage.error('复制失败，请手动复制')
  }
}

async function handleUpload(event: Event) {
  const input = event.target as HTMLInputElement
  const selectedFiles = Array.from(input.files ?? [])
  if (!selectedFiles.length) return
  uploading.value = true
  uploadProgress.value = 0
  try {
    if (activeTab.value === 'files') {
      const results = await uploadFiles(selectedFiles, (completed, total, current) => {
        uploadProgress.value = Math.round((completed / total) * 100)
        uploadStatus.value = current ? `正在上传 ${current}` : ''
      })
      await loadFiles()
      const failed = results.filter((result) => result.error)
      if (failed.length) {
        ElMessage.warning(`${results.length - failed.length} 个成功，${failed.length} 个失败`)
      }
    } else {
      let success = 0
      let failed = 0
      for (const [index, file] of selectedFiles.entries()) {
        try {
          uploadStatus.value = `正在上传 ${file.name}`
          const formData = new FormData()
          formData.append('file', file)
          const response = await fetch(`${BASE_URL}/api/v1/images/upload`, {
            method: 'POST',
            headers: { Authorization: `Bearer ${getToken() ?? ''}` },
            body: formData,
            credentials: 'include',
          })
          if (response.ok) success++
          else failed++
        } catch {
          failed++
        }
        uploadProgress.value = Math.round(((index + 1) / selectedFiles.length) * 100)
      }
      await loadImages()
      if (failed) ElMessage.warning(`${success} 个成功，${failed} 个失败`)
      else ElMessage.success(`${success} 张图片上传成功`)
      return
    }
    ElMessage.success(`${selectedFiles.length} 个文件上传完成`)
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '文件上传失败')
  } finally {
    uploading.value = false
    uploadStatus.value = ''
    input.value = ''
  }
}

async function downloadFile(file: UploadedFile) {
  await downloadResource(file.url, file.original_name)
}

async function downloadResource(path: string, filename: string) {
  if (downloading.value) return
  downloading.value = true
  downloadProgress.value = 0
  downloadStatus.value = `正在下载 ${filename}`
  try {
    await downloadWithProgress(resolveUrl(path), filename, {
      headers: { Authorization: `Bearer ${getToken() ?? ''}` },
      onProgress: (percent) => (downloadProgress.value = percent),
    })
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '文件下载失败')
  } finally {
    downloading.value = false
    downloadStatus.value = ''
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
  await downloadResource(image.url, image.original_name)
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
  await downloadResource(job.download_url, 'starlit-books.zip')
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
            <span v-if="uploading" class="upload-status">{{ uploadStatus }}</span>
        <el-progress v-if="uploading" :percentage="uploadProgress" :stroke-width="6" />
        <span v-if="downloading" class="upload-status">{{ downloadStatus }} {{ downloadProgress }}%</span>
        <el-progress v-if="downloading" :percentage="downloadProgress" :stroke-width="6" />
        <el-button
          type="primary"
          :icon="Upload"
          :loading="uploading"
          @click="openPicker"
          :disabled="activeTab === 'archives'"
        >
          {{ activeTab === 'files' ? '上传文件' : '上传图片' }}
        </el-button>
        <input ref="fileInput" type="file" class="file-input" multiple @change="handleUpload" />
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
        <el-table-column label="URL" min-width="280" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="url-cell">
              <span>{{ resolveUrl(row.url) }}</span>
              <el-button link size="small" @click="copyUrl(row.url)">复制</el-button>
            </div>
          </template>
        </el-table-column>
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
              :disabled="downloading"
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
            <img :src="resolveUrl(row.url)" :alt="row.original_name" class="image-preview" />
          </template>
        </el-table-column>
        <el-table-column
          prop="original_name"
          label="文件名"
          min-width="220"
          show-overflow-tooltip
        />
        <el-table-column label="URL" min-width="280" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="url-cell">
              <span>{{ resolveUrl(row.url) }}</span>
              <el-button link size="small" @click="copyUrl(row.url)">复制</el-button>
            </div>
          </template>
        </el-table-column>
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
              :disabled="downloading"
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
              :disabled="downloading"
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
.upload-status,
.url-cell span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.upload-status {
  max-width: 180px;
  color: var(--admin-text-secondary);
  font-size: 12px;
}
.url-cell {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}
.url-cell span {
  min-width: 0;
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
