<script setup lang="ts">
/**
 * 相册管理 — 列表页 + 照片管理
 * 两级：相册列表 → 点击进入照片管理（添加/删除/排序）
 */
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, ArrowLeft } from '@element-plus/icons-vue'
import { api, getToken, resolveUrl, BASE_URL } from '@/api/client'

/** 相册列表项 */
interface AlbumItem {
  id: number
  title: string
  description: string
  orientation: string
  cover_url: string
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
const albumForm = ref({ title: '', description: '', orientation: 'portrait' })
const editingAlbumId = ref(0)

// ============ 照片管理状态 ============
const currentAlbum = ref<AlbumDetail | null>(null)
const loadingPhotos = ref(false)
const uploading = ref(false)

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
  albumForm.value = { title: '', description: '', orientation: 'portrait' }
  showAlbumDialog.value = true
}

/** 打开编辑相册弹窗 */
function openEditAlbum(album: AlbumItem) {
  isEditAlbum.value = true
  editingAlbumId.value = album.id
  albumForm.value = { title: album.title, description: album.description, orientation: album.orientation }
  showAlbumDialog.value = true
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
    await ElMessageBox.confirm(`确定删除相册「${album.title}」？所有照片将同时删除。`, '确认删除', { type: 'warning' })
    await api.delete(`/api/v1/albums/${album.id}`)
    ElMessage.success('删除成功')
    loadAlbums()
  } catch { /* 取消 */ }
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

/** 上传照片并关联到当前相册 */
async function handlePhotoUpload(event: Event) {
  const input = event.target as HTMLInputElement
  if (!input.files || !input.files[0] || !currentAlbum.value) return

  const file = input.files[0]
  uploading.value = true
  try {
    // 第一步：上传图片到图床
    const formData = new FormData()
    formData.append('file', file)
    const token = getToken()
    const uploadResp = await fetch(`${BASE_URL}/api/v1/images/upload`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    })
    if (!uploadResp.ok) throw new Error('图片上传失败')
    const imageData = await uploadResp.json()

    // 第二步：关联到相册
    await api.post(`/api/v1/albums/${currentAlbum.value.id}/photos`, { image_id: imageData.id }, true)
    ElMessage.success('照片添加成功')

    // 刷新照片列表
    const detail = await api.get<AlbumDetail>(`/api/v1/albums/${currentAlbum.value.id}`, true)
    currentAlbum.value = detail
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '上传失败')
  } finally {
    uploading.value = false
    input.value = '' // 重置文件选择
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
  } catch { /* 取消 */ }
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
        <el-table :data="(albums as any)" v-loading="loading" stripe style="width: 100%">
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
              <el-button type="primary" link size="small" @click="enterPhotoManage(row)">照片</el-button>
              <el-button type="primary" link size="small" @click="openEditAlbum(row)">编辑</el-button>
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
        <span class="page-title">{{ currentAlbum.title }} — {{ currentAlbum.photos.length }} 张照片</span>
        <label class="upload-btn">
          <el-button type="primary" :loading="uploading">
            <el-icon><Plus /></el-icon>添加照片
          </el-button>
          <input type="file" accept="image/*" hidden @change="handlePhotoUpload" />
        </label>
      </div>

      <el-card shadow="never" class="table-card">
        <div v-loading="loadingPhotos" class="photo-grid">
          <div v-for="photo in currentAlbum.photos" :key="photo.id" class="photo-item">
            <img :src="resolveUrl(photo.url)" alt="" class="photo-thumb" />
            <div class="photo-actions">
              <el-button type="danger" size="small" @click="deletePhoto(photo)">删除</el-button>
            </div>
            <span v-if="photo.caption" class="photo-caption">{{ photo.caption }}</span>
          </div>
          <div v-if="currentAlbum.photos.length === 0" class="empty-state">暂无照片，点击上方按钮添加</div>
        </div>
      </el-card>
    </template>

    <!-- 新建/编辑相册弹窗 -->
    <el-dialog v-model="showAlbumDialog" :title="isEditAlbum ? '编辑相册' : '新建相册'" width="440px">
      <el-form label-position="top">
        <el-form-item label="标题">
          <el-input v-model="albumForm.title" placeholder="相册标题" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="albumForm.description" type="textarea" :rows="2" placeholder="相册描述" />
        </el-form-item>
        <el-form-item label="照片方向">
          <el-radio-group v-model="albumForm.orientation">
            <el-radio value="portrait">竖版 (3:4)</el-radio>
            <el-radio value="landscape">横版 (4:3)</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAlbumDialog = false">取消</el-button>
        <el-button type="primary" :loading="savingAlbum" @click="saveAlbum">{{ isEditAlbum ? '更新' : '创建' }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.album-list-page { display: flex; flex-direction: column; gap: 16px; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
.page-title { font-size: 14px; color: var(--admin-text-secondary, #909399); }
.table-card { border-radius: 12px; }
.upload-btn { cursor: pointer; }

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
  border: 1px solid #eee;
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
.photo-item:hover .photo-actions { opacity: 1; }
.photo-caption {
  display: block;
  padding: 4px 8px;
  font-size: 12px;
  color: #666;
  background: #f9f9f9;
}
.empty-state { grid-column: 1 / -1; text-align: center; padding: 60px 0; color: #999; }
</style>
