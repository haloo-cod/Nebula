<script setup lang="ts">
/**
 * 展览管理 — 列表页
 * 展示所有展览项目，支持新建、编辑（弹窗 + Markdown textarea）、删除
 */
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { api } from '@/api/client'
import { useAdminTable } from '@/admin/composables/useAdminTable'

/** 展览项目（匹配后端 GalleryListItem） */
interface GalleryItem {
  id: number
  slug: string
  title: string
  description: string
  tags: string[]
  status: string
  year: string
  is_featured: boolean
  created_at: string
}

/** 展览详情（编辑时用） */
interface GalleryDetail extends GalleryItem {
  content_md: string
  content_html: string
  updated_at: string
}

const showDialog = ref(false)
const isEdit = ref(false)
const saving = ref(false)
const form = ref({
  slug: '',
  title: '',
  description: '',
  tags: '',
  status: '',
  year: '',
  is_featured: false,
  content_md: '',
})

const { loading, data, pagination, loadData, handleDelete } = useAdminTable<GalleryItem>({
  fetchData: async () => {
    // 展览 API 没有分页，返回全部列表
    const items = await api.get<GalleryItem[]>('/api/v1/gallery', true)
    return { items, total: items.length }
  },
  deleteItem: async (item) => {
    await api.delete(`/api/v1/gallery/${item.slug}`)
  },
})

/** 打开新建弹窗 */
function openCreate() {
  isEdit.value = false
  form.value = {
    slug: '',
    title: '',
    description: '',
    tags: '',
    status: '',
    year: '',
    is_featured: false,
    content_md: '',
  }
  showDialog.value = true
}

/** 打开编辑弹窗 */
async function openEdit(item: GalleryItem) {
  isEdit.value = true
  try {
    const detail = await api.get<GalleryDetail>(`/api/v1/gallery/${item.slug}`, true)
    form.value = {
      slug: detail.slug,
      title: detail.title,
      description: detail.description,
      tags: detail.tags.join(', '),
      status: detail.status,
      year: detail.year,
      is_featured: detail.is_featured,
      content_md: detail.content_md,
    }
    showDialog.value = true
  } catch {
    ElMessage.error('加载详情失败')
  }
}

/** 保存（新建 or 更新） */
async function handleSave() {
  if (!form.value.title.trim()) {
    ElMessage.warning('请填写标题')
    return
  }
  if (!isEdit.value && !form.value.slug.trim()) {
    ElMessage.warning('请填写 Slug')
    return
  }

  saving.value = true
  try {
    const payload = {
      slug: form.value.slug,
      title: form.value.title,
      description: form.value.description,
      tags: form.value.tags
        ? form.value.tags
            .split(',')
            .map((t) => t.trim())
            .filter(Boolean)
        : [],
      status: form.value.status,
      year: form.value.year,
      is_featured: form.value.is_featured,
      content_md: form.value.content_md,
    }

    if (isEdit.value) {
      await api.put(`/api/v1/gallery/${form.value.slug}`, payload, true)
      ElMessage.success('更新成功')
    } else {
      await api.post('/api/v1/gallery', payload, true)
      ElMessage.success('创建成功')
    }
    showDialog.value = false
    loadData()
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(() => loadData())
</script>

<template>
  <div class="gallery-list-page">
    <div class="page-header">
      <span class="page-title">共 {{ pagination.total }} 个展览项目</span>
      <el-button type="primary" @click="openCreate">
        <el-icon><Plus /></el-icon>新建项目
      </el-button>
    </div>

    <el-card shadow="never" class="table-card">
      <el-table :data="data as any" v-loading="loading" stripe style="width: 100%">
        <el-table-column prop="title" label="标题" min-width="180" />
        <el-table-column prop="status" label="状态" width="100" />
        <el-table-column prop="year" label="年份" width="80" />
        <el-table-column prop="tags" label="标签" min-width="150">
          <template #default="{ row }: { row: any }">
            <el-tag v-for="tag in row.tags" :key="tag" size="small" style="margin-right: 4px">{{
              tag
            }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_featured" label="精选" width="70">
          <template #default="{ row }: { row: any }">
            <el-tag v-if="row.is_featured" type="success" size="small">是</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }: { row: any }">
            <el-button type="primary" link size="small" @click="openEdit(row)">编辑</el-button>
            <el-button
              type="danger"
              link
              size="small"
              @click="handleDelete(row, `「${row.title}」`)"
              >删除</el-button
            >
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新建/编辑弹窗 -->
    <el-dialog v-model="showDialog" :title="isEdit ? '编辑展览' : '新建展览'" width="640px">
      <el-form label-position="top">
        <div class="form-grid">
          <el-form-item label="Slug" v-if="!isEdit">
            <el-input v-model="form.slug" placeholder="url-friendly-slug" />
          </el-form-item>
          <el-form-item label="标题">
            <el-input v-model="form.title" placeholder="项目名称" />
          </el-form-item>
          <el-form-item label="状态">
            <el-input v-model="form.status" placeholder="如：构建中、已完成" />
          </el-form-item>
          <el-form-item label="年份">
            <el-input v-model="form.year" placeholder="如：2026" />
          </el-form-item>
        </div>
        <el-form-item label="简介">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="项目简介" />
        </el-form-item>
        <el-form-item label="标签（逗号分隔）">
          <el-input v-model="form.tags" placeholder="Vue, TypeScript, WebGL" />
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="form.is_featured">精选项目</el-checkbox>
        </el-form-item>
        <el-form-item label="Markdown 正文">
          <el-input
            v-model="form.content_md"
            type="textarea"
            :rows="8"
            placeholder="项目详细介绍（Markdown）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">{{
          isEdit ? '更新' : '创建'
        }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.gallery-list-page {
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
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 24px;
}
</style>
