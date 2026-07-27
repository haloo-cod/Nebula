<script setup lang="ts">
/**
 * 藏宝阁管理 — 列表页
 * 表格展示所有资源，支持按分类筛选、新建、编辑、删除
 */
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, Plus, Upload } from '@element-plus/icons-vue'
import { api } from '@/api/client'
import { deleteUploadedFile, fetchFiles, uploadFile, type UploadedFile } from '@/api/files'

/** 藏宝阁项（匹配后端 TreasureResponse） */
interface TreasureItem {
  id: number
  slug: string
  title: string
  description: string
  category: string
  icon: string
  url: string
  download_file: string
  tags: string[]
  sort_order: number
  created_at: string
  archive_id: number | null
  archive_status: string | null
  archive_expires_at: string | null
}

/** 已完成的图书归档任务。 */
interface BookArchiveJob {
  id: number
  status: string
  total_books: number
  file_size: number
  created_at: string
  download_url: string | null
  archive_name: string
  expire_days: number
  expires_at: string | null
}

const loading = ref(false)
const treasures = ref<TreasureItem[]>([])
const categories = ref<string[]>([])
const filterCategory = ref('')
const showDialog = ref(false)
const isEdit = ref(false)
const saving = ref(false)
const editingId = ref(0)
const uploadedFiles = ref<UploadedFile[]>([])
const bookArchives = ref<BookArchiveJob[]>([])
const loadingArchives = ref(false)
const loadingFiles = ref(false)
const uploadingFile = ref(false)
const uploadProgress = ref(0)
const fileInputRef = ref<HTMLInputElement | null>(null)
const form = ref({
  slug: '',
  title: '',
  description: '',
  category: '',
  icon: '',
  url: '',
  download_file: '',
  tags: '',
  sort_order: 0,
})

/** 加载数据 */
async function loadData() {
  loading.value = true
  try {
    const params = filterCategory.value
      ? `?category=${encodeURIComponent(filterCategory.value)}`
      : ''
    const res = await api.get<{ items: TreasureItem[]; total: number }>(
      `/api/v1/treasures${params}`,
      true,
    )
    treasures.value = res.items
  } catch {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

/** 加载分类列表 */
async function loadCategories() {
  try {
    categories.value = await api.get<string[]>('/api/v1/treasures/categories', true)
  } catch {
    /* 静默 */
  }
}

/** 加载可复用的下载文件库 */
async function loadFiles() {
  loadingFiles.value = true
  try {
    uploadedFiles.value = await fetchFiles()
  } catch {
    ElMessage.error('加载文件库失败')
  } finally {
    loadingFiles.value = false
  }
}

/** 加载可挂载到藏宝阁的已完成图书归档。 */
async function loadBookArchives() {
  loadingArchives.value = true
  try {
    const response = await api.get<{ items: BookArchiveJob[]; total: number }>(
      '/api/v1/books/download-jobs?page_size=100',
      true,
    )
    bookArchives.value = response.items.filter(
      (job) => job.status === 'completed' && Boolean(job.download_url),
    )
  } catch {
    ElMessage.error('加载图书归档失败')
  } finally {
    loadingArchives.value = false
  }
}

/** 生成藏宝阁归档下载地址。 */
function archiveDownloadUrl(jobId: number): string {
  return `/api/v1/treasures/archive/${jobId}/download`
}

/** 选择归档后使用藏宝阁自己的下载地址，避免直接暴露后台任务地址。 */
function selectBookArchive(jobId: number) {
  if (!form.value.slug.trim()) {
    ElMessage.warning('请先填写 Slug，再选择图书归档')
    return
  }
  form.value.download_file = archiveDownloadUrl(jobId)
}

/** 根据标题生成 slug 预览，后端负责最终唯一化。 */
function previewSlug(title: string): string {
  return title
    .normalize('NFKC')
    .toLowerCase()
    .replace(/[^\p{L}\p{N}]+/gu, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 180)
}

/** 格式化文件大小 */
function formatFileSize(size: number): string {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  if (size < 1024 * 1024 * 1024) return `${(size / 1024 / 1024).toFixed(1)} MB`
  return `${(size / 1024 / 1024 / 1024).toFixed(2)} GB`
}

/** 格式化归档剩余时间。 */
function archiveExpiryLabel(item: TreasureItem): string {
  if (!item.archive_id || !item.archive_expires_at) return ''
  const remaining = Math.ceil((new Date(item.archive_expires_at).getTime() - Date.now()) / 86400000)
  return remaining > 0 ? `${remaining} 天后过期` : '已过期'
}

/** 当前关联的文件记录 */
function currentFile(): UploadedFile | undefined {
  return uploadedFiles.value.find((file) => file.url === form.value.download_file)
}

/** 显式打开系统文件选择器，避免组件按钮嵌套在 label 中失效 */
function openFilePicker() {
  if (!uploadingFile.value) fileInputRef.value?.click()
}

/** 上传资源文件并自动关联到当前藏宝条目 */
async function handleFileUpload(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  uploadingFile.value = true
  uploadProgress.value = 0
  try {
    const uploaded = await uploadFile(file, (percent) => {
      uploadProgress.value = percent
    })
    uploadedFiles.value.unshift(uploaded)
    form.value.download_file = uploaded.url
    ElMessage.success('文件上传成功，已关联到当前资源')
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '文件上传失败')
  } finally {
    uploadingFile.value = false
    uploadProgress.value = 0
    input.value = ''
  }
}

/** 从文件库删除文件；被其他条目引用的文件应先解除关联 */
async function removeUploadedFile(file: UploadedFile) {
  try {
    await ElMessageBox.confirm(
      `确定永久删除文件「${file.original_name}」？使用该地址的其他资源也会无法下载。`,
      '删除文件',
      { type: 'warning' },
    )
    await deleteUploadedFile(file.id)
    uploadedFiles.value = uploadedFiles.value.filter((item) => item.id !== file.id)
    if (form.value.download_file === file.url) form.value.download_file = ''
    ElMessage.success('文件已删除')
  } catch {
    // 用户取消
  }
}

/** 筛选分类变化 */
function handleCategoryChange() {
  loadData()
}

/** 打开新建弹窗 */
function openCreate() {
  isEdit.value = false
  form.value = {
    slug: '',
    title: '',
    description: '',
    category: '',
    icon: '',
    url: '',
    download_file: '',
    tags: '',
    sort_order: 0,
  }
  showDialog.value = true
}

/** 打开编辑弹窗 */
function openEdit(item: TreasureItem) {
  isEdit.value = true
  editingId.value = item.id
  form.value = {
    slug: item.slug,
    title: item.title,
    description: item.description,
    category: item.category,
    icon: item.icon,
    url: item.url,
    download_file: item.download_file,
    tags: item.tags.join(', '),
    sort_order: item.sort_order,
  }
  showDialog.value = true
}

/** 保存 */
async function handleSave() {
  if (!form.value.title.trim() || !form.value.category.trim()) {
    ElMessage.warning('标题和分类不能为空')
    return
  }
  if (!isEdit.value && !form.value.slug.trim())
    form.value.slug = previewSlug(form.value.title) || 'treasure'

  saving.value = true
  try {
    const payload = {
      ...form.value,
      tags: form.value.tags
        ? form.value.tags
            .split(',')
            .map((t) => t.trim())
            .filter(Boolean)
        : [],
    }

    if (isEdit.value) {
      await api.put(`/api/v1/treasures/${editingId.value}`, payload, true)
      ElMessage.success('更新成功')
    } else {
      await api.post('/api/v1/treasures', payload, true)
      ElMessage.success('创建成功')
    }
    showDialog.value = false
    loadData()
    loadCategories()
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '保存失败')
  } finally {
    saving.value = false
  }
}

/** 删除 */
async function handleDelete(item: TreasureItem) {
  try {
    await ElMessageBox.confirm(`确定删除「${item.title}」？`, '确认删除', { type: 'warning' })
    await api.delete(`/api/v1/treasures/${item.id}`)
    ElMessage.success('删除成功')
    loadData()
  } catch {
    /* 取消 */
  }
}

onMounted(() => {
  loadData()
  loadCategories()
  loadFiles()
  loadBookArchives()
})
</script>

<template>
  <div class="treasure-list-page">
    <div class="page-header">
      <div class="filter-row">
        <el-select
          v-model="filterCategory"
          placeholder="全部分类"
          clearable
          style="width: 140px"
          @change="handleCategoryChange"
        >
          <el-option v-for="cat in categories" :key="cat" :label="cat" :value="cat" />
        </el-select>
        <span class="page-title">共 {{ treasures.length }} 项</span>
      </div>
      <el-button type="primary" @click="openCreate">
        <el-icon><Plus /></el-icon>新增资源
      </el-button>
    </div>

    <el-card shadow="never" class="table-card">
      <el-table :data="treasures as any" v-loading="loading" stripe style="width: 100%">
        <el-table-column prop="icon" label="图标" width="60">
          <template #default="{ row }: { row: any }">
            <span class="icon-cell">{{ row.icon }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="150" />
        <el-table-column prop="category" label="分类" width="100">
          <template #default="{ row }: { row: any }">
            <el-tag size="small">{{ row.category }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200">
          <template #default="{ row }: { row: any }">
            {{ row.description?.slice(0, 40) }}{{ row.description?.length > 40 ? '...' : '' }}
          </template>
        </el-table-column>
        <el-table-column prop="tags" label="标签" min-width="120">
          <template #default="{ row }: { row: any }">
            <el-tag v-for="tag in row.tags" :key="tag" size="small" style="margin-right: 4px">{{
              tag
            }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="sort_order" label="排序" width="60" />
        <el-table-column label="下载状态" min-width="130">
          <template #default="{ row }: { row: any }">
            <el-tag
              v-if="row.archive_id"
              :type="row.archive_status === 'expired' ? 'danger' : 'warning'"
              size="small"
            >
              {{
                row.archive_status === 'expired'
                  ? '归档已过期'
                  : archiveExpiryLabel(row as TreasureItem)
              }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }: { row: any }">
            <el-button type="primary" link size="small" @click="openEdit(row)">编辑</el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新建/编辑弹窗 -->
    <el-dialog v-model="showDialog" :title="isEdit ? '编辑资源' : '新增资源'" width="540px">
      <el-form label-position="top">
        <div class="form-grid">
          <el-form-item label="Slug">
            <el-input
              :model-value="isEdit ? form.slug : previewSlug(form.title) || '保存后自动生成'"
              disabled
            />
          </el-form-item>
          <el-form-item label="标题">
            <el-input v-model="form.title" placeholder="资源名称" />
          </el-form-item>
          <el-form-item label="分类">
            <el-input v-model="form.category" placeholder="如：开源项目、工具、资源下载" />
          </el-form-item>
          <el-form-item label="图标（emoji）">
            <el-input v-model="form.icon" placeholder="🔧" />
          </el-form-item>
        </div>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="资源简介" />
        </el-form-item>
        <el-form-item label="链接 URL">
          <el-input v-model="form.url" placeholder="https://github.com/..." />
        </el-form-item>
        <el-form-item label="下载文件（可选）">
          <div class="download-file-field">
            <div class="file-actions">
              <el-button type="primary" plain :loading="uploadingFile" @click="openFilePicker">
                <el-icon><Upload /></el-icon>
                {{ uploadingFile ? `上传中 ${uploadProgress}%` : '上传新文件' }}
              </el-button>
              <input
                ref="fileInputRef"
                type="file"
                class="file-input"
                tabindex="-1"
                @change="handleFileUpload"
              />
              <el-button v-if="form.download_file" @click="form.download_file = ''"
                >解除关联</el-button
              >
            </div>

            <el-progress
              v-if="uploadingFile"
              :percentage="uploadProgress"
              :stroke-width="8"
              :show-text="false"
            />

            <el-select
              v-model="form.download_file"
              filterable
              clearable
              :loading="loadingFiles"
              placeholder="从已上传文件中选择"
              style="width: 100%"
            >
              <el-option
                v-for="file in uploadedFiles"
                :key="file.id"
                :label="`${file.original_name} (${formatFileSize(file.file_size)})`"
                :value="file.url"
              >
                <div class="file-option">
                  <span class="file-option__name">{{ file.original_name }}</span>
                  <span>{{ formatFileSize(file.file_size) }}</span>
                  <el-button
                    type="danger"
                    link
                    :icon="Delete"
                    @click.stop="removeUploadedFile(file)"
                  >
                    删除
                  </el-button>
                </div>
              </el-option>
            </el-select>

            <el-select
              :model-value="
                bookArchives.find(
                  (job) =>
                    form.download_file.includes(
                      `/treasures/${encodeURIComponent(form.slug)}/download`,
                    ) && form.download_file.includes(`archive=${job.id}`),
                )?.id
              "
              filterable
              clearable
              :loading="loadingArchives"
              placeholder="或选择已完成的图书归档"
              style="width: 100%"
              @update:model-value="(value: number | undefined) => value && selectBookArchive(value)"
            >
              <el-option
                v-for="job in bookArchives"
                :key="job.id"
                :label="`图书归档 #${job.id}（${job.total_books} 本，${formatFileSize(job.file_size)}）`"
                :value="job.id"
              />
            </el-select>

            <el-input
              v-model="form.download_file"
              placeholder="也可手动填写外部下载地址"
              clearable
            />

            <div v-if="currentFile()" class="selected-file">
              已关联：{{ currentFile()?.original_name }}
              <span>{{ formatFileSize(currentFile()?.file_size ?? 0) }}</span>
            </div>
          </div>
        </el-form-item>
        <el-form-item label="标签（逗号分隔）">
          <el-input v-model="form.tags" placeholder="Vue, 工具, 效率" />
        </el-form-item>
        <el-form-item label="排序权重">
          <el-input-number v-model="form.sort_order" :min="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">{{
          isEdit ? '更新' : '创建'
        }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.treasure-list-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.filter-row {
  display: flex;
  align-items: center;
  gap: 12px;
}
.page-title {
  font-size: 14px;
  color: var(--admin-text-secondary, #909399);
}
.table-card {
  border-radius: 12px;
}

/* 弹窗内容过长时只滚动表单，底部操作区始终留在视口内。 */
:deep(.el-dialog) {
  display: flex;
  flex-direction: column;
  max-height: calc(100vh - 48px);
  margin: 24px auto;
}

:deep(.el-dialog__header),
:deep(.el-dialog__footer) {
  flex-shrink: 0;
}

:deep(.el-dialog__body) {
  min-height: 0;
  overflow-y: auto;
}

.icon-cell {
  font-size: 20px;
}
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 24px;
}
.download-file-field {
  display: flex;
  flex-direction: column;
  gap: 10px;
  width: 100%;
}
.file-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.file-input {
  display: none;
}
.file-option {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}
.file-option__name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
}
.selected-file {
  color: var(--admin-text-secondary, #909399);
  font-size: 12px;
}
.selected-file span {
  margin-left: 8px;
}
</style>
