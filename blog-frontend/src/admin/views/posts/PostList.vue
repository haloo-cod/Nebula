<script setup lang="ts">
/**
 * 文章管理 — 列表页
 * 表格展示所有文章，支持搜索、新建、编辑、删除
 */
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Plus } from '@element-plus/icons-vue'
import { api } from '@/api/client'
import { useAdminTable } from '@/admin/composables/useAdminTable'

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
    const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) })
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
      <el-button type="primary" @click="goCreate">
        <el-icon><Plus /></el-icon>新建文章
      </el-button>
    </div>

    <!-- 文章表格 -->
    <el-card shadow="never" class="table-card">
      <el-table :data="data as any" v-loading="loading" stripe style="width: 100%">
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
</style>
