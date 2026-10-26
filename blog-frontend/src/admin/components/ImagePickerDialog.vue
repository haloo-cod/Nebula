<script setup lang="ts">
/** 后台媒体库图片选择器：复用已有图床图片，也支持上传新图片。 */
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Upload } from '@element-plus/icons-vue'
import { api, resolveUrl } from '@/api/client'
import { uploadImage } from '@/api/images'
import { useStorageBackend } from '@/admin/composables/useStorageBackend'
import StorageBackendSelect from '@/admin/components/StorageBackendSelect.vue'

/** 图床图片记录。 */
export interface PickerImage {
  id: number
  original_name: string
  url: string
  file_size: number
  width: number
  height: number
  mime_type: string
  created_at: string
}

const props = defineProps<{
  modelValue: boolean
  title?: string
  multiple?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  select: [image: PickerImage]
  'select-many': [images: PickerImage[]]
}>()

const images = ref<PickerImage[]>([])
const loading = ref(false)
const uploading = ref(false)
const { storageBackend } = useStorageBackend()
const uploadInput = ref<HTMLInputElement | null>(null)
const keyword = ref('')
const page = ref(1)
const pageSize = ref(24)
const total = ref(0)
const error = ref('')
const selectedImage = ref<PickerImage | null>(null)
const selectedImages = ref(new Map<number, PickerImage>())
const selectedId = computed(() => selectedImage.value?.id ?? null)
const selectedIds = computed(() => [...selectedImages.value.keys()])
let requestVersion = 0
let dialogVersion = 0

/** 每次打开、关闭都开始独立的选择会话，并作废未完成的列表请求。 */
function resetPicker() {
  requestVersion++
  dialogVersion++
  images.value = []
  loading.value = false
  error.value = ''
  keyword.value = ''
  page.value = 1
  total.value = 0
  selectedImage.value = null
  selectedImages.value.clear()
}

function close() {
  resetPicker()
  emit('update:modelValue', false)
}

function formatSize(size: number): string {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

/** 只接收当前对话框最后一次列表请求的结果。 */
async function loadImages() {
  const version = ++requestVersion
  loading.value = true
  error.value = ''
  images.value = []
  const params = new URLSearchParams({
    page: String(page.value),
    page_size: String(pageSize.value),
  })
  const query = keyword.value.trim()
  if (query) params.set('keyword', query)
  try {
    const response = await api.get<{ items: PickerImage[]; total: number }>(
      `/api/v1/images?${params}`,
      true,
    )
    if (version !== requestVersion || !props.modelValue) return
    images.value = response.items
    total.value = response.total
  } catch (err: unknown) {
    if (version !== requestVersion || !props.modelValue) return
    error.value = err instanceof Error ? err.message : '加载图片库失败'
    ElMessage.error(error.value)
  } finally {
    if (version === requestVersion) loading.value = false
  }
}

function searchImages() {
  page.value = 1
  void loadImages()
}

function changePage(value: number) {
  page.value = value
  void loadImages()
}

function changePageSize(value: number) {
  pageSize.value = value
  searchImages()
}

function choose(image: PickerImage) {
  if (props.multiple) {
    if (selectedImages.value.has(image.id)) selectedImages.value.delete(image.id)
    else selectedImages.value.set(image.id, image)
    return
  }
  selectedImage.value = image
}

function confirm() {
  if (props.multiple) {
    const selected = [...selectedImages.value.values()]
    if (!selected.length) {
      ElMessage.warning('请至少选择一张图片')
      return
    }
    emit('select-many', selected)
    close()
    return
  }
  const image = selectedImage.value
  if (!image) {
    ElMessage.warning('请选择一张图片')
    return
  }
  emit('select', image)
  close()
}

function openUpload() {
  if (!uploading.value) uploadInput.value?.click()
}

async function handleUpload(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  const session = dialogVersion
  uploading.value = true
  try {
    const image = await uploadImage(file, storageBackend.value)
    if (session !== dialogVersion || !props.modelValue) return
    if (props.multiple) selectedImages.value.set(image.id, image)
    else selectedImage.value = image
    keyword.value = ''
    page.value = 1
    await loadImages()
    if (session === dialogVersion) ElMessage.success('图片上传成功，已选中')
  } catch (err: unknown) {
    if (session === dialogVersion) {
      ElMessage.error(err instanceof Error ? err.message : '图片上传失败')
    }
  } finally {
    uploading.value = false
    input.value = ''
  }
}

watch(
  () => props.modelValue,
  (visible) => {
    resetPicker()
    if (visible) void loadImages()
  },
  { immediate: true },
)

onBeforeUnmount(() => {
  requestVersion++
  dialogVersion++
})
</script>

<template>
  <el-dialog
    :model-value="modelValue"
    :title="title || '选择图片'"
    width="760px"
    append-to-body
    @close="close"
  >
    <div class="picker-toolbar">
      <el-input
        v-model="keyword"
        clearable
        placeholder="搜索全部图片文件名"
        @keyup.enter="searchImages"
        @clear="searchImages"
      />
      <el-button :disabled="uploading" @click="searchImages">搜索</el-button>
      <el-button type="primary" plain :icon="Upload" :loading="uploading" @click="openUpload">
        上传新图片
      </el-button>
      <StorageBackendSelect />
      <input
        ref="uploadInput"
        type="file"
        accept="image/*"
        class="file-input"
        @change="handleUpload"
      />
    </div>

    <el-result v-if="error" icon="error" :title="error">
      <template #extra><el-button @click="loadImages">重新加载</el-button></template>
    </el-result>
    <div v-else v-loading="loading" class="image-grid">
      <button
        v-for="image in images"
        :key="image.id"
        type="button"
        class="image-option"
        :class="{ selected: multiple ? selectedIds.includes(image.id) : selectedId === image.id }"
        :disabled="loading || uploading"
        @click="choose(image)"
      >
        <img :src="resolveUrl(image.url)" :alt="image.original_name" />
        <span class="image-name">{{ image.original_name }}</span>
        <span class="image-meta">
          {{ image.width }} × {{ image.height }} · {{ formatSize(image.file_size) }}
        </span>
      </button>
      <el-empty v-if="!loading && images.length === 0" description="暂无可选图片" />
    </div>
    <el-pagination
      :current-page="page"
      :page-size="pageSize"
      :page-sizes="[24, 48, 100]"
      :total="total"
      :disabled="uploading"
      layout="total, sizes, prev, pager, next"
      @current-change="changePage"
      @size-change="changePageSize"
    />

    <template #footer>
      <el-button @click="close">取消</el-button>
      <el-button type="primary" :disabled="loading || uploading" @click="confirm"
        >确认选择{{ multiple ? `（${selectedIds.length}）` : '' }}</el-button
      >
    </template>
  </el-dialog>
</template>

<style scoped>
.picker-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.picker-toolbar .el-input {
  max-width: 320px;
}
.file-input {
  display: none;
}
.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 12px;
  min-height: 180px;
  max-height: 480px;
  overflow-y: auto;
  padding: 2px;
}
.image-option {
  display: flex;
  flex-direction: column;
  min-width: 0;
  padding: 6px;
  border: 1px solid var(--admin-border-color, #dcdfe6);
  border-radius: 8px;
  background: transparent;
  color: var(--admin-text-color, #303133);
  text-align: left;
  cursor: pointer;
}
.image-option:hover,
.image-option.selected {
  border-color: var(--el-color-primary, #409eff);
}
.image-option.selected {
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--el-color-primary, #409eff) 22%, transparent);
}
.image-option img {
  width: 100%;
  height: 96px;
  object-fit: contain;
  border-radius: 4px;
  background: var(--admin-fill-bg, #f5f7fa);
}
.image-name,
.image-meta {
  overflow: hidden;
  margin-top: 6px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.image-name {
  font-size: 13px;
}
.image-meta {
  color: var(--admin-text-secondary, #909399);
  font-size: 11px;
}
@media (max-width: 640px) {
  .picker-toolbar {
    align-items: stretch;
    flex-direction: column;
  }
  .picker-toolbar .el-input {
    max-width: none;
  }

  .image-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    max-height: calc(100vh - 300px);
  }

  .image-option img {
    height: 82px;
  }
}
</style>
