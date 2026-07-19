<script setup lang="ts">
/**
 * 藏宝阁管理 — 列表页
 * 表格展示所有资源，支持按分类筛选、新建、编辑、删除
 */
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { api } from '@/api/client'

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
}

const loading = ref(false)
const treasures = ref<TreasureItem[]>([])
const categories = ref<string[]>([])
const filterCategory = ref('')
const showDialog = ref(false)
const isEdit = ref(false)
const saving = ref(false)
const editingId = ref(0)
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
    const params = filterCategory.value ? `?category=${encodeURIComponent(filterCategory.value)}` : ''
    const res = await api.get<{ items: TreasureItem[]; total: number }>(`/api/v1/treasures${params}`, true)
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
  } catch { /* 静默 */ }
}

/** 筛选分类变化 */
function handleCategoryChange() {
  loadData()
}

/** 打开新建弹窗 */
function openCreate() {
  isEdit.value = false
  form.value = { slug: '', title: '', description: '', category: '', icon: '', url: '', download_file: '', tags: '', sort_order: 0 }
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
  if (!isEdit.value && !form.value.slug.trim()) {
    ElMessage.warning('请填写 Slug')
    return
  }

  saving.value = true
  try {
    const payload = {
      ...form.value,
      tags: form.value.tags ? form.value.tags.split(',').map((t) => t.trim()).filter(Boolean) : [],
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
  } catch { /* 取消 */ }
}

onMounted(() => {
  loadData()
  loadCategories()
})
</script>

<template>
  <div class="treasure-list-page">
    <div class="page-header">
      <div class="filter-row">
        <el-select v-model="filterCategory" placeholder="全部分类" clearable style="width: 140px" @change="handleCategoryChange">
          <el-option v-for="cat in categories" :key="cat" :label="cat" :value="cat" />
        </el-select>
        <span class="page-title">共 {{ treasures.length }} 项</span>
      </div>
      <el-button type="primary" @click="openCreate">
        <el-icon><Plus /></el-icon>新增资源
      </el-button>
    </div>

    <el-card shadow="never" class="table-card">
      <el-table :data="(treasures as any)" v-loading="loading" stripe style="width: 100%">
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
            <el-tag v-for="tag in row.tags" :key="tag" size="small" style="margin-right: 4px">{{ tag }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="sort_order" label="排序" width="60" />
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
          <el-form-item label="Slug" v-if="!isEdit">
            <el-input v-model="form.slug" placeholder="url-friendly-slug" />
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
        <el-form-item label="下载文件路径（可选）">
          <el-input v-model="form.download_file" placeholder="留空则无下载功能" />
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
        <el-button type="primary" :loading="saving" @click="handleSave">{{ isEdit ? '更新' : '创建' }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.treasure-list-page { display: flex; flex-direction: column; gap: 16px; }
.page-header { display: flex; justify-content: space-between; align-items: center; }
.filter-row { display: flex; align-items: center; gap: 12px; }
.page-title { font-size: 14px; color: var(--admin-text-secondary, #909399); }
.table-card { border-radius: 12px; }
.icon-cell { font-size: 20px; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0 24px; }
</style>
