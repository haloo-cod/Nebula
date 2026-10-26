<script setup lang="ts">
/**
 * 友链申请审核面板
 * 负责管理员端的申请列表、通过/拒绝、删除、JSON 同步提示与讨论抽屉。
 * 正式友链列表由父组件监听 changed 事件后刷新，本组件不直接修改父列表。
 */
import { computed, nextTick, onMounted, onBeforeUnmount, ref, useId } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ApiError } from '@/api/client'
import {
  deleteFriendApplication,
  fetchAdminFriendApplications,
  reviewFriendApplication,
  syncFriendsJson,
} from '@/api/friends'
import type { FriendApplicationPrivate, FriendApplicationStatus } from '@/api/friends'
import { deleteComment, fetchComments, postComment } from '@/api/comments'
import type { CommentItem } from '@/api/comments'

/** 管理员列表每页条数，与后端默认值保持一致。 */
const PAGE_SIZE = 20
/** 评论正文上限，与后端评论校验保持一致。 */
const REPLY_MAX_LENGTH = 2000
/** 每个根评论默认展示前三条回复。 */
const COLLAPSED_REPLY_LIMIT = 3
/** 数据库已提交但 JSON 副本同步失败时，后端返回的错误标识。 */
const JSON_SYNC_ERROR = 'FRIEND_JSON_SYNC_FAILED'

/** 单行正在执行的审核操作，用于防止重复点击。 */
type RowAction = 'approve' | 'reject' | 'delete'

/** 管理表格采用平铺行，避免组件树再次递归展开历史评论。 */
interface DiscussionRow extends CommentItem {
  isReply: boolean
  replyCount: number
}

const emit = defineEmits<{ changed: [] }>()

const loading = ref(false)
const applications = ref<FriendApplicationPrivate[]>([])
const total = ref(0)
const page = ref(1)
const statusFilter = ref<FriendApplicationStatus | ''>('pending')
const listError = ref('')
const listSeq = ref(0)
const busyRows = ref<Record<number, RowAction>>({})
const syncingJson = ref(false)
const syncFailed = ref(false)

const detailVisible = ref(false)
const detailApplication = ref<FriendApplicationPrivate | null>(null)

const rejectDialogVisible = ref(false)
const rejectTarget = ref<FriendApplicationPrivate | null>(null)
const rejectReason = ref('')
const rejectError = ref('')
const rejectSubmitting = ref(false)

const discussionVisible = ref(false)
const discussionApplication = ref<FriendApplicationPrivate | null>(null)
const discussionComments = ref<CommentItem[]>([])
const discussionLoading = ref(false)
const discussionError = ref('')
const discussionSeq = ref(0)
const discussionInput = ref('')
const discussionInputWrap = ref<HTMLElement | null>(null)
const discussionReplyTarget = ref<{ id: number; author: string } | null>(null)
const discussionSubmitting = ref(false)
const deletingCommentId = ref<number | null>(null)
/** 评论 ID → 根评论 ID，仅用于展开对应讨论串，不改写回复目标。 */
const discussionRootById = new Map<number, number>()
const expandedDiscussionThreads = ref(new Set<number>())
const discussionTableId = `${useId()}-discussion-comments`
const discussionBusy = computed(
  () =>
    discussionLoading.value ||
    discussionSubmitting.value ||
    deletingCommentId.value !== null ||
    Boolean(discussionError.value),
)
let discussionContext = 0

/** 状态筛选为空字符串时表示“全部”。 */
const emptyDescription = computed(() => {
  switch (statusFilter.value) {
    case 'pending':
      return '暂无待审核申请'
    case 'approved':
      return '暂无已通过申请'
    case 'rejected':
      return '暂无未通过申请'
    default:
      return '暂无申请'
  }
})

const discussionTitle = computed(() =>
  discussionApplication.value ? `讨论 · ${discussionApplication.value.name}` : '申请讨论',
)

const discussionCount = computed(() => countComments(discussionComments.value))
const discussionRows = computed<DiscussionRow[]>(() => {
  const rows: DiscussionRow[] = []
  for (const root of discussionComments.value) {
    const replies = root.children ?? []
    rows.push({ ...root, children: [], isReply: false, replyCount: replies.length })
    const visibleReplies = expandedDiscussionThreads.value.has(root.id)
      ? replies
      : replies.slice(0, COLLAPSED_REPLY_LIMIT)
    for (const reply of visibleReplies) {
      rows.push({ ...reply, children: [], isReply: true, replyCount: 0 })
    }
  }
  return rows
})

const STATUS_META: Record<
  FriendApplicationStatus,
  { label: string; tag: 'warning' | 'success' | 'danger' }
> = {
  pending: { label: '待审核', tag: 'warning' },
  approved: { label: '已通过', tag: 'success' },
  rejected: { label: '未通过', tag: 'danger' },
}

/** 缺失用户仍保留申请与审核数据，管理端明确显示为已注销。 */
function applicantLabel(row: Pick<FriendApplicationPrivate, 'user_id'>): string {
  return row.user_id === null ? '已注销用户' : `用户 #${row.user_id}`
}

/** 头像加载失败时使用站点名称首字作为占位。 */
function avatarFallback(name: string): string {
  return Array.from(name.trim())[0] ?? '友'
}

/** 后端时间为 ISO 字符串，表格与详情统一显示为本地时间。 */
function formatDateTime(value: string | null | undefined): string {
  if (!value) return '—'
  const normalized = /(?:[zZ]|[+-]\d{2}:\d{2})$/.test(value) ? value : `${value}Z`
  const date = new Date(normalized)
  if (Number.isNaN(date.getTime())) return value
  const pad = (part: number) => String(part).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

function errorText(err: unknown, fallback: string): string {
  if (err instanceof ApiError) return err.detail || fallback
  if (err instanceof Error) return err.message || fallback
  return fallback
}

function isJsonSyncFailure(err: unknown): boolean {
  return err instanceof ApiError && err.status === 503 && err.detail === JSON_SYNC_ERROR
}

function isRowBusy(id: number): boolean {
  return Boolean(busyRows.value[id])
}

function setRowBusy(id: number, action: RowAction) {
  busyRows.value[id] = action
}

function clearRowBusy(id: number) {
  delete busyRows.value[id]
}

/** 加载当前筛选/分页的申请；序号保证旧请求不会覆盖新结果。 */
async function loadApplications() {
  const seq = ++listSeq.value
  loading.value = true
  listError.value = ''
  try {
    const res = await fetchAdminFriendApplications(statusFilter.value, page.value, PAGE_SIZE)
    if (seq !== listSeq.value) return
    applications.value = res.items
    total.value = res.total

    // 删除最后一页数据后回退到仍存在的最大页码。
    const maxPage = Math.max(1, Math.ceil(res.total / PAGE_SIZE))
    if (page.value > maxPage) {
      page.value = maxPage
      if (res.total > 0) {
        await loadApplications()
        return
      }
    }

    syncOpenDialogs(res.items)
  } catch (err) {
    if (seq !== listSeq.value) return
    listError.value = errorText(err, '加载申请列表失败')
  } finally {
    if (seq === listSeq.value) loading.value = false
  }
}

/** 刷新列表后同步已打开详情/讨论抽屉中的记录，记录不存在时关闭。 */
function syncOpenDialogs(items: FriendApplicationPrivate[]) {
  if (detailVisible.value && detailApplication.value) {
    const detailId = detailApplication.value.id
    const updated = items.find((item) => item.id === detailId)
    if (updated) detailApplication.value = updated
    else closeDetails()
  }
  if (discussionVisible.value && discussionApplication.value) {
    const discussionId = discussionApplication.value.id
    const updated = items.find((item) => item.id === discussionId && item.status === 'approved')
    if (updated) discussionApplication.value = updated
    else closeDiscussion()
  }
}

function handleStatusChange() {
  closeDetails()
  closeDiscussion()
  page.value = 1
  void loadApplications()
}

function handlePageChange(value: number) {
  closeDetails()
  closeDiscussion()
  page.value = value
  void loadApplications()
}

/** 通过申请：确认后调用审核接口，成功后通知父组件刷新正式友链。 */
async function approveApplication(row: FriendApplicationPrivate) {
  if (isRowBusy(row.id)) return
  try {
    await ElMessageBox.confirm(
      `通过「${row.name}」后将加入正式友链，并在友链页公开这条申请。确定通过吗？`,
      '确认通过',
      { type: 'warning', confirmButtonText: '通过', cancelButtonText: '取消' },
    )
  } catch {
    return
  }
  if (isRowBusy(row.id)) return

  setRowBusy(row.id, 'approve')
  try {
    await reviewFriendApplication(row.id, { decision: 'approved' })
    syncFailed.value = false
    ElMessage.success('申请已通过，已加入正式友链')
    emit('changed')
    await loadApplications()
  } catch (err) {
    await handleMutationError(err, '审核失败')
  } finally {
    clearRowBusy(row.id)
  }
}

function openReject(row: FriendApplicationPrivate) {
  if (isRowBusy(row.id)) return
  rejectTarget.value = row
  rejectReason.value = ''
  rejectError.value = ''
  rejectDialogVisible.value = true
}

/** 拒绝必须填写原因，前后端均使用 trim 后的 1–500 字。 */
async function submitReject() {
  const row = rejectTarget.value
  if (!row || rejectSubmitting.value || isRowBusy(row.id)) return

  const reason = rejectReason.value.trim()
  if (!reason) {
    rejectError.value = '请填写拒绝原因'
    return
  }
  if (reason.length > 500) {
    rejectError.value = '拒绝原因不能超过 500 个字符'
    return
  }

  rejectSubmitting.value = true
  setRowBusy(row.id, 'reject')
  try {
    await reviewFriendApplication(row.id, { decision: 'rejected', reason })
    rejectDialogVisible.value = false
    ElMessage.success('申请已拒绝')
    await loadApplications()
  } catch (err) {
    if (isJsonSyncFailure(err)) {
      syncFailed.value = true
      ElMessage.warning('数据已保存，JSON 同步失败')
      rejectDialogVisible.value = false
      emit('changed')
      await loadApplications()
    } else if (err instanceof ApiError && (err.status === 409 || err.status === 404)) {
      rejectDialogVisible.value = false
      ElMessage.error(errorText(err, err.status === 409 ? '申请已处理，请刷新列表' : '申请不存在'))
      await loadApplications()
    } else {
      rejectError.value = errorText(err, '拒绝失败')
    }
  } finally {
    rejectSubmitting.value = false
    clearRowBusy(row.id)
  }
}

function handleRejectClosed() {
  if (rejectDialogVisible.value) return
  rejectTarget.value = null
  rejectReason.value = ''
  rejectError.value = ''
}

/** 删除申请：已通过申请会同时移除正式友链与全部讨论。 */
async function handleDelete(row: FriendApplicationPrivate) {
  if (isRowBusy(row.id)) return
  const approved = row.status === 'approved'
  const message = approved
    ? `确定删除「${row.name}」的申请？将同时删除其正式友链、公开申请和全部讨论，且无法恢复。`
    : `确定删除「${row.name}」的申请？该操作无法恢复。`

  try {
    await ElMessageBox.confirm(message, '确认删除', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  if (isRowBusy(row.id)) return

  setRowBusy(row.id, 'delete')
  try {
    await deleteFriendApplication(row.id)
    // 只有已通过记录会改写正式友链 JSON；普通申请删除不会修复之前的同步失败。
    if (approved) syncFailed.value = false
    closeViewsForApplication(row.id)
    ElMessage.success(approved ? '申请、正式友链及讨论已删除' : '申请已删除')
    emit('changed')
    await loadApplications()
  } catch (err) {
    if (isJsonSyncFailure(err) || (err instanceof ApiError && err.status === 409)) {
      closeViewsForApplication(row.id)
    }
    await handleMutationError(err, '删除失败')
  } finally {
    clearRowBusy(row.id)
  }
}

/** 审核/删除失败：503 表示数据库已保存但文件失败；409 需要刷新当前页。 */
async function handleMutationError(err: unknown, fallback: string) {
  if (isJsonSyncFailure(err)) {
    syncFailed.value = true
    ElMessage.warning('数据已保存，JSON 同步失败')
    emit('changed')
    await loadApplications()
    return
  }
  if (err instanceof ApiError && (err.status === 409 || err.status === 404)) {
    ElMessage.error(errorText(err, err.status === 409 ? '申请已处理，请刷新列表' : '申请不存在'))
    await loadApplications()
    return
  }
  ElMessage.error(errorText(err, fallback))
}

/** 只重试文件同步，不重复创建/批准/删除。 */
async function retrySyncJson() {
  if (syncingJson.value) return
  syncingJson.value = true
  try {
    await syncFriendsJson()
    syncFailed.value = false
    ElMessage.success('友链 JSON 已重新同步')
  } catch (err) {
    ElMessage.error(errorText(err, '重新同步 JSON 失败'))
  } finally {
    syncingJson.value = false
  }
}

function closeViewsForApplication(id: number) {
  if (detailApplication.value?.id === id) closeDetails()
  if (discussionApplication.value?.id === id) closeDiscussion()
}

function openDetails(row: FriendApplicationPrivate) {
  detailApplication.value = row
  detailVisible.value = true
}

function closeDetails() {
  if (!detailVisible.value) return
  detailVisible.value = false
}

function handleDetailsClosed() {
  if (!detailVisible.value) detailApplication.value = null
}

function openDiscussion(row: FriendApplicationPrivate) {
  if (row.status !== 'approved' || isRowBusy(row.id)) return
  closeDetails()
  discussionApplication.value = row
  discussionVisible.value = true
  clearDiscussionComments()
  void loadDiscussion()
}

function closeDiscussion() {
  if (!discussionVisible.value && !discussionApplication.value) return
  discussionVisible.value = false
  clearDiscussionComments()
}

function handleDiscussionClosed() {
  if (discussionVisible.value) return
  clearDiscussionComments()
  discussionApplication.value = null
}

/** 关闭/切换申请时立即失效评论请求与输入，避免旧数据串到新抽屉。 */
function clearDiscussionComments() {
  discussionContext += 1
  discussionSeq.value += 1
  discussionComments.value = []
  discussionLoading.value = false
  discussionError.value = ''
  discussionInput.value = ''
  discussionReplyTarget.value = null
  discussionSubmitting.value = false
  deletingCommentId.value = null
  discussionRootById.clear()
  expandedDiscussionThreads.value.clear()
}

/** 加载当前申请的讨论树；请求序号防止旧申请结果覆盖新抽屉。 */
async function loadDiscussion() {
  const app = discussionApplication.value
  if (!app || !discussionVisible.value) return

  const seq = ++discussionSeq.value
  discussionLoading.value = true
  discussionError.value = ''
  try {
    const items = await fetchComments(`friend-application:${app.id}`)
    if (
      seq !== discussionSeq.value ||
      discussionApplication.value?.id !== app.id ||
      !discussionVisible.value
    ) {
      return
    }
    discussionComments.value = items
    rebuildRootMap()
    validateDiscussionReplyTarget()
  } catch (err) {
    if (
      seq !== discussionSeq.value ||
      discussionApplication.value?.id !== app.id ||
      !discussionVisible.value
    ) {
      return
    }
    if (err instanceof ApiError && err.status === 404) {
      ElMessage.error('该申请已不可公开讨论')
      closeDiscussion()
      await loadApplications()
      return
    }
    discussionError.value = errorText(err, '加载讨论失败')
  } finally {
    if (seq === discussionSeq.value) discussionLoading.value = false
  }
}

function rebuildRootMap() {
  discussionRootById.clear()
  for (const root of discussionComments.value) {
    discussionRootById.set(root.id, root.id)
    for (const child of root.children ?? []) {
      discussionRootById.set(child.id, root.id)
    }
  }
}

function validateDiscussionReplyTarget() {
  const target = discussionReplyTarget.value
  if (target && !discussionRootById.has(target.id)) {
    discussionReplyTarget.value = null
  }
}

/** 回复始终指向实际点击的评论，根 ID 只控制展示层折叠。 */
function startDiscussionReply(comment: CommentItem) {
  if (discussionBusy.value) return
  discussionReplyTarget.value = { id: comment.id, author: comment.author }
  void nextTick(() => {
    discussionInputWrap.value?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    discussionInputWrap.value?.querySelector('textarea')?.focus()
  })
}

function cancelDiscussionReply() {
  discussionReplyTarget.value = null
}

function toggleDiscussionThread(rootId: number) {
  if (expandedDiscussionThreads.value.has(rootId)) expandedDiscussionThreads.value.delete(rootId)
  else expandedDiscussionThreads.value.add(rootId)
}

/** 发送回复；失败时保留输入和回复对象，成功后才清空并重新加载。 */
async function submitDiscussionComment() {
  const app = discussionApplication.value
  if (!app || discussionBusy.value) return

  const text = discussionInput.value.trim()
  if (!text) return
  if (text.length > REPLY_MAX_LENGTH) {
    ElMessage.warning(`回复不能超过 ${REPLY_MAX_LENGTH} 个字符`)
    return
  }

  discussionSubmitting.value = true
  const context = discussionContext
  const parentId = discussionReplyTarget.value?.id ?? null
  const rootId = parentId === null ? undefined : discussionRootById.get(parentId)
  try {
    await postComment(`friend-application:${app.id}`, text, parentId)
    if (
      context !== discussionContext ||
      discussionApplication.value?.id !== app.id ||
      !discussionVisible.value
    )
      return
    discussionInput.value = ''
    discussionReplyTarget.value = null
    if (rootId !== undefined) expandedDiscussionThreads.value.add(rootId)
    await loadDiscussion()
    if (context !== discussionContext) return
    ElMessage.success('回复已发送')
  } catch (err) {
    // 抽屉已关闭或已切换到另一条申请时，不再用旧申请的失败状态干扰当前界面。
    if (
      context !== discussionContext ||
      discussionApplication.value?.id !== app.id ||
      !discussionVisible.value
    )
      return
    if (err instanceof ApiError && err.status === 404) {
      ElMessage.error('该申请已不可公开讨论')
      closeDiscussion()
      await loadApplications()
      return
    }
    ElMessage.error(errorText(err, '发送失败，请稍后重试'))
  } finally {
    if (context === discussionContext) discussionSubmitting.value = false
  }
}

/** 管理员可删除任意评论，删除后重新加载讨论树。 */
async function handleDeleteComment(comment: CommentItem) {
  if (discussionBusy.value) return
  const initialApplication = discussionApplication.value
  if (!initialApplication) return
  const appId = initialApplication.id
  const context = discussionContext

  try {
    await ElMessageBox.confirm(`确定删除「${comment.author}」的这条评论吗？`, '确认删除', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  if (deletingCommentId.value !== null) return
  if (
    context !== discussionContext ||
    discussionApplication.value?.id !== appId ||
    !discussionVisible.value
  )
    return

  deletingCommentId.value = comment.id
  try {
    await deleteComment(comment.id)
    if (
      context !== discussionContext ||
      discussionApplication.value?.id !== appId ||
      !discussionVisible.value
    )
      return
    ElMessage.success('评论已删除')
    await loadDiscussion()
  } catch (err) {
    if (
      context !== discussionContext ||
      discussionApplication.value?.id !== appId ||
      !discussionVisible.value
    )
      return
    if (err instanceof ApiError && err.status === 404) {
      ElMessage.error('该评论或申请已不存在')
      await loadDiscussion()
      return
    }
    ElMessage.error(errorText(err, '删除评论失败'))
  } finally {
    if (context === discussionContext) deletingCommentId.value = null
  }
}

function countComments(items: CommentItem[]): number {
  let count = 0
  for (const item of items) {
    count += 1 + (item.children?.length ?? 0)
  }
  return count
}

onMounted(() => {
  void loadApplications()
})

onBeforeUnmount(() => {
  ++listSeq.value
  clearDiscussionComments()
})
</script>

<template>
  <div class="friend-applications-panel">
    <el-alert v-if="syncFailed" type="warning" :closable="false" show-icon>
      <template #title>数据已保存，JSON 同步失败</template>
      <div class="sync-alert-body">
        <span
          >数据库修改已保存，但正式友链 JSON
          副本可能尚未更新。可只重新同步文件，无需重复审核。</span
        >
        <el-button type="primary" size="small" :loading="syncingJson" @click="retrySyncJson">
          重新同步 JSON
        </el-button>
      </div>
    </el-alert>

    <el-card shadow="never" class="table-card">
      <template #header>
        <div class="panel-header">
          <div class="filter-group">
            <span class="filter-label">审核状态</span>
            <el-radio-group v-model="statusFilter" @change="handleStatusChange">
              <el-radio-button value="pending">待审核</el-radio-button>
              <el-radio-button value="approved">已通过</el-radio-button>
              <el-radio-button value="rejected">未通过</el-radio-button>
              <el-radio-button value="">全部</el-radio-button>
            </el-radio-group>
          </div>
          <div class="header-actions">
            <span class="total-text">共 {{ total }} 条</span>
            <el-button :loading="loading" :disabled="loading" @click="loadApplications">
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <el-alert v-if="listError" class="list-alert" type="error" :closable="false" show-icon>
        <template #title>申请列表加载失败</template>
        <div class="list-alert-body">
          <span>{{ listError }}</span>
          <el-button size="small" @click="loadApplications">重试</el-button>
        </div>
      </el-alert>

      <el-table
        v-if="applications.length > 0 || !listError"
        v-loading="loading"
        :data="applications"
        row-key="id"
        stripe
        class="application-table"
      >
        <!-- @vue-generic {FriendApplicationPrivate} -->
        <el-table-column prop="name" label="站点名称" min-width="130">
          <template #default="{ row }: { row: FriendApplicationPrivate }">
            <span class="site-name">{{ row.name }}</span>
          </template>
        </el-table-column>
        <!-- @vue-generic {FriendApplicationPrivate} -->
        <el-table-column label="站点地址" min-width="190">
          <template #default="{ row }: { row: FriendApplicationPrivate }">
            <a
              :href="row.url"
              target="_blank"
              rel="noopener noreferrer"
              class="link-text"
              :title="row.url"
              >{{ row.url }}</a
            >
          </template>
        </el-table-column>
        <!-- @vue-generic {FriendApplicationPrivate} -->
        <el-table-column label="头像" width="72" align="center">
          <template #default="{ row }: { row: FriendApplicationPrivate }">
            <el-avatar :src="row.avatar" :size="32" shape="circle">
              {{ avatarFallback(row.name) }}
            </el-avatar>
          </template>
        </el-table-column>
        <!-- @vue-generic {FriendApplicationPrivate} -->
        <el-table-column label="邮箱" min-width="190">
          <template #default="{ row }: { row: FriendApplicationPrivate }">
            <div class="email-cell">
              <span class="email-text">{{ row.email }}</span>
              <span class="applicant-meta" :class="{ 'is-deleted': row.user_id === null }">
                {{ applicantLabel(row) }}
              </span>
            </div>
          </template>
        </el-table-column>
        <!-- @vue-generic {FriendApplicationPrivate} -->
        <el-table-column label="RSS" min-width="170">
          <template #default="{ row }: { row: FriendApplicationPrivate }">
            <a
              v-if="row.rss_url"
              :href="row.rss_url"
              target="_blank"
              rel="noopener noreferrer"
              class="link-text rss-link"
              :title="row.rss_url"
              >{{ row.rss_url }}</a
            >
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>
        <!-- @vue-generic {FriendApplicationPrivate} -->
        <el-table-column label="申请时间" width="150">
          <template #default="{ row }: { row: FriendApplicationPrivate }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <!-- @vue-generic {FriendApplicationPrivate} -->
        <el-table-column label="状态" width="130">
          <template #default="{ row }: { row: FriendApplicationPrivate }">
            <el-tag :type="STATUS_META[row.status].tag" size="small">
              {{ STATUS_META[row.status].label }}
            </el-tag>
            <div
              v-if="row.status === 'rejected' && row.review_note"
              class="review-note"
              :title="row.review_note"
            >
              {{ row.review_note }}
            </div>
          </template>
        </el-table-column>
        <!-- @vue-generic {FriendApplicationPrivate} -->
        <el-table-column label="操作" width="270" fixed="right">
          <template #default="{ row }: { row: FriendApplicationPrivate }">
            <div class="row-actions">
              <el-button type="primary" link size="small" @click="openDetails(row)">
                详情
              </el-button>
              <template v-if="row.status === 'pending'">
                <el-button
                  type="success"
                  link
                  size="small"
                  :loading="busyRows[row.id] === 'approve'"
                  :disabled="isRowBusy(row.id)"
                  @click="approveApplication(row)"
                >
                  通过
                </el-button>
                <el-button
                  type="warning"
                  link
                  size="small"
                  :disabled="isRowBusy(row.id)"
                  @click="openReject(row)"
                >
                  拒绝
                </el-button>
              </template>
              <el-button
                v-if="row.status === 'approved'"
                type="primary"
                link
                size="small"
                :disabled="isRowBusy(row.id)"
                @click="openDiscussion(row)"
              >
                查看讨论
              </el-button>
              <el-button
                type="danger"
                link
                size="small"
                :loading="busyRows[row.id] === 'delete'"
                :disabled="isRowBusy(row.id)"
                @click="handleDelete(row)"
              >
                删除
              </el-button>
            </div>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty :description="emptyDescription" :image-size="80" />
        </template>
      </el-table>

      <div v-if="total > 0" class="pagination-wrap">
        <el-pagination
          v-model:current-page="page"
          :page-size="PAGE_SIZE"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <el-dialog
      v-model="detailVisible"
      title="申请详情"
      width="min(560px, 94vw)"
      @closed="handleDetailsClosed"
    >
      <el-descriptions v-if="detailApplication" :column="1" border>
        <el-descriptions-item label="站点名称">
          {{ detailApplication.name }}
        </el-descriptions-item>
        <el-descriptions-item label="站点地址">
          <a
            :href="detailApplication.url"
            target="_blank"
            rel="noopener noreferrer"
            class="link-text detail-link"
            >{{ detailApplication.url }}</a
          >
        </el-descriptions-item>
        <el-descriptions-item label="头像">
          <div class="detail-avatar-row">
            <el-avatar :src="detailApplication.avatar" :size="36" shape="circle">
              {{ avatarFallback(detailApplication.name) }}
            </el-avatar>
            <span class="detail-avatar-url">{{ detailApplication.avatar }}</span>
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="邮箱">
          {{ detailApplication.email }}
        </el-descriptions-item>
        <el-descriptions-item label="申请人">
          {{ applicantLabel(detailApplication) }}
        </el-descriptions-item>
        <el-descriptions-item label="RSS">
          <a
            v-if="detailApplication.rss_url"
            :href="detailApplication.rss_url"
            target="_blank"
            rel="noopener noreferrer"
            class="link-text detail-link"
            >{{ detailApplication.rss_url }}</a
          >
          <span v-else class="muted">—</span>
        </el-descriptions-item>
        <el-descriptions-item label="申请时间">
          {{ formatDateTime(detailApplication.created_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="审核时间">
          {{ formatDateTime(detailApplication.reviewed_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="STATUS_META[detailApplication.status].tag" size="small">
            {{ STATUS_META[detailApplication.status].label }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item v-if="detailApplication.status === 'rejected'" label="拒绝原因">
          <span class="detail-note">{{ detailApplication.review_note || '—' }}</span>
        </el-descriptions-item>
        <el-descriptions-item v-else-if="detailApplication.review_note" label="审核备注">
          <span class="detail-note">{{ detailApplication.review_note }}</span>
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="rejectDialogVisible"
      title="拒绝申请"
      width="min(500px, 94vw)"
      :close-on-click-modal="false"
      :close-on-press-escape="!rejectSubmitting"
      :show-close="!rejectSubmitting"
      @closed="handleRejectClosed"
    >
      <div v-if="rejectTarget" class="reject-target">
        <div>
          站点：<strong>{{ rejectTarget.name }}</strong>
        </div>
        <a
          :href="rejectTarget.url"
          target="_blank"
          rel="noopener noreferrer"
          class="link-text detail-link"
          >{{ rejectTarget.url }}</a
        >
      </div>
      <el-form class="reject-form" label-position="top">
        <el-form-item label="拒绝原因" required :error="rejectError">
          <el-input
            v-model="rejectReason"
            type="textarea"
            :rows="4"
            maxlength="500"
            show-word-limit
            :disabled="rejectSubmitting"
            placeholder="请填写拒绝原因，仅申请本人和管理员可见"
            @input="rejectError = ''"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button :disabled="rejectSubmitting" @click="rejectDialogVisible = false">
          取消
        </el-button>
        <el-button type="danger" :loading="rejectSubmitting" @click="submitReject">
          确认拒绝
        </el-button>
      </template>
    </el-dialog>

    <el-drawer
      v-model="discussionVisible"
      :title="discussionTitle"
      size="min(640px, 94%)"
      :close-on-click-modal="false"
      @closed="handleDiscussionClosed"
    >
      <div v-if="discussionApplication" class="discussion-drawer">
        <div class="discussion-meta">
          <div class="discussion-meta-main">
            <span class="discussion-site">{{ discussionApplication.name }}</span>
            <a
              :href="discussionApplication.url"
              target="_blank"
              rel="noopener noreferrer"
              class="link-text"
              >{{ discussionApplication.url }}</a
            >
          </div>
          <el-tag type="success" size="small">已通过</el-tag>
        </div>

        <div ref="discussionInputWrap" class="discussion-input-wrap">
          <div v-if="discussionReplyTarget" class="reply-target">
            <span
              >回复 <strong>@{{ discussionReplyTarget.author }}</strong></span
            >
            <el-button
              type="primary"
              link
              size="small"
              :disabled="discussionBusy"
              @click="cancelDiscussionReply"
            >
              取消回复
            </el-button>
          </div>
          <el-input
            v-model="discussionInput"
            type="textarea"
            :rows="3"
            :maxlength="REPLY_MAX_LENGTH"
            show-word-limit
            :placeholder="
              discussionReplyTarget ? `回复 @${discussionReplyTarget.author}` : '发表管理员回复...'
            "
            :disabled="discussionBusy"
          />
          <div class="discussion-actions">
            <el-button
              type="primary"
              :loading="discussionSubmitting"
              :disabled="discussionBusy || !discussionInput.trim()"
              @click="submitDiscussionComment"
            >
              发送
            </el-button>
          </div>
        </div>

        <div class="discussion-list-head">
          <span class="discussion-list-title">讨论 ({{ discussionCount }})</span>
          <el-button
            size="small"
            :loading="discussionLoading"
            :disabled="discussionLoading"
            @click="loadDiscussion"
          >
            刷新
          </el-button>
        </div>

        <el-alert v-if="discussionError" type="error" :closable="false" show-icon>
          <template #title>讨论加载失败</template>
          <div class="list-alert-body">
            <span>{{ discussionError }}</span>
            <el-button size="small" @click="loadDiscussion">重试</el-button>
          </div>
        </el-alert>

        <el-table
          :id="discussionTableId"
          v-loading="discussionLoading"
          :data="discussionRows"
          row-key="id"
          class="discussion-table"
        >
          <el-table-column prop="author" label="作者" width="110" show-overflow-tooltip />
          <el-table-column prop="date" label="时间" width="140" />
          <!-- @vue-generic {DiscussionRow} -->
          <el-table-column label="内容" min-width="180">
            <template #default="{ row }: { row: DiscussionRow }">
              <div :class="{ 'discussion-reply-row': row.isReply }">
                <span v-if="row.reply_to_author" class="muted">
                  回复 @{{ row.reply_to_author }}：
                </span>
                <span class="comment-content">{{ row.content }}</span>
                <el-button
                  v-if="!row.isReply && row.replyCount > COLLAPSED_REPLY_LIMIT"
                  type="primary"
                  link
                  size="small"
                  :aria-expanded="expandedDiscussionThreads.has(row.id)"
                  :aria-controls="discussionTableId"
                  :disabled="discussionBusy"
                  @click="toggleDiscussionThread(row.id)"
                >
                  {{
                    expandedDiscussionThreads.has(row.id)
                      ? '收起回复'
                      : `展开剩余 ${row.replyCount - COLLAPSED_REPLY_LIMIT} 条回复`
                  }}
                </el-button>
              </div>
            </template>
          </el-table-column>
          <!-- @vue-generic {CommentItem} -->
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }: { row: CommentItem }">
              <div class="row-actions">
                <el-button
                  type="primary"
                  link
                  size="small"
                  :disabled="discussionBusy"
                  @click="startDiscussionReply(row)"
                >
                  回复
                </el-button>
                <el-button
                  type="danger"
                  link
                  size="small"
                  :loading="deletingCommentId === row.id"
                  :disabled="discussionBusy"
                  @click="handleDeleteComment(row)"
                >
                  删除
                </el-button>
              </div>
            </template>
          </el-table-column>
          <template #empty>
            <el-empty description="暂无讨论" :image-size="70" />
          </template>
        </el-table>
      </div>
    </el-drawer>
  </div>
</template>

<style scoped src="@/assets/styles/admin-friend-applications.css"></style>
