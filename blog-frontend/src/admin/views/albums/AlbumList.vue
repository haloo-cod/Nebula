<script setup lang="ts">
/**
 * 相册管理 — 列表页 + 照片管理
 * 两级：相册列表 → 点击进入照片管理（添加/删除/排序）
 */
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, ArrowLeft } from '@element-plus/icons-vue'
import { api, getToken, resolveUrl, BASE_URL } from '@/api/client'
import ImagePickerDialog, { type PickerImage } from '@/admin/components/ImagePickerDialog.vue'

/** 相册列表项 */
interface AlbumItem {
  id: number
  title: string
  description: string
  orientation: string
  cover_url: string
  cover_image_id: number | null
  photo_count: number
  date: string
  created_at: string
}

/** 照片项 */
interface PhotoItem {
  id: number
  url: string
  caption: string | null
  sort_order: number
  created_at: string
}

/** 相册详情（含照片列表） */
interface AlbumDetail extends AlbumItem {
  photos: PhotoItem[]
}

// ============ 相册列表状态 ============
const loading = ref(false)
const albums = ref<AlbumItem[]>([])
const showAlbumDialog = ref(false)
const isEditAlbum = ref(false)
const savingAlbum = ref(false)
const albumForm = ref({
  title: '',
  description: '',
  orientation: 'portrait',
  cover_image_id: null as number | null,
})
const editingAlbumId = ref(0)
const showCoverPicker = ref(false)

// ============ 照片管理状态 ============
const currentAlbum = ref<AlbumDetail | null>(null)
const loadingPhotos = ref(false)
const uploading = ref(false)
const photoInputRef = ref<HTMLInputElement | null>(null)
const savingPhotoId = ref<number | null>(null)
const showPhotoPicker = ref(false)

/** 加载相册列表 */
async function loadAlbums() {
  loading.value = true
  try {
    const res = await api.get<{ items: AlbumItem[]; total: number }>('/api/v1/albums', true)
    albums.value = res.items
  } catch {
    ElMessage.error('加载相册失败')
  } finally {
    loading.value = false
  }
}

/** 打开新建相册弹窗 */
function openCreateAlbum() {
  isEditAlbum.value = false
  albumForm.value = { title: '', description: '', orientation: 'portrait', cover_image_id: null }
  showAlbumDialog.value = true
}

/** 打开编辑相册弹窗 */
function openEditAlbum(album: AlbumItem) {
  isEditAlbum.value = true
  editingAlbumId.value = album.id
  albumForm.value = {
    title: album.title,
    description: album.description,
    orientation: album.orientation,
    cover_image_id: album.cover_image_id,
  }
  showAlbumDialog.value = true
}

function handleCoverSelected(image: PickerImage) {
  albumForm.value.cover_image_id = image.id
}

/** 保存相册 */
async function saveAlbum() {
  if (!albumForm.value.title.trim()) {
    ElMessage.warning('请填写相册标题')
    return
  }
  savingAlbum.value = true
  try {
    if (isEditAlbum.value) {
      await api.put(`/api/v1/albums/${editingAlbumId.value}`, albumForm.value, true)
      ElMessage.success('更新成功')
    } else {
      await api.post('/api/v1/albums', albumForm.value, true)
      ElMessage.success('创建成功')
    }
    showAlbumDialog.value = false
    loadAlbums()
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '保存失败')
  } finally {
    savingAlbum.value = false
  }
}

/** 删除相册 */
async function deleteAlbum(album: AlbumItem) {
  try {
    await ElMessageBox.confirm(`确定删除相册「${album.title}」？所有照片将同时删除。`, '确认删除', {
      type: 'warning',
    })
    await api.delete(`/api/v1/albums/${album.id}`)
    ElMessage.success('删除成功')
    loadAlbums()
  } catch {
    /* 取消 */
  }
}

/** 进入照片管理 */
async function enterPhotoManage(album: AlbumItem) {
  loadingPhotos.value = true
  try {
    const detail = await api.get<AlbumDetail>(`/api/v1/albums/${album.id}`, true)
    currentAlbum.value = detail
  } catch {
    ElMessage.error('加载照片失败')
  } finally {
    loadingPhotos.value = false
  }
}

/** 返回相册列表 */
function backToList() {
  currentAlbum.value = null
}

/** 显式打开照片选择器，避免 el-button 嵌套 label 时点击失效 */
function openPhotoPicker() {
  if (!uploading.value) photoInputRef.value?.click()
}

/** 上传照片并关联到当前相册 */
async function handlePhotoUpload(event: Event) {
  const input = event.target as HTMLInputElement
  const files = Array.from(input.files ?? [])
  if (!files.length || !currentAlbum.value) return
  uploading.value = true
  let success = 0
  let failed = 0
  try {
    for (const file of files) {
      try {
        const formData = new FormData()
        formData.append('file', file)
        const token = getToken()
        const uploadResp = await fetch(`${BASE_URL}/api/v1/images/upload`, {
          method: 'POST',
          headers: token ? { Authorization: `Bearer ${token}` } : {},
          body: formData,
          credentials: 'include',
        })
        if (!uploadResp.ok) {
          const error = await uploadResp.json().catch(() => ({ detail: '图片上传失败' }))
          throw new Error(error.detail || '图片上传失败')
        }
        const imageData = await uploadResp.json()
        await api.post(
          `/api/v1/albums/${currentAlbum.value.id}/photos`,
          { image_id: imageData.id },
          true,
        )
        success++
      } catch {
        failed++
      }
    }
    const detail = await api.get<AlbumDetail>(`/api/v1/albums/${currentAlbum.value.id}`, true)
    currentAlbum.value = detail
    ElMessage[failed ? 'warning' : 'success'](
      failed ? `${success} 张成功，${failed} 张失败` : `成功添加 ${success} 张照片`,
    )
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '上传失败')
  } finally {
    uploading.value = false
    input.value = '' // 重置文件选择
  }
}

/** 从图片库选择已有图片并关联到当前相册。 */
async function handlePhotoSelected(images: PickerImage[]) {
  if (!currentAlbum.value || !images.length) return
  uploading.value = true
  try {
    const results = await Promise.allSettled(
      images.map((image) =>
        api.post(`/api/v1/albums/${currentAlbum.value!.id}/photos`, { image_id: image.id }, true),
      ),
    )
    const failed = results.filter((result) => result.status === 'rejected').length
    const success = images.length - failed
    const detail = await api.get<AlbumDetail>(`/api/v1/albums/${currentAlbum.value.id}`, true)
    currentAlbum.value = detail
    ElMessage[failed ? 'warning' : 'success'](
      failed ? `${success} 张成功，${failed} 张失败` : `成功添加 ${success} 张照片`,
    )
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '添加照片失败')
  } finally {
    uploading.value = false
  }
}

/** 保存照片说明字段。 */
async function savePhoto(photo: PhotoItem) {
  if (!currentAlbum.value) return
  savingPhotoId.value = photo.id
  try {
    await api.put(
      `/api/v1/albums/${currentAlbum.value.id}/photos/${photo.id}`,
      { caption: photo.caption || '' },
      true,
    )
    ElMessage.success('照片信息已保存')
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '保存照片信息失败')
  } finally {
    savingPhotoId.value = null
  }
}

/** 删除照片 */
async function deletePhoto(photo: PhotoItem) {
  if (!currentAlbum.value) return
  try {
    await ElMessageBox.confirm('确定删除这张照片？', '确认', { type: 'warning' })
    await api.delete(`/api/v1/albums/${currentAlbum.value.id}/photos/${photo.id}`)
    ElMessage.success('删除成功')
    // 刷新
    const detail = await api.get<AlbumDetail>(`/api/v1/albums/${currentAlbum.value.id}`, true)
    currentAlbum.value = detail
  } catch {
    /* 取消 */
  }
}

onMounted(() => loadAlbums())
</script>

<template>
  <div class="album-list-page">
    <!-- 相册列表视图 -->
    <template v-if="!currentAlbum">
      <div class="page-header">
        <span class="page-title">共 {{ albums.length }} 个相册</span>
        <el-button type="primary" @click="openCreateAlbum">
          <el-icon><Plus /></el-icon>新建相册
        </el-button>
      </div>

      <el-card shadow="never" class="table-card">
        <el-table :data="albums as any" v-loading="loading" stripe style="width: 100%">
          <el-table-column prop="title" label="标题" min-width="150" />
          <el-table-column prop="description" label="描述" min-width="200">
            <template #default="{ row }: { row: any }">
              {{ row.description?.slice(0, 40) }}{{ row.description?.length > 40 ? '...' : '' }}
            </template>
          </el-table-column>
          <el-table-column prop="orientation" label="方向" width="80">
            <template #default="{ row }: { row: any }">
              {{ row.orientation === 'portrait' ? '竖版' : '横版' }}
            </template>
          </el-table-column>
          <el-table-column prop="photo_count" label="照片数" width="80" />
          <el-table-column prop="date" label="日期" width="100" />
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }: { row: any }">
              <el-button type="primary" link size="small" @click="enterPhotoManage(row)"
                >照片</el-button
              >
              <el-button type="primary" link size="small" @click="openEditAlbum(row)"
                >编辑</el-button
              >
              <el-button type="danger" link size="small" @click="deleteAlbum(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </template>

    <!-- 照片管理视图 -->
    <template v-else>
      <div class="page-header">
        <el-button @click="backToList">
          <el-icon><ArrowLeft /></el-icon>返回相册列表
        </el-button>
        <span class="page-title"
          >{{ currentAlbum.title }} — {{ currentAlbum.photos.length }} 张照片</span
        >
        <div class="upload-control">
          <el-button type="primary" :loading="uploading" @click="openPhotoPicker">
            <el-icon><Plus /></el-icon>上传照片
          </el-button>
          <el-button :disabled="uploading" @click="showPhotoPicker = true">
            从图片库选择
          </el-button>
          <input
            ref="photoInputRef"
            type="file"
            accept="image/*"
            multiple
            class="file-input"
            tabindex="-1"
            @change="handlePhotoUpload"
          />
        </div>
      </div>

      <el-card shadow="never" class="table-card">
        <div v-loading="loadingPhotos" class="photo-grid">
          <div v-for="photo in currentAlbum.photos" :key="photo.id" class="photo-item">
            <img :src="resolveUrl(photo.url)" alt="" class="photo-thumb" />
            <div class="photo-actions">
              <el-button type="danger" size="small" @click="deletePhoto(photo)">删除</el-button>
            </div>
            <div class="photo-fields">
              <el-input v-model="photo.caption" size="small" placeholder="照片说明" clearable />
              <el-button
                size="small"
                :loading="savingPhotoId === photo.id"
                @click="savePhoto(photo)"
                >保存</el-button
              >
            </div>
          </div>
          <div v-if="currentAlbum.photos.length === 0" class="empty-state">
            暂无照片，点击上方按钮添加
          </div>
        </div>
      </el-card>
    </template>

    <!-- 新建/编辑相册弹窗 -->
    <el-dialog
      v-model="showAlbumDialog"
      :title="isEditAlbum ? '编辑相册' : '新建相册'"
      width="440px"
    >
      <el-form label-position="top">
        <el-form-item label="标题">
          <el-input v-model="albumForm.title" placeholder="相册标题" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="albumForm.description"
            type="textarea"
            :rows="2"
            placeholder="相册描述"
          />
        </el-form-item>
        <el-form-item label="照片方向">
          <el-radio-group v-model="albumForm.orientation">
            <el-radio value="portrait">竖版 (3:4)</el-radio>
            <el-radio value="landscape">横版 (4:3)</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="相册封面">
          <div class="cover-picker">
            <span>{{
              albumForm.cover_image_id ? `已选择图片 #${albumForm.cover_image_id}` : '未设置封面'
            }}</span>
            <el-button @click="showCoverPicker = true">从已上传图片选择</el-button>
            <el-button v-if="albumForm.cover_image_id" @click="albumForm.cover_image_id = null"
              >清空</el-button
            >
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAlbumDialog = false">取消</el-button>
        <el-button type="primary" :loading="savingAlbum" @click="saveAlbum">{{
          isEditAlbum ? '更新' : '创建'
        }}</el-button>
      </template>
    </el-dialog>
    <ImagePickerDialog
      v-model="showCoverPicker"
      title="选择相册封面"
      @select="handleCoverSelected"
    />
    <ImagePickerDialog
      v-model="showPhotoPicker"
      title="选择相册照片"
      :multiple="true"
      @select-many="handlePhotoSelected"
    />
  </div>
</template>

<style scoped>
.album-list-page {
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
.upload-control {
  display: flex;
}
.file-input {
  display: none;
}
.cover-picker {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.photo-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
  min-height: 200px;
}
.photo-item {
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid var(--admin-border-color, #e4e7ed);
}
.photo-thumb {
  width: 100%;
  aspect-ratio: 1;
  object-fit: cover;
  display: block;
}
.photo-actions {
  position: absolute;
  top: 4px;
  right: 4px;
  opacity: 0;
  transition: opacity 0.2s;
}
.photo-item:hover .photo-actions {
  opacity: 1;
}
.photo-caption {
  display: block;
  padding: 4px 8px;
  font-size: 12px;
  color: var(--admin-text-secondary, #909399);
  background: var(--admin-fill-bg, #f5f7fa);
}
.photo-fields {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 8px;
  background: var(--admin-fill-bg, #f5f7fa);
}
.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 60px 0;
  color: #999;
}
</style>
