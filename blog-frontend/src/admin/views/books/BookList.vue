<script setup lang="ts">
/**
 * 图书管理 — 列表页
 * 展示所有图书，支持搜索、上传新书、删除
 */
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Upload } from '@element-plus/icons-vue'
import { api, getToken, resolveUrl } from '@/api/client'
import { useAdminTable } from '@/admin/composables/useAdminTable'

/** 图书列表项（匹配后端 BookListItem） */
interface BookItem {
  id: number
  slug: string
  title: string
  author: string
  description: string
  cover_url: string
  file_path: string
  created_at: string
}

const showUploadDialog = ref(false)
const uploading = ref(false)
const uploadForm = ref({
  title: '',
  author: '',
  description: '',
})
const selectedFile = ref<File | null>(null)

const { loading, data, keyword, pagination, loadData, handleSearch, handlePageChange, handleSizeChange, handleDelete } =
  useAdminTable<BookItem>({
    fetchData: async ({ page, pageSize, keyword: kw }) => {
      const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) })
      if (kw) params.set('keyword', kw)
      const res = await api.get<{ items: BookItem[]; total: number }>(`/api/v1/books?${params}`, true)
      return res
    },
    deleteItem: async (item) => {
      await api.delete(`/api/v1/books/${item.slug}`)
    },
    defaultPageSize: 15,
  })

/** 打开上传弹窗 */
function openUpload() {
  uploadForm.value = { title: '', author: '', description: '' }
  selectedFile.value = null
  showUploadDialog.value = true
}

/** 选择文件 */
function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files && input.files[0]) {
    const file = input.files[0]
    if (!file.name.endsWith('.epub')) {
      ElMessage.warning('只支持 EPUB 格式')
      return
    }
    selectedFile.value = file
    // 用文件名自动填充标题
    if (!uploadForm.value.title) {
      uploadForm.value.title = file.name.replace('.epub', '')
    }
  }
}

/** 提交上传 */
async function submitUpload() {
  if (!selectedFile.value) {
    ElMessage.warning('请选择 EPUB 文件')
    return
  }

  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    formData.append('title', uploadForm.value.title)
    formData.append('author', uploadForm.value.author)
    formData.append('description', uploadForm.value.description)

    // 使用原生 fetch 因为 api.post 会 JSON.stringify body
    const token = getToken()
    const resp = await fetch('http://localhost:8000/api/v1/books', {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    })

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: '上传失败' }))
      throw new Error(err.detail || '上传失败')
    }

    ElMessage.success('图书上传成功')
    showUploadDialog.value = false
    loadData()
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '上传失败'
    ElMessage.error(msg)
  } finally {
    uploading.value = false
  }
}

onMounted(() => loadData())
</script>

<template>
  <div class="book-list-page">
    <!-- 顶部操作栏 -->
    <div class="page-header">
      <el-input
        v-model="keyword"
        placeholder="搜索书名/作者..."
        clearable
        style="width: 240px"
        @keyup.enter="handleSearch"
      />
      <el-button type="primary" @click="openUpload">
        <el-icon><Upload /></el-icon>上传图书
      </el-button>
    </div>

    <!-- 图书表格 -->
    <el-card shadow="never" class="table-card">
      <el-table :data="(data as any)" v-loading="loading" stripe style="width: 100%">
        <el-table-column label="封面" width="80">
          <template #default="{ row }">
            <img
              v-if="row.cover_url"
              :src="resolveUrl(row.cover_url)"
              class="book-cover"
              alt=""
            />
            <div v-else class="book-cover-placeholder">无</div>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="书名" min-width="200" />
        <el-table-column prop="author" label="作者" width="150" />
        <el-table-column prop="description" label="简介" min-width="200">
          <template #default="{ row }">
            {{ row.description.slice(0, 50) }}{{ row.description.length > 50 ? '...' : '' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" width="170">
          <template #default="{ row }">
            {{ row.created_at?.slice(0, 10) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ row }: { row: any }">
            <el-button type="danger" link size="small" @click="handleDelete(row, `「${row.title}」`)">删除</el-button>
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

    <!-- 上传图书弹窗 -->
    <el-dialog v-model="showUploadDialog" title="上传图书" width="480px">
      <el-form label-position="top">
        <el-form-item label="EPUB 文件">
          <input type="file" accept=".epub" @change="handleFileChange" />
          <span v-if="selectedFile" class="file-name">{{ selectedFile.name }}</span>
        </el-form-item>
        <el-form-item label="书名">
          <el-input v-model="uploadForm.title" placeholder="留空则从文件名推断" />
        </el-form-item>
        <el-form-item label="作者">
          <el-input v-model="uploadForm.author" placeholder="作者名" />
        </el-form-item>
        <el-form-item label="简介">
          <el-input v-model="uploadForm.description" type="textarea" :rows="3" placeholder="图书简介" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="submitUpload">上传</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.book-list-page {
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

.book-cover {
  width: 40px;
  height: 56px;
  object-fit: cover;
  border-radius: 4px;
}

.book-cover-placeholder {
  width: 40px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f0f0;
  border-radius: 4px;
  font-size: 12px;
  color: #999;
}

.file-name {
  margin-left: 8px;
  font-size: 13px;
  color: #666;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
