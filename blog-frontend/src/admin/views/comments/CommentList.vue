<script setup lang="ts">
/**
 * 评论管理 — 列表页
 * 支持按页面类型筛选（固定页面 + 博文动态选择），删除评论
 */
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api/client'

/** 评论项（匹配后端 CommentItem） */
interface CommentItem {
  id: number
  author: string
  date: string
  content: string
  avatar_color: string
  children: CommentItem[]
}

/** 评论列表响应 */
interface CommentListResponse {
  items: CommentItem[]
  total: number
}

/** 文章简要信息（用于博文选择器） */
interface PostBrief {
  slug: string
  title: string
}

const loading = ref(false)
const comments = ref<CommentItem[]>([])
const total = ref(0)

/** 评论区类型：固定页面 or 博文 */
const sourceType = ref<'page' | 'post'>('page')

/** 固定页面选中的 key */
const selectedPage = ref('about')

/** 博文选择器：文章列表 + 选中的 slug */
const postList = ref<PostBrief[]>([])
const selectedPostSlug = ref('')
const postSearchKeyword = ref('')
const loadingPosts = ref(false)

/** 预定义的固定页面选项 */
const pageOptions = [
  { label: '关于页', value: 'about' },
  { label: '友链页', value: 'friends' },
  { label: '藏宝阁', value: 'treasure' },
]

/** 计算当前实际的 page_key */
const currentPageKey = computed(() => {
  if (sourceType.value === 'post') {
    return selectedPostSlug.value ? `post:${selectedPostSlug.value}` : ''
  }
  return selectedPage.value
})

/** 加载文章列表（用于博文选择器） */
async function loadPostList() {
  loadingPosts.value = true
  try {
    const res = await api.get<{ items: PostBrief[]; total: number }>(
      '/api/v1/posts?page=1&page_size=200',
      true,
    )
    postList.value = res.items
    // 默认选中第一篇
    if (res.items.length > 0 && !selectedPostSlug.value) {
      selectedPostSlug.value = res.items[0].slug
    }
  } catch {
    // 静默处理
  } finally {
    loadingPosts.value = false
  }
}

/** 过滤后的文章列表（支持搜索） */
const filteredPosts = computed(() => {
  if (!postSearchKeyword.value) return postList.value
  const kw = postSearchKeyword.value.toLowerCase()
  return postList.value.filter(
    (p) => p.title.toLowerCase().includes(kw) || p.slug.toLowerCase().includes(kw),
  )
})

/** 加载评论 */
async function loadComments() {
  const key = currentPageKey.value
  if (!key) return

  loading.value = true
  try {
    const res = await api.get<CommentListResponse>(
      `/api/v1/comments?page_key=${encodeURIComponent(key)}`,
      true,
    )
    comments.value = res.items
    total.value = res.total
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '加载评论失败'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}

/** 删除评论 */
async function deleteComment(comment: CommentItem) {
  try {
    await ElMessageBox.confirm('确定要删除这条评论吗？', '确认删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    const key = currentPageKey.value
    await api.delete(`/api/v1/comments/${comment.id}?page_key=${encodeURIComponent(key)}`)
    ElMessage.success('删除成功')
    loadComments()
  } catch {
    // 用户取消
  }
}

/** 将评论树打平为一维数组（方便表格展示） */
function flattenComments(items: CommentItem[], depth = 0): Array<CommentItem & { _depth: number }> {
  const result: Array<CommentItem & { _depth: number }> = []
  for (const item of items) {
    result.push({ ...item, _depth: depth })
    if (item.children && item.children.length > 0) {
      result.push(...flattenComments(item.children, depth + 1))
    }
  }
  return result
}

/** 切换来源类型时加载对应数据 */
function handleSourceChange() {
  if (sourceType.value === 'post' && postList.value.length === 0) {
    loadPostList().then(() => loadComments())
  } else {
    loadComments()
  }
}

/** 切换选中的页面/文章时重新加载评论 */
function handleSelectionChange() {
  loadComments()
}

onMounted(() => loadComments())
</script>

<template>
  <div class="comment-list-page">
    <!-- 顶部筛选栏 -->
    <div class="page-header">
      <div class="filter-row">
        <el-radio-group v-model="sourceType" @change="handleSourceChange" size="default">
          <el-radio-button value="page">固定页面</el-radio-button>
          <el-radio-button value="post">博文评论</el-radio-button>
        </el-radio-group>

        <!-- 固定页面选择器 -->
        <el-select
          v-if="sourceType === 'page'"
          v-model="selectedPage"
          @change="handleSelectionChange"
          style="width: 140px; margin-left: 12px"
        >
          <el-option
            v-for="opt in pageOptions"
            :key="opt.value"
            :label="opt.label"
            :value="opt.value"
          />
        </el-select>

        <!-- 博文选择器（支持搜索） -->
        <el-select
          v-if="sourceType === 'post'"
          v-model="selectedPostSlug"
          filterable
          :filter-method="(val: string) => { postSearchKeyword = val }"
          placeholder="选择文章"
          @change="handleSelectionChange"
          :loading="loadingPosts"
          style="width: 300px; margin-left: 12px"
        >
          <el-option
            v-for="post in filteredPosts"
            :key="post.slug"
            :label="post.title"
            :value="post.slug"
          />
        </el-select>
      </div>

      <span class="total-text">共 {{ total }} 条评论</span>
    </div>

    <!-- 评论表格 -->
    <el-card shadow="never" class="table-card">
      <el-table :data="flattenComments(comments)" v-loading="loading" stripe style="width: 100%">
        <el-table-column label="层级" width="60">
          <template #default="{ row }">
            <span v-if="row._depth > 0" class="indent-mark">{{ '└'.padStart(row._depth + 1, '  ') }}</span>
            <span v-else>—</span>
          </template>
        </el-table-column>
        <el-table-column prop="author" label="作者" width="120">
          <template #default="{ row }">
            <div class="author-cell">
              <span class="avatar-dot" :style="{ background: row.avatar_color }"></span>
              {{ row.author }}
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="content" label="内容" min-width="300">
          <template #default="{ row }">
            {{ row.content.slice(0, 100) }}{{ row.content.length > 100 ? '...' : '' }}
          </template>
        </el-table-column>
        <el-table-column prop="date" label="日期" width="170">
          <template #default="{ row }">
            {{ row.date?.replace('T', ' ').slice(0, 16) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ row }: { row: any }">
            <el-button type="danger" link size="small" @click="deleteComment(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 空状态 -->
      <div v-if="!loading && comments.length === 0" class="empty-state">
        暂无评论
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.comment-list-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.filter-row {
  display: flex;
  align-items: center;
}

.total-text {
  font-size: 14px;
  color: var(--admin-text-secondary, #909399);
}

.table-card {
  border-radius: 12px;
}

.author-cell {
  display: flex;
  align-items: center;
  gap: 6px;
}

.avatar-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.indent-mark {
  color: #c0c4cc;
  font-family: monospace;
}

.empty-state {
  text-align: center;
  padding: 40px 0;
  color: var(--admin-text-secondary, #909399);
  font-size: 14px;
}
</style>
