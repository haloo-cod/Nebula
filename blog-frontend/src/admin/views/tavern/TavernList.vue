<script setup lang="ts">
/**
 * 深夜酒馆管理 — 列表页
 * 使用 admin 接口获取所有帖子（含隐藏），支持切换可见性、删除
 */
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api/client'

/** 酒馆帖子（admin 视图，含 is_visible 和 ip_hash） */
interface TavernPost {
  id: number
  author: string
  topic: string
  body: string
  is_visible: boolean
  ip_hash: string
  created_at: string
}

const loading = ref(false)
const posts = ref<TavernPost[]>([])
const bgUrl = ref('')
const savingBg = ref(false)

/** 加载帖子列表（admin 接口，含隐藏帖） */
async function loadPosts() {
  loading.value = true
  try {
    const res = await api.get<{ items: TavernPost[]; total: number }>('/api/v1/tavern/all', true)
    posts.value = res.items
  } catch {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

/** 加载背景图配置 */
async function loadBgConfig() {
  try {
    const config = await api.get<{ bg_url: string }>('/api/v1/tavern/config', true)
    bgUrl.value = config.bg_url || ''
  } catch {
    // 静默
  }
}

/** 保存背景图 URL */
async function saveBg() {
  savingBg.value = true
  try {
    await api.put('/api/v1/tavern/config', { bg_url: bgUrl.value }, true)
    ElMessage.success('背景图已保存')
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '保存失败')
  } finally {
    savingBg.value = false
  }
}

/** 切换帖子可见性 */
async function toggleVisibility(post: TavernPost) {
  try {
    await api.put(`/api/v1/tavern/${post.id}/visibility`, { is_visible: !post.is_visible }, true)
    post.is_visible = !post.is_visible
    ElMessage.success(post.is_visible ? '已显示' : '已隐藏')
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '操作失败')
  }
}

/** 删除帖子 */
async function handleDelete(post: TavernPost) {
  try {
    await ElMessageBox.confirm('确定永久删除这条帖子？', '确认删除', { type: 'warning' })
    await api.delete(`/api/v1/tavern/${post.id}`)
    ElMessage.success('删除成功')
    loadPosts()
  } catch {
    /* 取消 */
  }
}

onMounted(() => {
  loadPosts()
  loadBgConfig()
})
</script>

<template>
  <div class="tavern-list-page">
    <div class="page-header">
      <span class="page-title">共 {{ posts.length }} 条帖子</span>
    </div>

    <el-card shadow="never" class="config-card">
      <template #header><span>酒馆背景图</span></template>
      <div class="bg-config">
        <el-input
          v-model="bgUrl"
          placeholder="图片 URL，留空使用默认暗色背景"
          clearable
          style="flex: 1"
        />
        <el-button type="primary" :loading="savingBg" @click="saveBg">保存</el-button>
      </div>
    </el-card>

    <el-card shadow="never" class="table-card">
      <el-table :data="posts as any" v-loading="loading" stripe style="width: 100%">
        <el-table-column prop="author" label="作者" width="100" />
        <el-table-column prop="topic" label="话题" width="120" />
        <el-table-column prop="body" label="内容" min-width="250">
          <template #default="{ row }: { row: any }">
            {{ row.body?.slice(0, 60) }}{{ row.body?.length > 60 ? '...' : '' }}
          </template>
        </el-table-column>
        <el-table-column prop="is_visible" label="状态" width="80">
          <template #default="{ row }: { row: any }">
            <el-tag :type="row.is_visible ? 'success' : 'info'" size="small">
              {{ row.is_visible ? '可见' : '隐藏' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="ip_hash" label="IP Hash" width="120">
          <template #default="{ row }: { row: any }">
            <span class="ip-hash">{{ row.ip_hash?.slice(0, 8) }}...</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="发布时间" width="170">
          <template #default="{ row }: { row: any }">
            {{ row.created_at?.replace('T', ' ').slice(0, 16) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }: { row: any }">
            <el-button type="warning" link size="small" @click="toggleVisibility(row)">
              {{ row.is_visible ? '隐藏' : '显示' }}
            </el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
.tavern-list-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.config-card {
  border-radius: 12px;
}
.bg-config {
  display: flex;
  gap: 8px;
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
.ip-hash {
  font-family: monospace;
  font-size: 12px;
  color: #999;
}
</style>
