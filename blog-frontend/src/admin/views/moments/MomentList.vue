<script setup lang="ts">
/**
 * 说说管理 — 列表页
 * 展示所有说说，支持新建、删除
 */
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { api } from '@/api/client'
import { useAdminTable } from '@/admin/composables/useAdminTable'

/** 说说项（匹配后端 MomentResponse） */
interface MomentItem {
  id: number
  date: string
  content: string
  mood: string
  tags: string[]
  images: string[]
  likes: number
}

/** 新建说说的表单数据 */
const showCreateDialog = ref(false)
const createForm = ref({
  content: '',
  mood: '',
  tags: '',
  images: '',
})
const creating = ref(false)

const { loading, data, pagination, loadData, handlePageChange, handleSizeChange, handleDelete } =
  useAdminTable<MomentItem>({
    fetchData: async ({ page, pageSize }) => {
      const res = await api.get<{ items: MomentItem[]; total: number }>(
        `/api/v1/moments?page=${page}&page_size=${pageSize}`,
        true,
      )
      return res
    },
    deleteItem: async (item) => {
      await api.delete(`/api/v1/moments/${item.id}`)
    },
    defaultPageSize: 10,
  })

/** 打开新建弹窗 */
function openCreate() {
  createForm.value = { content: '', mood: '', tags: '', images: '' }
  showCreateDialog.value = true
}

/** 提交新建说说 */
async function submitCreate() {
  if (!createForm.value.content.trim()) {
    ElMessage.warning('请输入说说内容')
    return
  }

  creating.value = true
  try {
    const payload = {
      content: createForm.value.content,
      mood: createForm.value.mood || '',
      tags: createForm.value.tags ? createForm.value.tags.split(',').map((t) => t.trim()).filter(Boolean) : [],
      images: createForm.value.images ? createForm.value.images.split('\n').map((u) => u.trim()).filter(Boolean) : [],
    }
    await api.post('/api/v1/moments', payload, true)
    ElMessage.success('发布成功')
    showCreateDialog.value = false
    loadData()
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '发布失败'
    ElMessage.error(msg)
  } finally {
    creating.value = false
  }
}

/** 心情 emoji 映射 */
function moodEmoji(mood: string): string {
  const map: Record<string, string> = {
    开心: '😊', 平静: '😌', 灵感: '💡', 感动: '🥹',
    疲惫: '😴', 思考: '🤔', 满足: '😋', 期待: '✨',
  }
  return mood ? (map[mood] || '📝') + ' ' + mood : ''
}

onMounted(() => loadData())
</script>

<template>
  <div class="moment-list-page">
    <!-- 顶部操作栏 -->
    <div class="page-header">
      <span class="page-title">共 {{ pagination.total }} 条说说</span>
      <el-button type="primary" @click="openCreate">
        <el-icon><Plus /></el-icon>发说说
      </el-button>
    </div>

    <!-- 说说表格 -->
    <el-card shadow="never" class="table-card">
      <el-table :data="(data as any)" v-loading="loading" stripe style="width: 100%">
        <el-table-column prop="content" label="内容" min-width="300">
          <template #default="{ row }">
            <div class="content-cell">{{ row.content.slice(0, 80) }}{{ row.content.length > 80 ? '...' : '' }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="mood" label="心情" width="100">
          <template #default="{ row }">
            <span>{{ moodEmoji(row.mood) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="images" label="图片" width="80">
          <template #default="{ row }">
            <span>{{ row.images.length }} 张</span>
          </template>
        </el-table-column>
        <el-table-column prop="likes" label="点赞" width="70" />
        <el-table-column prop="date" label="日期" width="170">
          <template #default="{ row }">
            {{ row.date.replace('T', ' ').slice(0, 16) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ row }: { row: any }">
            <el-button type="danger" link size="small" @click="handleDelete(row, '这条说说')">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </el-card>

    <!-- 新建说说弹窗 -->
    <el-dialog v-model="showCreateDialog" title="发说说" width="500px">
      <el-form label-position="top">
        <el-form-item label="内容">
          <el-input v-model="createForm.content" type="textarea" :rows="4" placeholder="说点什么..." />
        </el-form-item>
        <el-form-item label="心情">
          <el-input v-model="createForm.mood" placeholder="如：开心、思考、灵感" />
        </el-form-item>
        <el-form-item label="标签（逗号分隔）">
          <el-input v-model="createForm.tags" placeholder="标签1, 标签2" />
        </el-form-item>
        <el-form-item label="图片 URL（每行一个）">
          <el-input v-model="createForm.images" type="textarea" :rows="3" placeholder="http://..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="submitCreate">发布</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.moment-list-page {
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

.content-cell {
  line-height: 1.5;
  color: var(--admin-text-color, #303133);
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
