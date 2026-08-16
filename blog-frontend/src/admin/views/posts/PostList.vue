<script setup lang="ts">
/**
 * 文章管理 — 列表页
 * 表格展示所有文章，支持搜索、新建、编辑、删除
 */
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Download, MoreFilled, Plus, Upload } from '@element-plus/icons-vue'
import { api, BASE_URL, getToken } from '@/api/client'
import { useAdminTable } from '@/admin/composables/useAdminTable'
import { downloadWithProgress } from '@/utils/download'

/** 文章列表项（匹配后端 PostListItem） */
interface PostItem {
  id: number
  slug: string
  title: string
  description: string
  date: string
  cover_url: string
  category: string
  tags: string[]
  is_draft: boolean
  is_pinned: boolean
  created_at: string
}

const router = useRouter()
const selectedPosts = ref<PostItem[]>([])
const importing = ref(false)
const fileInputRef = ref<HTMLInputElement | null>(null)
const downloading = ref(false)

const {
  loading,
  data,
  keyword,
  pagination,
  loadData,
  handleSearch,
  handlePageChange,
  handleSizeChange,
  handleDelete,
} = useAdminTable<PostItem>({
  fetchData: async ({ page, pageSize, keyword: kw }) => {
    const params = new URLSearchParams({
      page: String(page),
      page_size: String(pageSize),
      include_drafts: 'true',
    })
    if (kw) params.set('category', kw)
    const res = await api.get<{ items: PostItem[]; total: number }>(`/api/v1/posts?${params}`, true)
    return res
  },
  deleteItem: async (item) => {
    await api.delete(`/api/v1/posts/${item.slug}`)
  },
  defaultPageSize: 15,
})

/** 跳转到编辑页 */
function goEdit(slug: string) {
  router.push(`/admin/posts/${slug}`)
}

/** 跳转到新建页 */
function goCreate() {
  router.push('/admin/posts/new')
}

/** 更新当前页文章选择。 */
function handleSelectionChange(rows: unknown[]) {
  selectedPosts.value = rows as PostItem[]
}

/** 下载单篇 Markdown。 */
async function downloadPost(post: PostItem) {
  try {
    await downloadWithProgress(
      `${BASE_URL}/api/v1/posts/${encodeURIComponent(post.slug)}/download`,
      `${post.slug}.md`,
      {
        headers: { Authorization: `Bearer ${getToken() ?? ''}` },
      },
    )
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '下载失败')
  }
}

/** 打开 Markdown 导入选择器。 */
function openImport() {
  if (!importing.value) fileInputRef.value?.click()
}

/** 导入单篇 Markdown，并让后端按草稿创建。 */
async function handleImport(event: Event) {
  const input = event.target as HTMLInputElement
  const files = Array.from(input.files ?? [])
  if (files.length === 0) return
  importing.value = true
  try {
    const previewForm = new FormData()
    files.forEach((file) => previewForm.append('files', file))
    const previewResponse = await fetch(`${BASE_URL}/api/v1/posts/import-preview`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${getToken() ?? ''}` },
      body: previewForm,
      credentials: 'include',
    })
    if (!previewResponse.ok) {
      const body = await previewResponse.json().catch(() => ({ detail: '预览失败' }))
      throw new Error(body.detail || '预览失败')
    }
    const previews = (await previewResponse.json()) as Array<{
      filename: string
      title: string
      slug: string
    }>
    await ElMessageBox.confirm(
      previews.map((item) => `${item.filename} -> ${item.title} (${item.slug})`).join('\n'),
      `确认导入 ${previews.length} 篇 Markdown？`,
      { confirmButtonText: '继续', cancelButtonText: '取消', type: 'info' },
    )
    const conflict = await ElMessageBox.prompt(
      'slug 冲突处理：skip / overwrite / rename',
      '导入选项',
      {
        inputValue: 'skip',
        inputPattern: /^(skip|overwrite|rename)$/,
        inputErrorMessage: '请输入 skip、overwrite 或 rename',
        confirmButtonText: '开始导入',
        cancelButtonText: '取消',
      },
    )
    const formData = new FormData()
    files.forEach((file) => formData.append('files', file))
    formData.append('conflict', conflict.value)
    const response = await fetch(`${BASE_URL}/api/v1/posts/import-batch`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${getToken() ?? ''}` },
      body: formData,
      credentials: 'include',
    })
    if (!response.ok) {
      const body = await response.json().catch(() => ({ detail: '导入失败' }))
      throw new Error(body.detail || '导入失败')
    }
    ElMessage.success('Markdown 导入完成，文章已保存为草稿')
    await loadData()
  } catch (err: unknown) {
    if (err !== 'cancel' && err !== 'close')
      ElMessage.error(err instanceof Error ? err.message : '导入失败')
  } finally {
    importing.value = false
    input.value = ''
  }
}

/** 创建选中文章的 ZIP，并轮询后台任务。 */
async function downloadSelectedZip() {
  if (selectedPosts.value.length === 0 || downloading.value) return
  downloading.value = true
  try {
    const response = await fetch(`${BASE_URL}/api/v1/posts/download-jobs`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${getToken() ?? ''}`,
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({
        slugs: selectedPosts.value.map((post) => post.slug),
        archive_name: 'starlit-posts',
        include_images: true,
      }),
    })
    if (!response.ok) throw new Error('创建文章 ZIP 任务失败')
    const created = (await response.json()) as { id: number }
    for (let attempt = 0; attempt < 300; attempt += 1) {
      await new Promise((resolve) => window.setTimeout(resolve, 700))
      const statusResponse = await fetch(`${BASE_URL}/api/v1/posts/download-jobs/${created.id}`, {
        headers: { Authorization: `Bearer ${getToken() ?? ''}` },
        credentials: 'include',
      })
      if (!statusResponse.ok) throw new Error('读取文章 ZIP 任务失败')
      const job = (await statusResponse.json()) as {
        status: string
        download_url: string | null
        error_message: string
      }
      if (job.status === 'failed') throw new Error(job.error_message || '文章 ZIP 打包失败')
      if (job.status === 'completed' && job.download_url) {
        await downloadWithProgress(`${BASE_URL}${job.download_url}`, 'starlit-posts.zip', {
          headers: { Authorization: `Bearer ${getToken() ?? ''}` },
        })
        break
      }
      if (attempt === 299) throw new Error('文章 ZIP 打包超时，请稍后重试')
    }
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '文章 ZIP 下载失败')
  } finally {
    downloading.value = false
  }
}

onMounted(() => loadData())
</script>

<template>
  <div class="post-list-page">
    <!-- 顶部操作栏 -->
    <div class="page-header">
      <el-input
        v-model="keyword"
        placeholder="搜索分类..."
        clearable
        style="width: 240px"
        @keyup.enter="handleSearch"
      />
      <div class="header-actions">
        <input
          ref="fileInputRef"
          type="file"
          accept=".md,text/markdown"
          multiple
          hidden
          @change="handleImport"
        />
        <el-button :loading="importing" @click="openImport">
          <el-icon><Upload /></el-icon>导入 Markdown
        </el-button>
        <el-button type="primary" @click="goCreate">
          <el-icon><Plus /></el-icon>新建文章
        </el-button>
      </div>
    </div>

    <!-- 文章表格 -->
    <el-card shadow="never" class="table-card">
      <div class="table-toolbar">
        <span>已选择 {{ selectedPosts.length }} 篇</span>
        <el-button
          :disabled="selectedPosts.length === 0"
          :loading="downloading"
          @click="downloadSelectedZip"
        >
          <el-icon><Download /></el-icon>打包下载
        </el-button>
      </div>
      <!-- 移动端卡片列表 -->
      <div class="post-mobile-list">
        <div v-for="row in data" :key="row.slug" class="post-mobile-card">
          <div class="post-mobile-head">
            <div class="post-mobile-title-wrap">
              <div class="post-mobile-title">
                <el-tag v-if="row.is_pinned" type="danger" size="small">置顶</el-tag>
                <el-tag v-if="row.is_draft" type="info" size="small">草稿</el-tag>
                <span>{{ row.title }}</span>
              </div>
              <div class="post-mobile-meta">
                <span v-if="row.category">{{ row.category }}</span>
                <span>{{ row.date }}</span>
              </div>
            </div>
            <el-dropdown trigger="click">
              <el-button circle :icon="MoreFilled" aria-label="更多操作" />
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="goEdit(row.slug)">编辑</el-dropdown-item>
                  <el-dropdown-item @click="downloadPost(row)">下载</el-dropdown-item>
                  <el-dropdown-item divided @click="handleDelete(row, `「${row.title}」`)">
                    删除
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
          <div v-if="row.tags.length" class="post-mobile-tags">
            <el-tag v-for="tag in row.tags" :key="tag" size="small">{{ tag }}</el-tag>
          </div>
        </div>
        <el-empty v-if="data.length === 0" description="暂无文章" :image-size="72" />
      </div>

      <!-- 桌面端表格 -->
      <el-table
        :data="data as any"
        v-loading="loading"
        stripe
        class="post-desktop-table"
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="48" />
        <el-table-column prop="title" label="标题" min-width="200">
          <template #default="{ row }">
            <div class="title-cell">
              <el-tag v-if="row.is_pinned" type="danger" size="small" class="pin-tag">置顶</el-tag>
              <el-tag v-if="row.is_draft" type="info" size="small" class="draft-tag">草稿</el-tag>
              <span class="title-text">{{ row.title }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="category" label="分类" width="100" />
        <el-table-column prop="tags" label="标签" min-width="150">
          <template #default="{ row }">
            <el-tag v-for="tag in row.tags" :key="tag" size="small" class="tag-item">{{
              tag
            }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="date" label="日期" width="120" />
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }: { row: any }">
            <el-button type="primary" link size="small" @click="goEdit(row.slug)">编辑</el-button>
            <el-button type="success" link size="small" @click="downloadPost(row)">下载</el-button>
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

      <!-- 分页 -->
      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 15, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.post-list-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions,
.table-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
}

.table-toolbar {
  justify-content: space-between;
  margin-bottom: 12px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.table-card {
  border-radius: 12px;
}

.title-cell {
  display: flex;
  align-items: center;
  gap: 6px;
}

.title-text {
  font-weight: 500;
}

.pin-tag,
.draft-tag {
  flex-shrink: 0;
}

.tag-item {
  margin-right: 4px;
  margin-bottom: 2px;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

/* 移动端卡片列表（默认隐藏，窄屏替换表格） */
.post-mobile-list {
  display: none;
  flex-direction: column;
  gap: 12px;
}

.post-mobile-card {
  padding: 14px;
  border: 1px solid var(--admin-border-color, #e4e7ed);
  border-radius: 12px;
  background: var(--admin-panel-bg, #ffffff);
}

.post-mobile-head {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.post-mobile-title-wrap {
  flex: 1;
  min-width: 0;
}

.post-mobile-title {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  color: var(--admin-text-color, #303133);
  font-size: 14px;
  font-weight: 650;
}

.post-mobile-title span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.post-mobile-meta {
  display: flex;
  gap: 10px;
  margin-top: 5px;
  color: var(--admin-text-secondary, #909399);
  font-size: 12px;
}

.post-mobile-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 10px;
}

@media (max-width: 767px) {
  .page-header {
    align-items: stretch;
    flex-direction: column;
  }

  .page-header > .el-input {
    width: 100% !important;
  }

  .header-actions {
    width: 100%;
  }

  .header-actions > * {
    flex: 1;
  }

  .post-desktop-table {
    display: none;
  }

  .post-mobile-list {
    display: flex;
  }

  .pagination-wrap {
    justify-content: center;
  }
}
</style>
