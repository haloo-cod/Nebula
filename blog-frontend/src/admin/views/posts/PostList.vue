<script setup lang="ts">
/**
 * 文章管理 — 列表页 + 右侧快速编辑抽屉（设计稿 D 范式）
 * 表格展示文章封面、标题、slug、分类、圆点状态与更新日期，支持快捷元信息编辑与全文编辑器跳转。
 */
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Download, MoreFilled, Plus, Upload } from '@element-plus/icons-vue'
import { api, BASE_URL, getToken, resolveUrl } from '@/api/client'
import { useAdminTable } from '@/admin/composables/useAdminTable'
import { downloadWithProgress } from '@/utils/download'
import AdminPageHeader from '@/admin/components/AdminPageHeader.vue'
import ImagePickerDialog, { type PickerImage } from '@/admin/components/ImagePickerDialog.vue'

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

/** 单篇文章详情（用于快速编辑抽屉回填与保存，保留正文内容） */
interface PostDetail extends PostItem {
  content_md: string
}

const router = useRouter()
const selectedPosts = ref<PostItem[]>([])
const statusFilter = ref<'all' | 'published' | 'draft'>('all')
const importing = ref(false)
const fileInputRef = ref<HTMLInputElement | null>(null)
const downloading = ref(false)

// 右侧快速编辑抽屉状态
const drawerVisible = ref(false)
const drawerLoading = ref(false)
const drawerSaving = ref(false)
const showCoverPicker = ref(false)
const quickTagInput = ref('')
const quickForm = ref<PostDetail | null>(null)

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
    return api.get<{ items: PostItem[]; total: number }>(`/api/v1/posts?${params}`, true)
  },
  deleteItem: async (item) => {
    await api.delete(`/api/v1/posts/${item.slug}`)
  },
  defaultPageSize: 15,
})

const filteredData = computed(() => {
  if (statusFilter.value === 'published') return data.value.filter((item) => !item.is_draft)
  if (statusFilter.value === 'draft') return data.value.filter((item) => item.is_draft)
  return data.value
})

function goEdit(slug: string) {
  void router.push(`/admin/posts/${slug}`)
}

function goCreate() {
  void router.push('/admin/posts/new')
}

function handleSelectionChange(rows: unknown[]) {
  selectedPosts.value = rows as PostItem[]
}

/** 打开右侧快速编辑抽屉并加载文章详情 */
async function openQuickEdit(post: PostItem) {
  drawerVisible.value = true
  drawerLoading.value = true
  quickTagInput.value = ''
  quickForm.value = { ...post, tags: [...post.tags], content_md: '' }
  try {
    const detail = await api.get<PostDetail>(`/api/v1/posts/${encodeURIComponent(post.slug)}`, true)
    quickForm.value = { ...detail, tags: [...detail.tags] }
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '加载文章详情失败')
    drawerVisible.value = false
  } finally {
    drawerLoading.value = false
  }
}

function addQuickTag() {
  if (!quickForm.value) return
  const tag = quickTagInput.value.trim()
  if (tag && !quickForm.value.tags.includes(tag)) {
    quickForm.value.tags.push(tag)
  }
  quickTagInput.value = ''
}

function removeQuickTag(tag: string) {
  if (!quickForm.value) return
  quickForm.value.tags = quickForm.value.tags.filter((item) => item !== tag)
}

function handleQuickCoverSelected(image: PickerImage) {
  if (quickForm.value) quickForm.value.cover_url = image.url
}

/** 保存快速编辑的元信息并保留原文内容 */
async function saveQuickEdit() {
  if (!quickForm.value) return
  if (!quickForm.value.title.trim()) {
    ElMessage.warning('请填写文章标题')
    return
  }
  drawerSaving.value = true
  try {
    await api.put(`/api/v1/posts/${encodeURIComponent(quickForm.value.slug)}`, quickForm.value, true)
    ElMessage.success('文章信息已更新')
    drawerVisible.value = false
    await loadData()
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '保存失败')
  } finally {
    drawerSaving.value = false
  }
}

/** 下载单篇 Markdown */
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

function openImport() {
  if (!importing.value) fileInputRef.value?.click()
}

async function handleImport(event: Event) {
  const input = event.target as HTMLInputElement
  const files = Array.from(input.files ?? [])
  if (files.length === 0) return
  importing.value = true
  try {
    const previewForm = new FormData()
    files.forEach((file) => previewForm.append('files', file))
    const previews = await api.post<Array<{ filename: string; title: string; slug: string }>>(
      '/api/v1/posts/import-preview',
      previewForm,
      true,
    )
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
    await api.post('/api/v1/posts/import-batch', formData, true)
    ElMessage.success('Markdown 导入完成，文章已保存为草稿')
    await loadData()
  } catch (err: unknown) {
    if (err !== 'cancel' && err !== 'close') {
      ElMessage.error(err instanceof Error ? err.message : '导入失败')
    }
  } finally {
    importing.value = false
    input.value = ''
  }
}

async function downloadSelectedZip() {
  if (selectedPosts.value.length === 0 || downloading.value) return
  downloading.value = true
  try {
    const created = await api.post<{ id: number }>(
      '/api/v1/posts/download-jobs',
      {
        slugs: selectedPosts.value.map((post) => post.slug),
        archive_name: 'starlit-posts',
        include_images: true,
      },
      true,
    )
    for (let attempt = 0; attempt < 300; attempt += 1) {
      await new Promise((resolve) => window.setTimeout(resolve, 700))
      const job = await api.get<{
        status: string
        download_url: string | null
        error_message: string
      }>(`/api/v1/posts/download-jobs/${created.id}`, true)
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

/** 将 Element Plus 默认表格行收窄为文章记录。 */
function asPost(row: unknown): PostItem {
  // Element Plus el-table 插槽默认推导为 DefaultRow，运行时即为 PostItem
  return row as PostItem
}

onMounted(() => loadData())
</script>

<template>
  <div class="admin-page">
    <AdminPageHeader
      eyebrow="CONTENT"
      title="文章管理"
      :count="`${pagination.total} 篇`"
      subtitle="管理博客博文、草稿与置顶状态，支持侧栏快速编辑元信息或进入 Markdown 全文工作台。"
    >
      <template #actions>
        <input
          ref="fileInputRef"
          type="file"
          accept=".md,text/markdown"
          multiple
          hidden
          @change="handleImport"
        />
        <el-button :loading="importing" :icon="Upload" @click="openImport">导入 Markdown</el-button>
        <el-button type="primary" :icon="Plus" @click="goCreate">新建文章</el-button>
      </template>
    </AdminPageHeader>

    <!-- 单行轻量筛选与批量操作栏 -->
    <div class="admin-toolbar">
      <div class="admin-toolbar-group">
        <el-input
          v-model="keyword"
          placeholder="按分类搜索并回车..."
          clearable
          style="width: 240px"
          @keyup.enter="handleSearch"
          @clear="handleSearch"
        />
        <div class="admin-segmented" role="tablist" aria-label="发布状态筛选">
          <button
            type="button"
            :class="{ 'is-active': statusFilter === 'all' }"
            @click="statusFilter = 'all'"
          >
            全部
          </button>
          <button
            type="button"
            :class="{ 'is-active': statusFilter === 'published' }"
            @click="statusFilter = 'published'"
          >
            已发布
          </button>
          <button
            type="button"
            :class="{ 'is-active': statusFilter === 'draft' }"
            @click="statusFilter = 'draft'"
          >
            草稿
          </button>
        </div>
      </div>

      <div class="admin-toolbar-group">
        <span v-if="selectedPosts.length > 0" class="selected-hint">
          已选 {{ selectedPosts.length }} 篇
        </span>
        <el-button
          :disabled="selectedPosts.length === 0"
          :loading="downloading"
          :icon="Download"
          @click="downloadSelectedZip"
        >
          打包下载
        </el-button>
      </div>
    </div>

    <el-card shadow="never" class="table-card">
      <!-- 移动端卡片列表 -->
      <div class="post-mobile-list">
        <div v-for="row in filteredData" :key="row.slug" class="post-mobile-card">
          <div class="post-mobile-head">
            <img v-if="row.cover_url" :src="resolveUrl(row.cover_url)" class="post-thumb" alt="" />
            <div v-else class="post-thumb post-thumb--empty">文</div>
            <div class="post-mobile-title-wrap">
              <div class="post-mobile-title">{{ row.title }}</div>
              <div class="post-mobile-meta">
                <span class="admin-status-dot" :class="row.is_draft ? 'is-warning' : 'is-success'">
                  {{ row.is_draft ? '草稿' : '已发布' }}
                </span>
                <span v-if="row.is_pinned" class="pinned-badge">置顶</span>
                <span class="admin-mono">{{ row.date }}</span>
              </div>
            </div>
            <el-dropdown trigger="click">
              <el-button circle size="small" :icon="MoreFilled" aria-label="更多操作" />
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="openQuickEdit(row)">快速编辑</el-dropdown-item>
                  <el-dropdown-item @click="goEdit(row.slug)">全文编辑</el-dropdown-item>
                  <el-dropdown-item @click="downloadPost(row)">下载 Markdown</el-dropdown-item>
                  <el-dropdown-item divided @click="handleDelete(row, `「${row.title}」`)">
                    删除
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
          <div v-if="row.tags.length" class="post-mobile-tags">
            <el-tag v-for="tag in row.tags" :key="tag" size="small" type="info">{{ tag }}</el-tag>
          </div>
        </div>
        <el-empty v-if="!loading && filteredData.length === 0" description="暂无文章" :image-size="68" />
      </div>

      <!-- 桌面端表格 -->
      <el-table
        :data="filteredData"
        v-loading="loading"
        class="post-desktop-table"
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="44" />
        <el-table-column label="文章" min-width="280">
          <template #default="{ row }">
            <div class="post-cell">
              <img v-if="row.cover_url" :src="resolveUrl(row.cover_url)" class="post-thumb" alt="" />
              <div v-else class="post-thumb post-thumb--empty">文</div>
              <div class="post-cell-copy">
                <div class="post-cell-title">
                  <span>{{ row.title }}</span>
                  <span v-if="row.is_pinned" class="pinned-badge">置顶</span>
                </div>
                <span class="post-cell-slug admin-mono">/post/{{ row.slug }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="category" label="分类" width="110">
          <template #default="{ row }">
            <el-tag v-if="row.category" size="small" type="info">{{ row.category }}</el-tag>
            <span v-else class="muted-text">—</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <span class="admin-status-dot" :class="row.is_draft ? 'is-warning' : 'is-success'">
              {{ row.is_draft ? '草稿' : '已发布' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="标签" min-width="150">
          <template #default="{ row }">
            <div class="tag-list">
              <el-tag v-for="tag in row.tags.slice(0, 3)" :key="tag" size="small" type="info">
                {{ tag }}
              </el-tag>
              <span v-if="row.tags.length > 3" class="muted-text admin-mono">
                +{{ row.tags.length - 3 }}
              </span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="date" label="日期" width="118">
          <template #default="{ row }">
            <span class="admin-mono">{{ row.date }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="205" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="openQuickEdit(asPost(row))"
              >快编</el-button
            >
            <el-button type="primary" link size="small" @click="goEdit(asPost(row).slug)"
              >正文</el-button
            >
            <el-button link size="small" @click="downloadPost(asPost(row))">下载</el-button>
            <el-button
              type="danger"
              link
              size="small"
              @click="handleDelete(asPost(row), `「${asPost(row).title}」`)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

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

    <!-- 右侧滑出快速编辑抽屉 -->
    <el-drawer
      v-model="drawerVisible"
      :title="quickForm ? `快速编辑 · ${quickForm.title}` : '快速编辑'"
      size="420px"
    >
      <div v-if="quickForm" v-loading="drawerLoading" class="quick-drawer-body">
        <div class="quick-cover-box">
          <img
            v-if="quickForm.cover_url"
            :src="resolveUrl(quickForm.cover_url)"
            alt="文章封面"
            class="quick-cover-img"
          />
          <div v-else class="quick-cover-empty">暂未设置封面图片</div>
          <div class="quick-cover-actions">
            <el-button size="small" @click="showCoverPicker = true">更换封面</el-button>
            <el-button v-if="quickForm.cover_url" size="small" link @click="quickForm.cover_url = ''">
              清除
            </el-button>
          </div>
        </div>

        <el-form label-position="top">
          <el-form-item label="文章标题">
            <el-input v-model="quickForm.title" placeholder="文章标题" />
          </el-form-item>
          <el-form-item label="所属分类">
            <el-input v-model="quickForm.category" placeholder="如：技术、随笔" />
          </el-form-item>
          <el-form-item label="发布日期">
            <el-input v-model="quickForm.date" placeholder="YYYY-MM-DD" />
          </el-form-item>
          <el-form-item label="摘要">
            <el-input v-model="quickForm.description" type="textarea" :rows="3" placeholder="简短摘要" />
          </el-form-item>
          <el-form-item label="标签">
            <div class="quick-tags">
              <el-tag
                v-for="tag in quickForm.tags"
                :key="tag"
                closable
                type="info"
                @close="removeQuickTag(tag)"
              >
                {{ tag }}
              </el-tag>
              <el-input
                v-model="quickTagInput"
                size="small"
                placeholder="+ 回车添加标签"
                style="width: 130px"
                @keyup.enter="addQuickTag"
              />
            </div>
          </el-form-item>
          <div class="quick-switches">
            <div class="switch-row">
              <span>发布状态</span>
              <el-switch
                :model-value="!quickForm.is_draft"
                active-text="已发布"
                inactive-text="草稿"
                @update:model-value="quickForm.is_draft = !$event"
              />
            </div>
            <div class="switch-row">
              <span>首页置顶</span>
              <el-switch v-model="quickForm.is_pinned" />
            </div>
          </div>
        </el-form>
      </div>

      <template #footer>
        <div class="quick-drawer-footer">
          <el-button v-if="quickForm" @click="goEdit(quickForm.slug)">打开全文编辑器</el-button>
          <el-button type="primary" :loading="drawerSaving" @click="saveQuickEdit">保存修改</el-button>
        </div>
      </template>
    </el-drawer>

    <ImagePickerDialog
      v-model="showCoverPicker"
      title="选择文章封面"
      @select="handleQuickCoverSelected"
    />
  </div>
</template>

<style scoped>
.selected-hint,
.muted-text {
  color: var(--admin-text-muted);
  font-size: 12.5px;
}

.post-cell {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.post-thumb {
  width: 44px;
  height: 34px;
  border-radius: 6px;
  object-fit: cover;
  flex-shrink: 0;
  border: 1px solid var(--admin-border-color);
}

.post-thumb--empty {
  display: grid;
  place-items: center;
  background: var(--admin-fill-bg);
  color: var(--admin-text-muted);
  font-size: 12px;
  font-weight: 600;
}

.post-cell-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.post-cell-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  color: var(--admin-text-color);
}

.post-cell-title span:first-child {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.post-cell-slug {
  color: var(--admin-text-muted);
  font-size: 11.5px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pinned-badge {
  padding: 1px 6px;
  border-radius: 4px;
  background: color-mix(in srgb, var(--admin-primary-color) 14%, transparent);
  color: var(--admin-primary-color);
  font-size: 10.5px;
  font-weight: 600;
  flex-shrink: 0;
}

.tag-list {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
}

.post-mobile-list {
  display: none;
  flex-direction: column;
  gap: 10px;
}

.post-mobile-card {
  padding: 12px;
  border: 1px solid var(--admin-border-color);
  border-radius: 10px;
  background: var(--admin-panel-bg);
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
  color: var(--admin-text-color);
  font-size: 14px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.post-mobile-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 5px;
  color: var(--admin-text-secondary);
  font-size: 12px;
}

.post-mobile-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-top: 10px;
}

.quick-drawer-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.quick-cover-box {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.quick-cover-img,
.quick-cover-empty {
  width: 100%;
  height: 156px;
  border: 1px solid var(--admin-border-color);
  border-radius: 10px;
  object-fit: cover;
}

.quick-cover-empty {
  display: grid;
  place-items: center;
  background: var(--admin-fill-bg);
  color: var(--admin-text-muted);
  font-size: 12.5px;
}

.quick-cover-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.quick-tags {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}

.quick-switches {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 12px 14px;
  border: 1px solid var(--admin-border-color);
  border-radius: 10px;
  background: var(--admin-panel-subtle);
}

.switch-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  color: var(--admin-text-color);
}

.quick-drawer-footer {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}

@media (max-width: 767px) {
  .post-desktop-table {
    display: none;
  }

  .post-mobile-list {
    display: flex;
  }
}
</style>
