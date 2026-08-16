<script setup lang="ts">
/**
 * 图书管理 — 列表与 EPUB 批量上传队列
 * 批量上传按顺序执行，单本失败不会中断后续文件。
 */
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  ArrowDown,
  Close,
  Download,
  MoreFilled,
  Rank,
  RefreshRight,
  Upload,
} from '@element-plus/icons-vue'
import { api, BASE_URL, getToken, resolveUrl } from '@/api/client'
import type { BookSort } from '@/api/books'
import { useAdminTable } from '@/admin/composables/useAdminTable'
import { downloadWithProgress } from '@/utils/download'

/** 图书列表项（匹配后端 BookListItem） */
interface BookItem {
  id: number
  slug: string
  title: string
  author: string
  description: string
  cover_url: string
  file_path: string
  sort_order: number
  created_at: string
}

/** 上传队列状态 */
type UploadStatus = 'pending' | 'uploading' | 'success' | 'skipped' | 'failed'

/** 单本 EPUB 上传任务 */
interface BookUploadTask {
  id: string
  file: File
  status: UploadStatus
  progress: number
  error: string
}

/** 当前 EPUB 内可选择的封面图片 */
interface CoverCandidate {
  item_name: string
  filename: string
  media_type: string
  width: number
  height: number
  size: number
  score: number
  recommended: boolean
  preview_data_url: string
}

const showUploadDialog = ref(false)
const uploading = ref(false)
const fileInputRef = ref<HTMLInputElement | null>(null)
const uploadQueue = ref<BookUploadTask[]>([])
const uploadForm = ref({ title: '', author: '', description: '' })
const showEditDialog = ref(false)
const savingEdit = ref(false)
const extractingCover = ref(false)
const coverInputRef = ref<HTMLInputElement | null>(null)
const editingBook = ref<BookItem | null>(null)
const editForm = ref({ title: '', author: '', description: '', cover_url: '', sort_order: 0 })
const showCoverCandidatesDialog = ref(false)
const loadingCoverCandidates = ref(false)
const selectingCover = ref(false)
const coverCandidates = ref<CoverCandidate[]>([])
const selectedCandidateName = ref('')
const showSortDialog = ref(false)
const loadingSort = ref(false)
const savingSort = ref(false)
const sortBooks = ref<BookItem[]>([])
const draggedSlug = ref('')
const selectedBooks = ref<BookItem[]>([])
const downloading = ref(false)
const listSort = ref<BookSort>('newest')
const showArchiveDialog = ref(false)
const archiveName = ref('starlit-books')
const archiveExpireDays = ref(7)
const archiveOnly = ref(false)
const downloadProgress = ref(0)
const downloadStatus = ref('')

const completedCount = computed(
  () =>
    uploadQueue.value.filter((task) => task.status === 'success' || task.status === 'skipped')
      .length,
)
const failedCount = computed(
  () => uploadQueue.value.filter((task) => task.status === 'failed').length,
)
const isSingleUpload = computed(() => uploadQueue.value.length === 1)

const {
  loading,
  data,
  keyword,
  pagination,
  loadData,
  handleSearch,
  handlePageChange,
  handleSizeChange,
  handleDelete,
} = useAdminTable<BookItem>({
  fetchData: async ({ page, pageSize, keyword: kw }) => {
    const params = new URLSearchParams({
      page: String(page),
      page_size: String(pageSize),
      sort: listSort.value,
    })
    if (kw) params.set('keyword', kw)
    return api.get<{ items: BookItem[]; total: number }>(`/api/v1/books?${params}`, true)
  },
  deleteItem: async (item) => api.delete(`/api/v1/books/${item.slug}`),
  defaultPageSize: 15,
})

/** 切换后台列表排序。 */
function changeListSort(sort: BookSort) {
  listSort.value = sort
  pagination.page = 1
  void loadData()
}

/** 打开上传弹窗并重置队列 */
function openUpload() {
  uploadForm.value = { title: '', author: '', description: '' }
  uploadQueue.value = []
  showUploadDialog.value = true
}

/** 显式打开 EPUB 多选文件选择器 */
function openFilePicker() {
  if (!uploading.value) fileInputRef.value?.click()
}

/** 将选择的 EPUB 合并到上传队列，并按文件名去重 */
function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const selected = Array.from(input.files ?? [])
  const existingKeys = new Set(
    uploadQueue.value.map((task) => `${task.file.name}:${task.file.size}`),
  )

  for (const file of selected) {
    if (!file.name.toLowerCase().endsWith('.epub')) continue
    const key = `${file.name}:${file.size}`
    if (existingKeys.has(key)) continue
    existingKeys.add(key)
    uploadQueue.value.push({
      id: `${file.name}-${file.size}-${file.lastModified}`,
      file,
      status: 'pending',
      progress: 0,
      error: '',
    })
  }

  if (uploadQueue.value.length === 1 && !uploadForm.value.title) {
    uploadForm.value.title = uploadQueue.value[0].file.name.replace(/\.epub$/i, '')
  }
  input.value = ''
}

/** 从等待队列移除单个文件 */
function removeTask(taskId: string) {
  if (uploading.value) return
  uploadQueue.value = uploadQueue.value.filter((task) => task.id !== taskId)
}

/** 格式化文件大小 */
function formatFileSize(size: number): string {
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

/** 上传单本 EPUB，并报告浏览器侧进度 */
function uploadBook(task: BookUploadTask): Promise<void> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    const formData = new FormData()
    formData.append('file', task.file)
    formData.append('title', isSingleUpload.value ? uploadForm.value.title : '')
    formData.append('author', isSingleUpload.value ? uploadForm.value.author : '')
    formData.append('description', isSingleUpload.value ? uploadForm.value.description : '')

    xhr.open('POST', `${BASE_URL}/api/v1/books`)
    const token = getToken()
    if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`)
    xhr.upload.addEventListener('progress', (event) => {
      if (event.lengthComputable) task.progress = Math.round((event.loaded / event.total) * 100)
    })
    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve()
        return
      }
      try {
        const body = JSON.parse(xhr.responseText) as { detail?: string }
        const error = new Error(body.detail || `上传失败 (${xhr.status})`)
        Object.assign(error, { status: xhr.status })
        reject(error)
      } catch {
        reject(new Error(`上传失败 (${xhr.status})`))
      }
    })
    xhr.addEventListener('error', () => reject(new Error('网络错误，上传失败')))
    xhr.send(formData)
  })
}

/** 顺序执行指定任务，重复 slug 标记为跳过，其余失败继续下一本 */
async function runTasks(tasks: BookUploadTask[]) {
  uploading.value = true
  for (const task of tasks) {
    task.status = 'uploading'
    task.progress = 0
    task.error = ''
    try {
      await uploadBook(task)
      task.status = 'success'
      task.progress = 100
    } catch (err: unknown) {
      const error = err as Error & { status?: number }
      task.status = error.status === 409 ? 'skipped' : 'failed'
      task.error = error.status === 409 ? '同名图书已存在，已跳过' : error.message
    }
  }
  uploading.value = false
  await loadData()
}

/** 上传所有等待项 */
async function submitUpload() {
  const pending = uploadQueue.value.filter((task) => task.status === 'pending')
  if (pending.length === 0) {
    ElMessage.warning('请选择 EPUB 文件')
    return
  }
  await runTasks(pending)
  ElMessage.success(`处理完成：成功/跳过 ${completedCount.value} 本，失败 ${failedCount.value} 本`)
}

/** 重试全部失败项 */
async function retryFailed() {
  const failed = uploadQueue.value.filter((task) => task.status === 'failed')
  if (failed.length > 0) await runTasks(failed)
}

/** 上传状态文案 */
function statusText(task: BookUploadTask): string {
  const labels: Record<UploadStatus, string> = {
    pending: '等待中',
    uploading: `上传中 ${task.progress}%`,
    success: '成功',
    skipped: '已跳过',
    failed: '失败',
  }
  return labels[task.status]
}

/** 更新当前页的批量下载选择。 */
function handleSelectionChange(rows: unknown[]) {
  // Element Plus 的表格泛型未从模板推断，这里将选择结果收窄为当前表格行类型。
  selectedBooks.value = rows as BookItem[]
}

/** 移动端卡片列表的“更多操作”命令分发。 */
function handleMobileCommand(command: string, book: BookItem) {
  if (command === 'edit') openEdit(book)
  else if (command === 'download') void downloadBook(book)
  else if (command === 'cover') void extractCover(book)
  else if (command === 'delete') void handleDelete(book, `「${book.title}」`)
}

/** 下载单本 EPUB。 */
async function downloadBook(book: BookItem) {
  downloading.value = true
  downloadProgress.value = 0
  downloadStatus.value = `正在下载 ${book.title}`
  try {
    await downloadWithProgress(
      `${BASE_URL}/api/v1/books/${encodeURIComponent(book.slug)}/download`,
      `${book.title}${book.author ? ` - ${book.author}` : ''}.epub`,
      {
        headers: { Authorization: `Bearer ${getToken() ?? ''}` },
        onProgress: (percent) => (downloadProgress.value = percent),
      },
    )
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '下载失败')
  } finally {
    downloading.value = false
    downloadStatus.value = ''
  }
}

/** 将当前选中的图书打包为 ZIP。 */
function openArchiveDialog(onlyArchive = false) {
  if (selectedBooks.value.length === 0 || downloading.value) return
  archiveOnly.value = onlyArchive
  archiveName.value = 'starlit-books'
  archiveExpireDays.value = 7
  showArchiveDialog.value = true
}

/** 处理打包菜单选项。 */
function handleArchiveCommand(command: string | number) {
  openArchiveDialog(command === 'archive')
}

/** 创建选中图书的 ZIP，可选择仅生成归档或生成后立即下载。 */
async function downloadSelectedZip() {
  if (selectedBooks.value.length === 0) return
  showArchiveDialog.value = false
  downloading.value = true
  downloadProgress.value = 0
  downloadStatus.value = '正在创建打包任务'
  try {
    const response = await fetch(`${BASE_URL}/api/v1/books/download-jobs`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${getToken() ?? ''}`,
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({
        slugs: selectedBooks.value.map((book) => book.slug),
        archive_name: archiveName.value,
        expire_days: archiveExpireDays.value,
      }),
    })
    if (!response.ok) throw new Error('创建 ZIP 打包任务失败')
    const created = (await response.json()) as { id: number }
    const job = await waitForDownloadJob(created.id)
    if (!archiveOnly.value) {
      await downloadWithProgress(`${BASE_URL}${job.download_url}`, `${archiveName.value}.zip`, {
        headers: { Authorization: `Bearer ${getToken() ?? ''}` },
        onProgress: (percent) => (downloadProgress.value = percent),
      })
    } else {
      ElMessage.success('归档已生成，可在文件管理中下载或挂载到藏宝阁')
    }
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : 'ZIP 下载失败')
  } finally {
    downloading.value = false
    downloadStatus.value = ''
  }
}

/** 轮询后台打包任务状态。 */
async function waitForDownloadJob(jobId: number): Promise<{ download_url: string }> {
  for (let attempt = 0; attempt < 300; attempt += 1) {
    await new Promise((resolve) => window.setTimeout(resolve, 1000))
    const response = await fetch(`${BASE_URL}/api/v1/books/download-jobs/${jobId}`, {
      headers: { Authorization: `Bearer ${getToken() ?? ''}` },
      credentials: 'include',
    })
    if (!response.ok) {
      const body = await response.json().catch(() => ({ detail: '读取 ZIP 任务状态失败' }))
      throw new Error(body.detail || '读取 ZIP 任务状态失败')
    }
    const job = (await response.json()) as {
      status: string
      progress: number
      completed_books: number
      total_books: number
      error_message: string
      download_url: string | null
    }
    downloadProgress.value = job.progress
    downloadStatus.value = `${job.completed_books}/${job.total_books} 本已打包`
    if (job.status === 'completed' && job.download_url) return { download_url: job.download_url }
    if (job.status === 'failed') throw new Error(job.error_message || 'ZIP 打包失败')
  }
  throw new Error('图书 ZIP 打包超时，请稍后重试')
}

/** 打开图书编辑弹窗 */
function openEdit(book: BookItem) {
  editingBook.value = book
  editForm.value = {
    title: book.title,
    author: book.author,
    description: book.description,
    cover_url: book.cover_url,
    sort_order: book.sort_order,
  }
  showEditDialog.value = true
}

/** 保存手动编辑的元数据、封面和排序值 */
async function saveEdit() {
  if (!editingBook.value || !editForm.value.title.trim()) {
    ElMessage.warning('书名不能为空')
    return
  }
  savingEdit.value = true
  try {
    await api.put(
      `/api/v1/books/${encodeURIComponent(editingBook.value.slug)}`,
      editForm.value,
      true,
    )
    ElMessage.success('图书信息已更新')
    showEditDialog.value = false
    await loadData()
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '更新失败')
  } finally {
    savingEdit.value = false
  }
}

/** 打开手动封面文件选择器 */
function openCoverPicker() {
  if (!savingEdit.value) coverInputRef.value?.click()
}

/** 上传自定义封面到图床并自动回填 URL */
async function handleCoverUpload(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  savingEdit.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)
    const token = getToken()
    const response = await fetch(`${BASE_URL}/api/v1/images/upload`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    })
    if (!response.ok) {
      const body = await response.json().catch(() => ({ detail: '封面上传失败' }))
      throw new Error(body.detail || '封面上传失败')
    }
    const image = (await response.json()) as { url: string }
    editForm.value.cover_url = image.url
    ElMessage.success('封面已上传，保存后生效')
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '封面上传失败')
  } finally {
    savingEdit.value = false
    input.value = ''
  }
}

/** 使用改进后的规则重新从 EPUB 提取封面 */
async function extractCover(book: BookItem) {
  extractingCover.value = true
  try {
    await api.post(`/api/v1/books/${encodeURIComponent(book.slug)}/extract-cover`, undefined, true)
    ElMessage.success('封面已重新提取')
    await loadData()
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '未能识别封面')
  } finally {
    extractingCover.value = false
  }
}

/** 读取当前图书 EPUB 内的图片并打开封面选择器 */
async function openCoverCandidates() {
  if (!editingBook.value) return
  showCoverCandidatesDialog.value = true
  loadingCoverCandidates.value = true
  selectedCandidateName.value = ''
  coverCandidates.value = []
  try {
    coverCandidates.value = await api.get<CoverCandidate[]>(
      `/api/v1/books/${encodeURIComponent(editingBook.value.slug)}/cover-candidates`,
      true,
    )
    const recommended = coverCandidates.value.find((candidate) => candidate.recommended)
    selectedCandidateName.value = recommended?.item_name || ''
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '读取 EPUB 图片失败')
  } finally {
    loadingCoverCandidates.value = false
  }
}

/** 将选中的 EPUB 内图片保存为当前图书封面 */
async function selectCoverCandidate() {
  if (!editingBook.value || !selectedCandidateName.value) {
    ElMessage.warning('请选择一张图片')
    return
  }
  selectingCover.value = true
  try {
    const book = await api.post<BookItem>(
      `/api/v1/books/${encodeURIComponent(editingBook.value.slug)}/select-cover`,
      { item_name: selectedCandidateName.value },
      true,
    )
    editForm.value.cover_url = book.cover_url
    editingBook.value.cover_url = book.cover_url
    showCoverCandidatesDialog.value = false
    ElMessage.success('已从 EPUB 更新封面')
    await loadData()
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '设置封面失败')
  } finally {
    selectingCover.value = false
  }
}

/** 加载全部图书并打开全局排序弹窗 */
async function openSort() {
  showSortDialog.value = true
  loadingSort.value = true
  try {
    sortBooks.value = await api.get<BookItem[]>('/api/v1/books/admin/all', true)
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '加载排序列表失败')
  } finally {
    loadingSort.value = false
  }
}

/** 原生拖拽排序：把拖拽项插入目标项当前位置 */
function moveBook(targetSlug: string) {
  if (!draggedSlug.value || draggedSlug.value === targetSlug) return
  const fromIndex = sortBooks.value.findIndex((book) => book.slug === draggedSlug.value)
  const toIndex = sortBooks.value.findIndex((book) => book.slug === targetSlug)
  if (fromIndex < 0 || toIndex < 0) return
  const [book] = sortBooks.value.splice(fromIndex, 1)
  sortBooks.value.splice(toIndex, 0, book)
}

/** 保存全局图书顺序 */
async function saveSort() {
  savingSort.value = true
  try {
    await api.put(
      '/api/v1/books/reorder',
      { slugs: sortBooks.value.map((book) => book.slug) },
      true,
    )
    ElMessage.success('排序已保存')
    showSortDialog.value = false
    await loadData()
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '保存排序失败')
  } finally {
    savingSort.value = false
  }
}

onMounted(() => loadData())
</script>

<template>
  <div class="book-list-page">
    <div class="page-header">
      <div class="book-list-filters">
        <el-input
          v-model="keyword"
          placeholder="搜索书名/作者..."
          clearable
          style="width: 240px"
          @keyup.enter="handleSearch"
        />
        <el-select
          :model-value="listSort"
          style="width: 130px"
          aria-label="图书排序"
          @update:model-value="changeListSort"
        >
          <el-option label="最新上传" value="newest" />
          <el-option label="最早上传" value="oldest" />
          <el-option label="自定义排序" value="custom" />
        </el-select>
      </div>
      <div class="header-actions">
        <el-dropdown
          :disabled="selectedBooks.length === 0 || downloading"
          @command="handleArchiveCommand"
        >
          <el-button :icon="Download" :disabled="selectedBooks.length === 0 || downloading">
            下载选中（{{ selectedBooks.length }}）<el-icon class="el-icon--right"
              ><ArrowDown
            /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="download">打包并下载 ZIP</el-dropdown-item>
              <el-dropdown-item command="archive">仅打包，不立即下载</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <span v-if="downloading" class="download-status">
          {{ downloadStatus }} {{ downloadProgress }}%
        </span>
        <el-button :icon="Rank" @click="openSort">排序管理</el-button>
        <el-button type="primary" @click="openUpload"
          ><el-icon><Upload /></el-icon>上传图书</el-button
        >
      </div>
    </div>

    <el-card shadow="never" class="table-card">
      <!-- 移动端卡片列表 -->
      <div class="book-mobile-list">
        <div v-for="row in data" :key="row.id" class="book-mobile-card">
          <div class="book-mobile-head">
            <img v-if="row.cover_url" :src="resolveUrl(row.cover_url)" class="book-cover" alt="" />
            <div v-else class="book-cover-placeholder">无</div>
            <div class="book-mobile-title-wrap">
              <div class="book-mobile-title">{{ row.title }}</div>
              <div class="book-mobile-author">{{ row.author || '未知作者' }}</div>
            </div>
            <el-dropdown trigger="click" @command="handleMobileCommand($event, row)">
              <el-button circle :icon="MoreFilled" aria-label="更多操作" />
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="edit">编辑</el-dropdown-item>
                  <el-dropdown-item command="download">下载</el-dropdown-item>
                  <el-dropdown-item command="cover">重提封面</el-dropdown-item>
                  <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
          <p class="book-mobile-desc">{{ row.description || '暂无简介' }}</p>
          <div class="book-mobile-meta">
            <span>上传 {{ row.created_at?.slice(0, 10) || '--' }}</span>
            <span>排序 {{ row.sort_order }}</span>
          </div>
        </div>
        <el-empty v-if="data.length === 0" description="暂无图书" :image-size="72" />
      </div>

      <!-- 桌面端表格 -->
      <el-table
        :data="data as any"
        v-loading="loading"
        stripe
        class="book-desktop-table"
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="48" />
        <el-table-column label="封面" width="80">
          <template #default="{ row }">
            <img v-if="row.cover_url" :src="resolveUrl(row.cover_url)" class="book-cover" alt="" />
            <div v-else class="book-cover-placeholder">无</div>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="书名" min-width="200" />
        <el-table-column prop="author" label="作者" width="150" />
        <el-table-column prop="sort_order" label="排序" width="70" />
        <el-table-column prop="description" label="简介" min-width="200">
          <template #default="{ row }"
            >{{ row.description.slice(0, 50)
            }}{{ row.description.length > 50 ? '...' : '' }}</template
          >
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" width="170">
          <template #default="{ row }">{{ row.created_at?.slice(0, 10) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="270" fixed="right">
          <template #default="{ row }: { row: any }">
            <el-button type="primary" link size="small" @click="openEdit(row)">编辑</el-button>
            <el-button
              type="success"
              link
              size="small"
              :loading="downloading"
              @click="downloadBook(row)"
              >下载</el-button
            >
            <el-button
              type="warning"
              link
              size="small"
              :loading="extractingCover"
              @click="extractCover(row)"
              >重提封面</el-button
            >
            <el-button
              type="danger"
              link
              size="small"
              @click="handleDelete(row, `「${row.title}」`)"
              >删除</el-button
            >
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 15, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </el-card>

    <el-dialog v-model="showArchiveDialog" title="打包图书" width="420px">
      <el-form label-position="top">
        <el-form-item label="ZIP 文件名">
          <el-input v-model="archiveName" placeholder="例如：我的阅读清单" clearable>
            <template #suffix>.zip</template>
          </el-input>
        </el-form-item>
        <el-form-item label="归档有效期">
          <el-input-number v-model="archiveExpireDays" :min="1" :max="3650" />
          <span class="archive-expire-suffix">天后过期</span>
        </el-form-item>
      </el-form>
      <p class="archive-dialog-hint">
        已选择 {{ selectedBooks.length }} 本图书，{{
          archiveOnly ? '仅生成归档，不会自动下载。' : '生成完成后会自动下载。'
        }}
      </p>
      <template #footer>
        <el-button @click="showArchiveDialog = false">取消</el-button>
        <el-button type="primary" :disabled="!archiveName.trim()" @click="downloadSelectedZip">
          {{ archiveOnly ? '开始打包' : '打包并下载' }}
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="showUploadDialog"
      title="上传图书"
      width="680px"
      :close-on-click-modal="!uploading"
    >
      <div class="file-picker-row">
        <el-button plain :icon="Upload" :disabled="uploading" @click="openFilePicker"
          >选择 EPUB（可多选）</el-button
        >
        <span>已选择 {{ uploadQueue.length }} 本</span>
        <input
          ref="fileInputRef"
          type="file"
          accept=".epub,application/epub+zip"
          multiple
          class="file-input"
          tabindex="-1"
          @change="handleFileChange"
        />
      </div>

      <el-alert
        v-if="uploadQueue.length > 1"
        title="批量模式将自动读取 EPUB 元数据，并按顺序逐本上传。重复图书会跳过。"
        type="info"
        :closable="false"
      />

      <el-form v-if="isSingleUpload" label-position="top" class="single-book-form">
        <el-form-item label="书名"
          ><el-input v-model="uploadForm.title" placeholder="留空则读取 EPUB 元数据"
        /></el-form-item>
        <el-form-item label="作者"
          ><el-input v-model="uploadForm.author" placeholder="留空则读取 EPUB 元数据"
        /></el-form-item>
        <el-form-item label="简介"
          ><el-input
            v-model="uploadForm.description"
            type="textarea"
            :rows="2"
            placeholder="留空则读取 EPUB 元数据"
        /></el-form-item>
      </el-form>

      <div class="upload-queue">
        <el-empty
          v-if="uploadQueue.length === 0"
          description="尚未选择 EPUB 文件"
          :image-size="72"
        />
        <div v-for="task in uploadQueue" :key="task.id" class="upload-task">
          <div class="task-main">
            <span class="task-name">{{ task.file.name }}</span>
            <span class="task-size">{{ formatFileSize(task.file.size) }}</span>
            <el-tag
              :type="
                task.status === 'success'
                  ? 'success'
                  : task.status === 'failed'
                    ? 'danger'
                    : task.status === 'skipped'
                      ? 'warning'
                      : 'info'
              "
              size="small"
              >{{ statusText(task) }}</el-tag
            >
            <el-button
              v-if="task.status === 'pending' && !uploading"
              link
              :icon="Close"
              @click="removeTask(task.id)"
            />
          </div>
          <el-progress
            v-if="task.status === 'uploading'"
            :percentage="task.progress"
            :show-text="false"
            :stroke-width="6"
          />
          <p v-if="task.error" class="task-error">{{ task.error }}</p>
        </div>
      </div>

      <template #footer>
        <span class="batch-summary"
          >完成 {{ completedCount }}/{{ uploadQueue.length }}，失败 {{ failedCount }}</span
        >
        <el-button v-if="failedCount > 0 && !uploading" :icon="RefreshRight" @click="retryFailed"
          >重试失败项</el-button
        >
        <el-button :disabled="uploading" @click="showUploadDialog = false">关闭</el-button>
        <el-button
          type="primary"
          :loading="uploading"
          :disabled="uploadQueue.length === 0"
          @click="submitUpload"
          >开始上传</el-button
        >
      </template>
    </el-dialog>

    <el-dialog v-model="showEditDialog" title="编辑图书" width="560px">
      <el-form label-position="top">
        <div class="edit-grid">
          <el-form-item label="书名"><el-input v-model="editForm.title" /></el-form-item>
          <el-form-item label="作者"><el-input v-model="editForm.author" /></el-form-item>
        </div>
        <el-form-item label="简介"
          ><el-input v-model="editForm.description" type="textarea" :rows="3"
        /></el-form-item>
        <el-form-item label="封面">
          <div class="cover-editor">
            <img
              v-if="editForm.cover_url"
              :src="resolveUrl(editForm.cover_url)"
              class="cover-preview"
              alt="封面预览"
            />
            <div v-else class="cover-preview cover-preview--empty">无封面</div>
            <div class="cover-actions">
              <el-button plain :icon="Upload" @click="openCoverPicker">上传封面</el-button>
              <el-button plain @click="openCoverCandidates">从 EPUB 选择</el-button>
              <el-button v-if="editForm.cover_url" @click="editForm.cover_url = ''"
                >清空封面</el-button
              >
              <input
                ref="coverInputRef"
                type="file"
                accept="image/*"
                class="file-input"
                tabindex="-1"
                @change="handleCoverUpload"
              />
            </div>
          </div>
          <el-input v-model="editForm.cover_url" placeholder="也可手动填写封面 URL" />
        </el-form-item>
        <el-form-item label="排序值（越小越靠前）"
          ><el-input-number v-model="editForm.sort_order" :min="0"
        /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" :loading="savingEdit" @click="saveEdit">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="showCoverCandidatesDialog"
      title="从当前 EPUB 选择封面"
      width="820px"
      append-to-body
    >
      <el-alert
        title="选择只会更新这本图书的封面，不会修改 EPUB 文件。推荐项是系统自动识别的结果。"
        type="info"
        :closable="false"
      />
      <div v-loading="loadingCoverCandidates" class="candidate-grid">
        <el-empty
          v-if="!loadingCoverCandidates && coverCandidates.length === 0"
          description="EPUB 内没有可用图片"
        />
        <button
          v-for="candidate in coverCandidates"
          :key="candidate.item_name"
          type="button"
          class="candidate-card"
          :class="{ 'candidate-card--selected': selectedCandidateName === candidate.item_name }"
          @click="selectedCandidateName = candidate.item_name"
        >
          <div class="candidate-image-wrap">
            <img
              :src="candidate.preview_data_url"
              class="candidate-image"
              :alt="candidate.filename"
            />
            <el-tag v-if="candidate.recommended" class="candidate-tag" type="success" size="small"
              >推荐</el-tag
            >
          </div>
          <span class="candidate-name" :title="candidate.item_name">{{ candidate.filename }}</span>
          <span class="candidate-meta"
            >{{ candidate.width }} × {{ candidate.height }} ·
            {{ formatFileSize(candidate.size) }}</span
          >
        </button>
      </div>
      <template #footer>
        <el-button @click="showCoverCandidatesDialog = false">取消</el-button>
        <el-button
          type="primary"
          :loading="selectingCover"
          :disabled="!selectedCandidateName"
          @click="selectCoverCandidate"
          >设为封面</el-button
        >
      </template>
    </el-dialog>

    <el-dialog v-model="showSortDialog" title="图书全局排序" width="620px">
      <el-alert
        title="拖动图书调整顺序，保存后用户端和搜索结果都会使用该顺序。"
        type="info"
        :closable="false"
      />
      <div v-loading="loadingSort" class="sort-list">
        <div
          v-for="(book, index) in sortBooks"
          :key="book.slug"
          class="sort-item"
          draggable="true"
          @dragstart="draggedSlug = book.slug"
          @dragover.prevent
          @drop.prevent="moveBook(book.slug)"
          @dragend="draggedSlug = ''"
        >
          <el-icon class="drag-handle"><Rank /></el-icon>
          <span class="sort-index">{{ index + 1 }}</span>
          <img v-if="book.cover_url" :src="resolveUrl(book.cover_url)" class="sort-cover" alt="" />
          <span class="sort-title">{{ book.title }}</span>
          <span class="sort-author">{{ book.author }}</span>
        </div>
      </div>
      <template #footer>
        <el-button @click="showSortDialog = false">取消</el-button>
        <el-button type="primary" :loading="savingSort" @click="saveSort">保存顺序</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.book-list-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.book-list-filters {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}
.archive-dialog-hint {
  margin: 0;
  color: var(--admin-text-secondary, #909399);
  font-size: 13px;
}
.archive-expire-suffix {
  margin-left: 8px;
  color: var(--admin-text-secondary, #909399);
  font-size: 13px;
}
.header-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}
.download-status {
  color: var(--admin-text-secondary, #909399);
  font-size: 12px;
  white-space: nowrap;
}
.table-card {
  border-radius: 12px;
}
.book-cover {
  width: 40px;
  height: 56px;
  object-fit: cover;
  border-radius: 4px;
}
.book-cover-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 56px;
  border-radius: 4px;
  background: var(--admin-fill-bg, var(--el-fill-color-light));
  color: var(--admin-text-secondary, var(--el-text-color-secondary));
  font-size: 12px;
}

/* 移动端卡片列表（默认隐藏，窄屏替换表格） */
.book-mobile-list {
  display: none;
  flex-direction: column;
  gap: 12px;
}

.book-mobile-card {
  padding: 14px;
  border: 1px solid var(--admin-border-color, #e4e7ed);
  border-radius: 12px;
  background: var(--admin-panel-bg, #ffffff);
}

.book-mobile-head {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.book-mobile-title-wrap {
  flex: 1;
  min-width: 0;
}

.book-mobile-title {
  overflow: hidden;
  color: var(--admin-text-color, #303133);
  font-size: 14px;
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.book-mobile-author {
  margin-top: 4px;
  overflow: hidden;
  color: var(--admin-text-secondary, #909399);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.book-mobile-desc {
  display: -webkit-box;
  margin: 10px 0 0;
  overflow: hidden;
  color: var(--admin-text-secondary, #909399);
  font-size: 12px;
  line-height: 1.6;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.book-mobile-meta {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin-top: 10px;
  color: var(--admin-text-secondary, #909399);
  font-size: 11px;
}
.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
.file-picker-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
  color: var(--admin-text-secondary, #909399);
  font-size: 13px;
}
.file-input {
  display: none;
}
.single-book-form {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 16px;
  margin-top: 14px;
}
.single-book-form :deep(.el-form-item:last-child) {
  grid-column: 1 / -1;
}
.upload-queue {
  max-height: 310px;
  margin-top: 14px;
  overflow-y: auto;
}
.upload-task {
  padding: 10px 0;
  border-bottom: 1px solid var(--admin-border-color, #e4e7ed);
}
.task-main {
  display: flex;
  align-items: center;
  gap: 10px;
}
.task-name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.task-size,
.batch-summary {
  color: var(--admin-text-secondary, #909399);
  font-size: 12px;
}
.task-error {
  margin: 5px 0 0;
  color: #f56c6c;
  font-size: 12px;
}
.batch-summary {
  margin-right: auto;
}
.edit-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 16px;
}
.cover-editor {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 10px;
}
.cover-preview {
  width: 72px;
  height: 100px;
  border-radius: 5px;
  object-fit: cover;
}
.cover-preview--empty {
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--admin-fill-bg, var(--el-fill-color-light));
  color: var(--admin-text-secondary, var(--el-text-color-secondary));
  font-size: 12px;
}
.cover-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.candidate-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(145px, 1fr));
  gap: 14px;
  min-height: 180px;
  max-height: 560px;
  margin-top: 14px;
  overflow-y: auto;
}
.candidate-card {
  min-width: 0;
  padding: 8px;
  border: 2px solid transparent;
  border-radius: 8px;
  background: var(--admin-fill-bg, var(--el-fill-color-light));
  color: inherit;
  text-align: left;
  cursor: pointer;
  transition:
    border-color 0.15s,
    transform 0.15s;
}
.candidate-card:hover {
  transform: translateY(-2px);
}
.candidate-card--selected {
  border-color: var(--el-color-primary);
}
.candidate-image-wrap {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 190px;
  border-radius: 5px;
  overflow: hidden;
  background: var(--admin-panel-bg, var(--el-bg-color));
}
.candidate-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.candidate-tag {
  position: absolute;
  top: 6px;
  right: 6px;
}
.candidate-name,
.candidate-meta {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.candidate-name {
  margin-top: 7px;
  font-size: 13px;
}
.candidate-meta {
  margin-top: 3px;
  color: var(--admin-text-secondary, var(--el-text-color-secondary));
  font-size: 11px;
}
.sort-list {
  max-height: 480px;
  margin-top: 14px;
  overflow-y: auto;
}
.sort-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-bottom: 1px solid var(--admin-border-color, #e4e7ed);
  cursor: grab;
}
.sort-item:active {
  cursor: grabbing;
}
.drag-handle,
.sort-index,
.sort-author {
  color: var(--admin-text-secondary, #909399);
}
.sort-index {
  width: 28px;
  font-size: 12px;
}
.sort-cover {
  width: 32px;
  height: 44px;
  border-radius: 3px;
  object-fit: cover;
}
.sort-title {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.sort-author {
  max-width: 130px;
  overflow: hidden;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 767px) {
  .page-header {
    align-items: stretch;
    flex-direction: column;
  }

  .book-list-filters,
  .book-list-filters .el-input,
  .book-list-filters .el-select {
    width: 100% !important;
  }

  .header-actions {
    width: 100%;
  }

  .header-actions > * {
    flex: 1;
  }

  /* 窄屏隐藏表格，改用卡片列表 */
  .book-desktop-table {
    display: none;
  }

  .book-mobile-list {
    display: flex;
  }

  .pagination-wrap {
    justify-content: center;
  }
}
</style>
