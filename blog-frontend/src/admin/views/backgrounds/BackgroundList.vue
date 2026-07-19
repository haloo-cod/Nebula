<script setup lang="ts">
/**
 * 背景图管理 — 列表页
 * 按 theme(dark/light) + device(desktop/mobile) 分组管理背景图
 */
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { api, getToken, resolveUrl, BASE_URL } from '@/api/client'

/** 背景图项（匹配后端 BackgroundResponse） */
interface BackgroundItem {
  id: number
  url: string
  theme: string
  device: string
  sort_order: number
  created_at: string
}

const loading = ref(false)
const backgrounds = ref<BackgroundItem[]>([])
const filterTheme = ref('')
const filterDevice = ref('')
const uploading = ref(false)
const showUploadDialog = ref(false)
const uploadForm = ref({ theme: 'dark', device: 'desktop' })

/** 加载背景图列表 */
async function loadBackgrounds() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (filterTheme.value) params.set('theme', filterTheme.value)
    if (filterDevice.value) params.set('device', filterDevice.value)
    const query = params.toString() ? `?${params}` : ''
    const res = await api.get<{ items: BackgroundItem[]; total: number }>(`/api/v1/backgrounds${query}`, true)
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
  showUploadDialog.value = true
}

/** 上传图片并创建背景记录 */
async function handleUpload(event: Event) {
  const input = event.target as HTMLInputElement
  if (!input.files || !input.files[0]) return

  uploading.value = true
  try {
    // 上传图片
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

    // 创建背景记录
    await api.post('/api/v1/backgrounds', {
      image_id: imageData.id,
      theme: uploadForm.value.theme,
      device: uploadForm.value.device,
      sort_order: backgrounds.value.length,
    }, true)
    ElMessage.success('添加成功')
    showUploadDialog.value = false
    loadBackgrounds()
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '上传失败')
  } finally {
    uploading.value = false
    const input2 = document.getElementById('bg-upload-input') as HTMLInputElement
    if (input2) input2.value = ''
  }
}

/** 删除背景图记录 */
async function handleDelete(item: BackgroundItem) {
  try {
    await ElMessageBox.confirm('确定移除这张背景图？（不会删除图片文件）', '确认', { type: 'warning' })
    await api.delete(`/api/v1/backgrounds/${item.id}`)
    ElMessage.success('删除成功')
    loadBackgrounds()
  } catch { /* 取消 */ }
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
        <el-select v-model="filterTheme" placeholder="主题" clearable style="width: 100px" @change="handleFilterChange">
          <el-option label="暗色" value="dark" />
          <el-option label="亮色" value="light" />
        </el-select>
        <el-select v-model="filterDevice" placeholder="设备" clearable style="width: 100px" @change="handleFilterChange">
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
      <div v-loading="loading" class="bg-grid">
        <div v-for="bg in backgrounds" :key="bg.id" class="bg-item">
          <img :src="resolveUrl(bg.url)" alt="" class="bg-img" />
          <div class="bg-overlay">
            <el-button type="danger" size="small" @click="handleDelete(bg)">移除</el-button>
          </div>
          <span class="bg-label">{{ formatLabel(bg.theme, bg.device) }}</span>
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
        <el-form-item label="选择图片">
          <input id="bg-upload-input" type="file" accept="image/*" @change="handleUpload" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.bg-list-page { display: flex; flex-direction: column; gap: 16px; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
.filter-row { display: flex; align-items: center; gap: 12px; }
.page-title { font-size: 14px; color: var(--admin-text-secondary, #909399); }
.table-card { border-radius: 12px; }

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
  border: 1px solid #eee;
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
.bg-item:hover .bg-overlay { opacity: 1; }
.bg-label {
  position: absolute;
  bottom: 6px;
  left: 6px;
  background: rgba(0,0,0,0.6);
  color: #fff;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
}
.empty-state { grid-column: 1 / -1; text-align: center; padding: 60px 0; color: #999; }
</style>
