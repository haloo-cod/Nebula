<script setup lang="ts">
/**
 * 轮播管理 — 列表页
 * 管理首页轮播图片：添加（从图床选择）、删除、排序
 */
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { api, resolveUrl } from '@/api/client'
import ImagePickerDialog, { type PickerImage } from '@/admin/components/ImagePickerDialog.vue'

/** 轮播项（匹配后端 CarouselSlideResponse） */
interface CarouselSlide {
  id: number
  url: string
  sort_order: number
  created_at: string
}

const loading = ref(false)
const slides = ref<CarouselSlide[]>([])
const uploading = ref(false)
const savingOrder = ref(false)
const draggedId = ref<number | null>(null)
const orderChanged = ref(false)
const showImagePicker = ref(false)
const selectedIds = ref<number[]>([])
const deleting = ref(false)

/** 加载轮播列表 */
async function loadSlides() {
  loading.value = true
  try {
    const res = await api.get<{ items: CarouselSlide[]; total: number }>('/api/v1/carousel', true)
    slides.value = res.items
    orderChanged.value = false
  } catch {
    ElMessage.error('加载轮播失败')
  } finally {
    loading.value = false
  }
}

/** 从媒体库选择图片并关联到轮播。 */
async function addImage(image: PickerImage) {
  uploading.value = true
  try {
    await api.post(
      '/api/v1/carousel',
      { image_id: image.id, sort_order: slides.value.length },
      true,
    )
    ElMessage.success('添加成功')
    await loadSlides()
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '上传失败')
  } finally {
    uploading.value = false
  }
}

async function addImages(images: PickerImage[]) {
  uploading.value = true
  try {
    const results = await Promise.allSettled(
      images.map((image, index) =>
        api.post(
          '/api/v1/carousel',
          { image_id: image.id, sort_order: slides.value.length + index },
          true,
        ),
      ),
    )
    const failed = results.filter((result) => result.status === 'rejected').length
    ElMessage[failed ? 'warning' : 'success'](
      failed ? `添加完成，${failed} 张失败` : `成功添加 ${images.length} 张`,
    )
    await loadSlides()
  } finally {
    uploading.value = false
  }
}

function toggleSelection(id: number) {
  selectedIds.value = selectedIds.value.includes(id)
    ? selectedIds.value.filter((item) => item !== id)
    : [...selectedIds.value, id]
}

async function handleBatchDelete() {
  if (!selectedIds.value.length) return
  try {
    await ElMessageBox.confirm(`确定移除选中的 ${selectedIds.value.length} 张轮播图？`, '确认', {
      type: 'warning',
    })
    deleting.value = true
    const results = await Promise.allSettled(
      selectedIds.value.map((id) => api.delete(`/api/v1/carousel/${id}`)),
    )
    const failed = results.filter((result) => result.status === 'rejected').length
    ElMessage[failed ? 'warning' : 'success'](
      failed ? `删除完成，${failed} 张失败` : '批量删除成功',
    )
    selectedIds.value = []
    await loadSlides()
  } catch {
    // 用户取消删除
  } finally {
    deleting.value = false
  }
}

/** 删除轮播项 */
async function handleDelete(slide: CarouselSlide) {
  try {
    await ElMessageBox.confirm('确定移除这张轮播图？', '确认', { type: 'warning' })
    await api.delete(`/api/v1/carousel/${slide.id}`)
    ElMessage.success('删除成功')
    loadSlides()
  } catch {
    /* 取消 */
  }
}

/** 拖拽开始，记录当前卡片。 */
function handleDragStart(slide: CarouselSlide) {
  draggedId.value = slide.id
}

/** 将拖拽卡片移动到目标卡片之前。 */
function handleDrop(target: CarouselSlide) {
  if (draggedId.value === null || draggedId.value === target.id) return
  const fromIndex = slides.value.findIndex((slide) => slide.id === draggedId.value)
  const targetIndex = slides.value.findIndex((slide) => slide.id === target.id)
  if (fromIndex < 0 || targetIndex < 0) return
  const [dragged] = slides.value.splice(fromIndex, 1)
  slides.value.splice(targetIndex, 0, dragged)
  slides.value.forEach((slide, index) => {
    slide.sort_order = index
  })
  orderChanged.value = true
}

/** 清理拖拽状态。 */
function handleDragEnd() {
  draggedId.value = null
}

/** 将当前卡片顺序保存到后端。 */
async function saveOrder() {
  savingOrder.value = true
  try {
    await api.put('/api/v1/carousel/reorder', { ids: slides.value.map((slide) => slide.id) }, true)
    ElMessage.success('轮播顺序已保存')
    orderChanged.value = false
    await loadSlides()
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '保存排序失败')
  } finally {
    savingOrder.value = false
  }
}

onMounted(() => loadSlides())
</script>

<template>
  <div class="carousel-list-page">
    <div class="page-header">
      <span class="page-title">共 {{ slides.length }} 张轮播图</span>
      <div class="upload-control">
        <el-button
          type="danger"
          plain
          :loading="deleting"
          :disabled="!selectedIds.length"
          @click="handleBatchDelete"
        >
          批量删除（{{ selectedIds.length }}）
        </el-button>
        <el-button v-if="orderChanged" :loading="savingOrder" @click="saveOrder"
          >保存排序</el-button
        >
        <el-button type="primary" :loading="uploading" @click="showImagePicker = true">
          <el-icon><Plus /></el-icon>添加轮播图
        </el-button>
      </div>
    </div>

    <el-card shadow="never" class="table-card">
      <div class="batch-toolbar">已选择 {{ selectedIds.length }} 张</div>
      <div v-loading="loading" class="slide-grid">
        <div
          v-for="slide in slides"
          :key="slide.id"
          class="slide-item"
          draggable="true"
          @dragstart="handleDragStart(slide)"
          @dragover.prevent
          @drop.prevent="handleDrop(slide)"
          @dragend="handleDragEnd"
        >
          <img :src="resolveUrl(slide.url)" alt="" class="slide-img" />
          <el-checkbox
            class="slide-check"
            :model-value="selectedIds.includes(slide.id)"
            @click.stop
            @change="toggleSelection(slide.id)"
          />
          <div class="slide-overlay">
            <el-button type="danger" size="small" @click="handleDelete(slide)">移除</el-button>
          </div>
          <span class="slide-order">{{ slide.sort_order }}</span>
        </div>
        <div v-if="!loading && slides.length === 0" class="empty-state">暂无轮播图</div>
      </div>
    </el-card>
    <ImagePickerDialog
      v-model="showImagePicker"
      title="选择轮播图"
      :multiple="true"
      @select-many="addImages"
      @select="addImage"
    />
  </div>
</template>

<style scoped>
.carousel-list-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.page-title {
  font-size: 14px;
  color: var(--admin-text-secondary, #909399);
}
.table-card {
  border-radius: 12px;
}
.batch-toolbar {
  margin-bottom: 12px;
  color: var(--admin-text-secondary, #909399);
  font-size: 13px;
}
.upload-control {
  display: flex;
}
.file-input {
  display: none;
}

.slide-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
  min-height: 200px;
}
.slide-item {
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid var(--admin-border-color, #e4e7ed);
  cursor: grab;
}
.slide-item:active {
  cursor: grabbing;
}
.slide-check {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 2;
  padding: 4px;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.55);
}
.slide-img {
  width: 100%;
  aspect-ratio: 16 / 9;
  object-fit: cover;
  display: block;
}
.slide-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.4);
  opacity: 0;
  transition: opacity 0.2s;
}
.slide-item:hover .slide-overlay {
  opacity: 1;
}
.slide-order {
  position: absolute;
  top: 6px;
  left: 6px;
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
}
.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 60px 0;
  color: var(--admin-text-secondary, #909399);
}
</style>
