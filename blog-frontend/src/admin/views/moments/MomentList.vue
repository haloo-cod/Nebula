<script setup lang="ts">
/**
 * 说说管理 — 列表页
 * 展示所有说说，支持新建、编辑、删除
 */
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { api, resolveUrl } from '@/api/client'
import { useAdminTable } from '@/admin/composables/useAdminTable'
import ImagePickerDialog, { type PickerImage } from '@/admin/components/ImagePickerDialog.vue'
import EmojiPicker from '@/admin/components/EmojiPicker.vue'

/** 说说项（匹配后端 MomentResponse） */
interface MomentItem {
  id: number
  date: string
  content: string
  mood: string
  mood_text: string
  tags: string[]
  images: string[]
  likes: number
}

/** 说说评论项。 */
interface MomentComment {
  id: number
  nickname: string
  content: string
  date: string
  likes: number
}

/** 新建说说的表单数据 */
const showCreateDialog = ref(false)
const editingId = ref<number | null>(null)
const createForm = ref({
  content: '',
  mood: '',
  moodText: '',
  tags: '',
  images: '',
})
const creating = ref(false)
const showImagePicker = ref(false)
const showCommentsDialog = ref(false)
const commentsLoading = ref(false)
const comments = ref<MomentComment[]>([])
const selectedMoment = ref<MomentItem | null>(null)

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
  editingId.value = null
  createForm.value = { content: '', mood: '', moodText: '', tags: '', images: '' }
  showCreateDialog.value = true
}

/** 打开已发布说说的编辑弹窗。 */
function openEdit(moment: MomentItem) {
  editingId.value = moment.id
  createForm.value = {
    content: moment.content,
    mood: moment.mood,
    moodText: moment.mood_text || '',
    tags: moment.tags.join(', '),
    images: moment.images.join('\n'),
  }
  showCreateDialog.value = true
}

/** 打开指定说说的评论列表。 */
async function openComments(moment: MomentItem) {
  selectedMoment.value = moment
  showCommentsDialog.value = true
  commentsLoading.value = true
  try {
    comments.value = await api.get<MomentComment[]>(`/api/v1/moments/${moment.id}/comments`, true)
  } catch (err: unknown) {
    comments.value = []
    ElMessage.error(err instanceof Error ? err.message : '加载评论失败')
  } finally {
    commentsLoading.value = false
  }
}

/** 删除指定说说评论。 */
async function removeComment(comment: MomentComment) {
  if (!selectedMoment.value) return
  try {
    await ElMessageBox.confirm('确定删除这条评论吗？此操作不可恢复。', '确认删除', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
    await api.delete(`/api/v1/moments/${selectedMoment.value.id}/comments/${comment.id}`, true)
    comments.value = comments.value.filter((item) => item.id !== comment.id)
    ElMessage.success('评论已删除')
  } catch {
    // 用户取消或删除失败
  }
}

/** Element Plus 未能从动态表格数据推导评论行类型，统一在边界处收窄。 */
function removeCommentRow(row: unknown) {
  const comment = row as MomentComment
  void removeComment(comment)
}

/** 将图库选择的图片追加到说说图片列表。 */
function handleImagesSelected(images: PickerImage[]) {
  const selectedUrls = images.map((image) => resolveUrl(image.url))
  const currentUrls = createForm.value.images
    .split('\n')
    .map((url) => url.trim())
    .filter(Boolean)
  createForm.value.images = [...new Set([...currentUrls, ...selectedUrls])].join('\n')
}

/** 将图库选择的图片追加到说说图片列表。 */

/** 创建或保存说说。 */
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
      mood_text: createForm.value.moodText.trim(),
      tags: createForm.value.tags
        ? createForm.value.tags
            .split(',')
            .map((t) => t.trim())
            .filter(Boolean)
        : [],
      images: createForm.value.images
        ? createForm.value.images
            .split('\n')
            .map((u) => u.trim())
            .filter(Boolean)
        : [],
    }
    if (editingId.value === null) {
      await api.post('/api/v1/moments', payload, true)
      ElMessage.success('发布成功')
    } else {
      await api.put(`/api/v1/moments/${editingId.value}`, payload, true)
      ElMessage.success('说说已更新')
    }
    showCreateDialog.value = false
    loadData()
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '发布失败'
    ElMessage.error(msg)
  } finally {
    creating.value = false
  }
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
      <!-- 移动端卡片列表 -->
      <div class="moment-mobile-list">
        <div v-for="row in data" :key="row.id" class="moment-mobile-card">
          <div class="moment-mobile-content">{{ row.content }}</div>
          <div class="moment-mobile-meta">
            <span v-if="row.mood || row.mood_text">
              {{ [row.mood, row.mood_text].filter(Boolean).join(' ') }}
            </span>
            <span>{{ row.images.length }} 张图</span>
            <span>{{ row.likes }} 赞</span>
            <span>{{ row.date.replace('T', ' ').slice(0, 16) }}</span>
          </div>
          <div class="moment-mobile-actions">
            <el-button type="primary" link size="small" @click="openComments(row)">评论</el-button>
             <el-button type="primary" link size="small" @click="openEdit(row)">编辑</el-button>
             <el-button type="danger" link size="small" @click="handleDelete(row, '这条说说')">
              删除
            </el-button>
          </div>
        </div>
        <el-empty v-if="data.length === 0" description="暂无说说" :image-size="72" />
      </div>

      <!-- 桌面端表格 -->
      <el-table
        :data="data as any"
        v-loading="loading"
        stripe
        class="moment-desktop-table"
        style="width: 100%"
      >
        <el-table-column prop="content" label="内容" min-width="300">
          <template #default="{ row }">
            <div class="content-cell">
              {{ row.content.slice(0, 80) }}{{ row.content.length > 80 ? '...' : '' }}
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="mood" label="心情" width="100">
          <template #default="{ row }">
            <span>{{ [row.mood, row.mood_text].filter(Boolean).join(' ') }}</span>
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
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }: { row: any }">
            <el-button type="primary" link size="small" @click="openComments(row)">
              评论
            </el-button>
            <el-button type="primary" link size="small" @click="openEdit(row)">编辑</el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row, '这条说说')"
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
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </el-card>

    <!-- 新建/编辑说说弹窗 -->
    <el-dialog v-model="showCreateDialog" :title="editingId === null ? '发说说' : '编辑说说'" width="500px">
      <el-form label-position="top">
        <el-form-item label="内容">
          <el-input
            v-model="createForm.content"
            type="textarea"
            :rows="4"
            placeholder="说点什么..."
          />
        </el-form-item>
        <el-form-item label="心情" class="mood-form-item">
          <div class="mood-editor">
            <div class="mood-picker-row">
              <EmojiPicker v-model="createForm.mood" />
              <span class="mood-picker-hint">选择一个表情</span>
            </div>
            <el-input
              v-model="createForm.moodText"
              class="mood-text-input"
              placeholder="给这份心情加一句话（可选）"
              maxlength="100"
              show-word-limit
            />
          </div>
        </el-form-item>
        <el-form-item label="标签（逗号分隔）">
          <el-input v-model="createForm.tags" placeholder="标签1, 标签2" />
        </el-form-item>
        <el-form-item label="图片 URL（每行一个）">
          <div class="image-picker-actions">
            <el-button type="primary" plain @click="showImagePicker = true"
              >从图库选择或上传</el-button
            >
            <span class="image-count">
              {{ createForm.images.split('\n').filter((url) => url.trim()).length }} 张已选择
            </span>
          </div>
          <el-input
            v-model="createForm.images"
            type="textarea"
            :rows="3"
            placeholder="可手动填写 URL，每行一个；也可从图库选择或上传"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="submitCreate">
          {{ editingId === null ? '发布' : '保存' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 评论管理弹窗 -->
    <el-dialog
      v-model="showCommentsDialog"
      :title="selectedMoment ? `「${selectedMoment.content.slice(0, 20)}」的评论` : '评论管理'"
      width="620px"
    >
      <el-table v-loading="commentsLoading" :data="comments" stripe>
        <el-table-column label="评论者" width="130">
          <template #default="{ row }">{{ row.nickname }}</template>
        </el-table-column>
        <el-table-column label="内容" min-width="240">
          <template #default="{ row }">{{ row.content }}</template>
        </el-table-column>
        <el-table-column label="时间" width="165">
          <template #default="{ row }">{{ row.date.replace('T', ' ').slice(0, 16) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="70" fixed="right">
          <template #default="{ row }">
            <el-button type="danger" link size="small" @click="removeCommentRow(row)"
              >删除</el-button
            >
          </template>
        </el-table-column>
        <template #empty>暂无评论</template>
      </el-table>
    </el-dialog>

    <ImagePickerDialog
      v-model="showImagePicker"
      title="选择说说图片"
      multiple
      @select-many="handleImagesSelected"
    />
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

.image-picker-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.mood-form-item :deep(.el-form-item__content) {
  display: block;
}

.mood-editor {
  width: 100%;
}

.mood-picker-row {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 36px;
}

.mood-picker-hint {
  color: var(--admin-text-secondary, #909399);
  font-size: 12px;
}

.mood-text-input {
  width: 100%;
  margin-top: 12px;
}

.mood-text-input :deep(.el-input__wrapper) {
  min-height: 38px;
  border-radius: 9px;
  background: var(--admin-input-bg, #fafafa);
  box-shadow: 0 0 0 1px var(--admin-border-color, #dcdfe6) inset;
  transition: box-shadow 0.2s ease, background 0.2s ease;
}

.mood-text-input :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px var(--el-color-primary-light-5) inset;
}

.mood-text-input :deep(.el-input__wrapper.is-focus) {
  background: var(--admin-panel-bg, #ffffff);
  box-shadow: 0 0 0 1px var(--el-color-primary) inset, 0 0 0 3px var(--el-color-primary-light-9);
}

.mood-text-input :deep(.el-input__count) {
  color: var(--admin-text-secondary, #a8abb2);
  font-size: 11px;
}

.image-count {
  color: var(--admin-text-secondary, #909399);
  font-size: 12px;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

/* 移动端卡片列表（默认隐藏，窄屏替换表格） */
.moment-mobile-list {
  display: none;
  flex-direction: column;
  gap: 12px;
}

.moment-mobile-card {
  padding: 14px;
  border: 1px solid var(--admin-border-color, #e4e7ed);
  border-radius: 12px;
  background: var(--admin-panel-bg, #ffffff);
}

.moment-mobile-content {
  color: var(--admin-text-color, #303133);
  font-size: 14px;
  line-height: 1.6;
}

.moment-mobile-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 14px;
  margin-top: 10px;
  color: var(--admin-text-secondary, #909399);
  font-size: 12px;
}

.moment-mobile-actions {
  display: flex;
  gap: 8px;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--admin-border-color, #e4e7ed);
}

@media (max-width: 767px) {
  .page-header {
    align-items: stretch;
    flex-direction: column;
  }

  .page-header .el-button {
    align-self: flex-start;
  }

  .moment-desktop-table {
    display: none;
  }

  .moment-mobile-list {
    display: flex;
  }

  .pagination-wrap {
    justify-content: center;
  }
}
</style>
