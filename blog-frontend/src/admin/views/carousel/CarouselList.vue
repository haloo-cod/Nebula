<script setup lang="ts">
/**
 * 轮播管理 — 列表页
 * 管理首页轮播图片：添加（从图床选择）、删除、排序
 */
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { api, getToken, resolveUrl, BASE_URL } from '@/api/client'

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

/** 加载轮播列表 */
async function loadSlides() {
  loading.value = true
  try {
    const res = await api.get<{ items: CarouselSlide[]; total: number }>('/api/v1/carousel', true)
    slides.value = res.items
  } catch {
    ElMessage.error('加载轮播失败')
  } finally {
    loading.value = false
  }
}

/** 上传图片并添加到轮播 */
async function handleUpload(event: Event) {
  const input = event.target as HTMLInputElement
  if (!input.files || !input.files[0]) return

  uploading.value = true
  try {
    // 第一步：上传图片到图床
    const formData = new FormData()
    formData.append('file', input.files[0])
    const token = getToken()
    const uploadResp = await fetch(`${BASE_URL}/api/v1/images/upload`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    })
    if (!uploadResp.ok) throw new Error('图片上传失败')
    const imageData = await uploadResp.json()

    // 第二步：关联到轮播
    await api.post('/api/v1/carousel', { image_id: imageData.id, sort_order: slides.value.length }, true)
    ElMessage.success('添加成功')
    loadSlides()
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '上传失败')
  } finally {
    uploading.value = false
    input.value = ''
  }
}

/** 删除轮播项 */
async function handleDelete(slide: CarouselSlide) {
  try {
    await ElMessageBox.confirm('确定移除这张轮播图？', '确认', { type: 'warning' })
    await api.delete(`/api/v1/carousel/${slide.id}`)
    ElMessage.success('删除成功')
    loadSlides()
  } catch { /* 取消 */ }
}

onMounted(() => loadSlides())
</script>

<template>
  <div class="carousel-list-page">
    <div class="page-header">
      <span class="page-title">共 {{ slides.length }} 张轮播图</span>
      <label class="upload-btn">
        <el-button type="primary" :loading="uploading">
          <el-icon><Plus /></el-icon>添加轮播图
        </el-button>
        <input type="file" accept="image/*" hidden @change="handleUpload" />
      </label>
    </div>

    <el-card shadow="never" class="table-card">
      <div v-loading="loading" class="slide-grid">
        <div v-for="slide in slides" :key="slide.id" class="slide-item">
          <img :src="resolveUrl(slide.url)" alt="" class="slide-img" />
          <div class="slide-overlay">
            <el-button type="danger" size="small" @click="handleDelete(slide)">移除</el-button>
          </div>
          <span class="slide-order">{{ slide.sort_order }}</span>
        </div>
        <div v-if="!loading && slides.length === 0" class="empty-state">暂无轮播图</div>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.carousel-list-page { display: flex; flex-direction: column; gap: 16px; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
.page-title { font-size: 14px; color: var(--admin-text-secondary, #909399); }
.table-card { border-radius: 12px; }
.upload-btn { cursor: pointer; }

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
  border: 1px solid #eee;
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
.slide-item:hover .slide-overlay { opacity: 1; }
.slide-order {
  position: absolute;
  top: 6px;
  left: 6px;
  background: rgba(0,0,0,0.6);
  color: #fff;
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
}
.empty-state { grid-column: 1 / -1; text-align: center; padding: 60px 0; color: #999; }
</style>
