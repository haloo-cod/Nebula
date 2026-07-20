<script setup lang="ts">
/** 后台媒体库图片选择器：复用已有图床图片，也支持上传新图片。 */
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Upload } from '@element-plus/icons-vue'
import { api, BASE_URL, getToken, resolveUrl } from '@/api/client'

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
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  select: [image: PickerImage]
}>()

const images = ref<PickerImage[]>([])
const loading = ref(false)
const uploading = ref(false)
const uploadInput = ref<HTMLInputElement | null>(null)
const keyword = ref('')
const selectedId = ref<number | null>(null)

const filteredImages = computed(() => {
  const query = keyword.value.trim().toLowerCase()
  if (!query) return images.value
  return images.value.filter((image) => image.original_name.toLowerCase().includes(query))
})

function close() {
  emit('update:modelValue', false)
}

function formatSize(size: number): string {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

async function loadImages() {
  loading.value = true
  try {
    const response = await api.get<{ items: PickerImage[]; total: number }>(
      '/api/v1/images?page=1&page_size=100',
      true,
    )
    images.value = response.items
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '加载图片库失败')
  } finally {
    loading.value = false
  }
}

function choose(image: PickerImage) {
  selectedId.value = image.id
}

function confirm() {
  const image = images.value.find((item) => item.id === selectedId.value)
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
  uploading.value = true
  try {
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
    const image = (await response.json()) as PickerImage
    await loadImages()
    selectedId.value = image.id
    ElMessage.success('图片上传成功，已选中')
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '图片上传失败')
  } finally {
    uploading.value = false
    input.value = ''
  }
}

watch(
  () => props.modelValue,
  (visible) => {
    if (visible) {
      selectedId.value = null
      keyword.value = ''
      void loadImages()
    }
  },
)
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
      <el-input v-model="keyword" clearable placeholder="搜索文件名" />
      <el-button type="primary" plain :icon="Upload" :loading="uploading" @click="openUpload">
        上传新图片
      </el-button>
      <input
        ref="uploadInput"
        type="file"
        accept="image/*"
        class="file-input"
        @change="handleUpload"
      />
    </div>

    <div v-loading="loading" class="image-grid">
      <button
        v-for="image in filteredImages"
        :key="image.id"
        type="button"
        class="image-option"
        :class="{ selected: selectedId === image.id }"
        @click="choose(image)"
      >
        <img :src="resolveUrl(image.url)" :alt="image.original_name" />
        <span class="image-name">{{ image.original_name }}</span>
        <span class="image-meta">
          {{ image.width }} × {{ image.height }} · {{ formatSize(image.file_size) }}
        </span>
      </button>
      <el-empty v-if="!loading && filteredImages.length === 0" description="暂无可选图片" />
    </div>

    <template #footer>
      <el-button @click="close">取消</el-button>
      <el-button type="primary" @click="confirm">确认选择</el-button>
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
}
</style>
