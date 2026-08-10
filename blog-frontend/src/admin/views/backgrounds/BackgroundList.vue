<script setup lang="ts">
/**
 * 背景图管理 — 列表页
 * 按 theme(dark/light) + device(desktop/mobile) 分组管理背景图
 */
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { api, resolveUrl } from '@/api/client'
import { fetchFiles, type UploadedFile } from '@/api/files'
import ImagePickerDialog, { type PickerImage } from '@/admin/components/ImagePickerDialog.vue'

/** 背景图项（匹配后端 BackgroundResponse） */
interface BackgroundItem {
  id: number
  url: string
  theme: string
  device: string
  sort_order: number
  created_at: string
  media_type?: 'image' | 'video'
  poster_url?: string
  mime_type?: string
  file_size?: number
}

const loading = ref(false)
const backgrounds = ref<BackgroundItem[]>([])
const filterTheme = ref('')
const filterDevice = ref('')
const uploading = ref(false)
const showUploadDialog = ref(false)
const uploadForm = ref({ theme: 'dark', device: 'desktop' })
const mediaType = ref<'image' | 'video'>('image')
const externalUrl = ref('')
const posterUrl = ref('')
const videoFile = ref<File | null>(null)
const videoInput = ref<HTMLInputElement | null>(null)
const videoPreview = ref('')
const videoStatus = ref<'idle' | 'ready' | 'error'>('idle')
const libraryFiles = ref<UploadedFile[]>([])
const selectedLibraryFileId = ref<number | null>(null)
const showImagePicker = ref(false)
const selectedImage = ref<PickerImage | null>(null)
const selectedImages = ref<PickerImage[]>([])
const selectedIds = ref<number[]>([])
const deleting = ref(false)

/** 加载背景图列表 */
async function loadBackgrounds() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (filterTheme.value) params.set('theme', filterTheme.value)
    if (filterDevice.value) params.set('device', filterDevice.value)
    const query = params.toString() ? `?${params}` : ''
    const res = await api.get<{ items: BackgroundItem[]; total: number }>(
      `/api/v1/backgrounds${query}`,
      true,
    )
    backgrounds.value = res.items
  } catch {
    ElMessage.error('加载背景图失败')
  } finally {
    loading.value = false
  }
}

/** 筛选变化 */
function handleFilterChange() {
  loadBackgrounds()
}

/** 打开上传弹窗 */
function openUpload() {
  uploadForm.value = { theme: 'dark', device: 'desktop' }
  mediaType.value = 'image'
  externalUrl.value = ''
  posterUrl.value = ''
  videoFile.value = null
  videoPreview.value = ''
  videoStatus.value = 'idle'
  selectedLibraryFileId.value = null
  void loadLibraryFiles()
  selectedImage.value = null
  selectedImages.value = []
  showUploadDialog.value = true
}

async function loadLibraryFiles() {
  try {
    libraryFiles.value = (await fetchFiles()).filter((file) => file.mime_type.startsWith('video/'))
  } catch { libraryFiles.value = [] }
}

function formatFileSize(size = 0): string {
  if (!size) return '—'
  if (size < 1024 * 1024) return `${Math.ceil(size / 1024)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

function handleVideoFileChange(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0] ?? null
  if (!file) return
  const expected = ({ 'video/mp4': '.mp4', 'video/webm': '.webm', 'video/quicktime': '.mov' } as Record<string, string>)[file.type]
  const suffix = file.name.slice(file.name.lastIndexOf('.')).toLowerCase()
  if (!expected || expected !== suffix) {
    ElMessage.error('仅支持 MIME 与扩展名匹配的 MP4、WebM 或 MOV 视频')
    return
  }
  if (file.size > 50 * 1024 * 1024) {
    ElMessage.error('视频文件不能超过 50MB')
    return
  }
  videoFile.value = file
  videoStatus.value = 'idle'
  videoPreview.value = URL.createObjectURL(file)
}

function handleVideoPreview(event: Event) {
  videoStatus.value = (event.target as HTMLVideoElement).error ? 'error' : 'ready'
}

/** 从媒体库选择图片，随后创建背景记录。 */
async function handleUpload() {
  const sourceCount = [externalUrl.value.trim(), videoFile.value, selectedLibraryFileId.value].filter(Boolean).length
  if (mediaType.value === 'video' && sourceCount !== 1) {
    ElMessage.warning('请选择一个视频来源：文件管理、本地上传或外部 URL')
    return
  }
  if (mediaType.value === 'video' && externalUrl.value.trim()) {
    try {
      const parsed = new URL(externalUrl.value.trim())
      if (!['http:', 'https:'].includes(parsed.protocol)) throw new Error()
    } catch {
      ElMessage.warning('外部视频 URL 必须是 HTTP 或 HTTPS 地址')
      return
    }
  }
  if (mediaType.value === 'video') {
    uploading.value = true
    try {
      let mediaUrl = externalUrl.value.trim()
      let mimeType = ''
      let fileSize = 0
      const libraryFile = libraryFiles.value.find((file) => file.id === selectedLibraryFileId.value)
      if (selectedLibraryFileId.value) {
        // Use the selected id directly so a delayed file-library refresh cannot produce an empty URL.
        mediaUrl = `/api/v1/files/${selectedLibraryFileId.value}/media`
        if (libraryFile) {
          mimeType = libraryFile.mime_type
          fileSize = libraryFile.file_size
        }
      }
      if (videoFile.value) {
        const form = new FormData()
        form.append('file', videoFile.value)
        const uploaded = await api.post<{ url: string; mime_type: string; file_size: number }>(
          '/api/v1/backgrounds/video-upload', form, true,
        )
        mediaUrl = uploaded.url
        mimeType = uploaded.mime_type
        fileSize = uploaded.file_size
      }
      if (!mediaUrl) {
        throw new Error('视频来源地址为空，请重新选择文件管理视频、本地视频或外部 URL')
      }
      if (!mimeType && videoFile.value) mimeType = videoFile.value.type
      await api.post('/api/v1/backgrounds', {
        image_id: null,
        media_type: 'video',
        media_url: mediaUrl,
        poster_url: posterUrl.value.trim(),
        mime_type: mimeType,
        file_size: fileSize,
        theme: uploadForm.value.theme,
        device: uploadForm.value.device,
        sort_order: backgrounds.value.length,
      }, true)
      ElMessage.success('视频背景添加成功')
      showUploadDialog.value = false
      await loadBackgrounds()
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '视频背景添加失败'
      ElMessage.error(message)
      console.error('[BackgroundList] video background create failed', {
        error: err,
        mediaType: mediaType.value,
        selectedLibraryFileId: selectedLibraryFileId.value,
        hasLocalFile: Boolean(videoFile.value),
        externalUrl: externalUrl.value.trim(),
      })
    } finally { uploading.value = false }
    return
  }
  if (!selectedImages.value.length && !selectedImage.value) {
    showImagePicker.value = true
    return
  }

  uploading.value = true
  try {
    const images = selectedImages.value.length ? selectedImages.value : [selectedImage.value!]
    const results = await Promise.allSettled(
      images.map((image, index) =>
        api.post(
          '/api/v1/backgrounds',
          {
            image_id: image.id,
            theme: uploadForm.value.theme,
            device: uploadForm.value.device,
            sort_order: backgrounds.value.length + index,
          },
          true,
        ),
      ),
    )
    const failed = results.filter((result) => result.status === 'rejected').length
    ElMessage[failed ? 'warning' : 'success'](
      failed ? `添加完成，${failed} 张失败` : `成功添加 ${images.length} 张`,
    )
    showUploadDialog.value = false
    loadBackgrounds()
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '上传失败')
  } finally {
    uploading.value = false
  }
}

function handleImageSelected(image: PickerImage) {
  selectedImage.value = image
  showImagePicker.value = false
}

function handleImagesSelected(images: PickerImage[]) {
  selectedImages.value = images
  selectedImage.value = images[0] ?? null
  showImagePicker.value = false
}

function toggleSelection(id: number) {
  selectedIds.value = selectedIds.value.includes(id)
    ? selectedIds.value.filter((item) => item !== id)
    : [...selectedIds.value, id]
}

async function handleBatchDelete() {
  if (!selectedIds.value.length) return
  try {
    await ElMessageBox.confirm(`确定移除选中的 ${selectedIds.value.length} 张背景图？`, '确认', {
      type: 'warning',
    })
    deleting.value = true
    const results = await Promise.allSettled(
      selectedIds.value.map((id) => api.delete(`/api/v1/backgrounds/${id}`)),
    )
    const failed = results.filter((result) => result.status === 'rejected').length
    ElMessage[failed ? 'warning' : 'success'](
      failed ? `删除完成，${failed} 张失败` : '批量删除成功',
    )
    selectedIds.value = []
    await loadBackgrounds()
  } catch {
    // 用户取消删除
  } finally {
    deleting.value = false
  }
}

/** 删除背景图记录 */
async function handleDelete(item: BackgroundItem) {
  try {
    await ElMessageBox.confirm('确定移除这张背景图？（不会删除图片文件）', '确认', {
      type: 'warning',
    })
    await api.delete(`/api/v1/backgrounds/${item.id}`)
    ElMessage.success('删除成功')
    loadBackgrounds()
  } catch {
    /* 取消 */
  }
}

/** 格式化标签 */
function formatLabel(theme: string, device: string): string {
  const t = theme === 'dark' ? '暗色' : '亮色'
  const d = device === 'desktop' ? '桌面' : '移动'
  return `${t} · ${d}`
}

onMounted(() => loadBackgrounds())
</script>

<template>
  <div class="bg-list-page">
    <div class="page-header">
      <div class="filter-row">
        <el-select
          v-model="filterTheme"
          placeholder="主题"
          clearable
          style="width: 100px"
          @change="handleFilterChange"
        >
          <el-option label="暗色" value="dark" />
          <el-option label="亮色" value="light" />
        </el-select>
        <el-select
          v-model="filterDevice"
          placeholder="设备"
          clearable
          style="width: 100px"
          @change="handleFilterChange"
        >
          <el-option label="桌面" value="desktop" />
          <el-option label="移动" value="mobile" />
        </el-select>
        <span class="page-title">共 {{ backgrounds.length }} 张</span>
      </div>
      <el-button type="primary" @click="openUpload">
        <el-icon><Plus /></el-icon>添加背景图
      </el-button>
    </div>

    <el-card shadow="never" class="table-card">
      <div class="batch-toolbar">
        <span>已选择 {{ selectedIds.length }} 张</span>
        <el-button
          type="danger"
          plain
          :loading="deleting"
          :disabled="!selectedIds.length"
          @click="handleBatchDelete"
          >批量删除</el-button
        >
      </div>
      <div v-loading="loading" class="bg-grid">
        <div v-for="bg in backgrounds" :key="bg.id" class="bg-item">
          <video v-if="bg.media_type === 'video'" :src="resolveUrl(bg.url)" :poster="bg.poster_url ? resolveUrl(bg.poster_url) : undefined" muted loop autoplay playsinline class="bg-img" />
          <img v-else :src="resolveUrl(bg.url)" alt="" class="bg-img" />
          <el-checkbox
            class="bg-check"
            :model-value="selectedIds.includes(bg.id)"
            @click.stop
            @change="toggleSelection(bg.id)"
          />
          <div class="bg-overlay">
            <el-button type="danger" size="small" @click="handleDelete(bg)">移除</el-button>
          </div>
          <span class="bg-label">{{ formatLabel(bg.theme, bg.device) }} · {{ bg.media_type === 'video' ? '视频' : '图片' }}</span>
        </div>
        <div v-if="!loading && backgrounds.length === 0" class="empty-state">暂无背景图</div>
      </div>
    </el-card>

    <!-- 上传弹窗 -->
    <el-dialog v-model="showUploadDialog" title="添加背景图" width="400px">
      <el-form label-position="top">
        <el-form-item label="主题">
          <el-radio-group v-model="uploadForm.theme">
            <el-radio value="dark">暗色</el-radio>
            <el-radio value="light">亮色</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="设备">
          <el-radio-group v-model="uploadForm.device">
            <el-radio value="desktop">桌面</el-radio>
            <el-radio value="mobile">移动</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="媒体类型">
          <el-radio-group v-model="mediaType">
            <el-radio value="image">图片</el-radio>
            <el-radio value="video">视频</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="mediaType === 'video'" label="视频来源">
          <el-select v-model="selectedLibraryFileId" clearable placeholder="从文件管理选择视频" style="width: 100%">
            <el-option v-for="file in libraryFiles" :key="file.id" :label="`${file.original_name} · ${file.mime_type}`" :value="file.id" />
          </el-select>
          <el-input v-model="externalUrl" placeholder="外部视频 URL（可选）" />
          <el-input v-model="posterUrl" placeholder="Poster URL（可选，播放失败时显示）" style="margin-top: 8px" />
          <input ref="videoInput" type="file" accept="video/mp4,video/webm,video/quicktime" hidden @change="handleVideoFileChange" />
          <el-button plain style="margin-top: 8px" @click="videoInput?.click()">选择本地视频（≤50MB）</el-button>
          <span v-if="videoFile" class="selected-image-name">{{ videoFile.name }}</span>
          <video v-if="videoPreview" :src="videoPreview" muted playsinline controls class="video-preview" @loadeddata="handleVideoPreview" @error="handleVideoPreview" />
          <span v-if="videoFile" class="video-meta">{{ videoFile.type }} · {{ formatFileSize(videoFile.size) }} · {{ videoStatus === 'error' ? '播放失败' : videoStatus === 'ready' ? '可播放' : '检测中' }}</span>
        </el-form-item>
        <el-form-item v-else label="选择图片">
          <div class="image-picker">
            <el-button plain @click="showImagePicker = true">从媒体库选择</el-button>
            <span class="selected-image-name">
              {{
                selectedImages.length
                  ? `已选择 ${selectedImages.length} 张图片`
                  : selectedImage?.original_name || '尚未选择图片'
              }}
            </span>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="handleUpload"> 确认上传 </el-button>
      </template>
    </el-dialog>
    <ImagePickerDialog
      v-model="showImagePicker"
      title="选择背景图"
      :multiple="true"
      @select-many="handleImagesSelected"
      @select="handleImageSelected"
    />
  </div>
</template>

<style scoped>
.bg-list-page {
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
.batch-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  color: var(--admin-text-secondary, #909399);
  font-size: 13px;
}
.image-picker {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
}
.selected-image-name {
  min-width: 0;
  overflow: hidden;
  color: var(--admin-text-secondary, #909399);
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.video-preview {
  width: 100%;
  max-height: 180px;
  margin-top: 10px;
  border-radius: 6px;
  background: #111;
}
.video-meta {
  display: block;
  margin-top: 6px;
  color: var(--admin-text-secondary, #909399);
  font-size: 12px;
}
.bg-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
  min-height: 200px;
}
.bg-item {
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid var(--admin-border-color, #e4e7ed);
}
.bg-check {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 2;
  padding: 4px;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.55);
}
.bg-img {
  width: 100%;
  aspect-ratio: 16 / 10;
  object-fit: cover;
  display: block;
}
.bg-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.4);
  opacity: 0;
  transition: opacity 0.2s;
}
.bg-item:hover .bg-overlay {
  opacity: 1;
}
.bg-label {
  position: absolute;
  bottom: 6px;
  left: 6px;
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
}
.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 60px 0;
  color: var(--admin-text-secondary, #909399);
}
</style>
