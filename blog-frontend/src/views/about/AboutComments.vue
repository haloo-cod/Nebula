<template>
  <div class="about-comments">
    <h3 class="comments-title">评论 ({{ totalCount }})</h3>

    <!-- 输入区 -->
    <div v-if="auth.isLoggedIn" class="comments-input-wrap">
      <div class="comments-input-row">
        <input
          ref="inputRef"
          v-model="inputText"
          class="comments-input"
          type="text"
          maxlength="2000"
          :disabled="interactionDisabled"
          aria-label="评论内容"
          :placeholder="replyTo ? `回复 @${replyTo.author}...` : '写下你的想法...'"
          @keydown.enter="submitComment"
        />
        <button
          v-if="replyTo"
          class="comments-cancel-reply"
          type="button"
          :disabled="interactionDisabled"
          @click="cancelReply"
          title="取消回复"
        >
          ✕
        </button>
        <button
          class="comments-submit"
          type="button"
          :disabled="interactionDisabled || !inputText.trim()"
          @click="submitComment"
        >
          {{ submitting ? '发送中…' : '发送' }}
        </button>
      </div>
      <div v-if="replyTo" class="comments-replying-to">
        回复 <strong>@{{ replyTo.author }}</strong>
      </div>
    </div>
    <div v-else class="comments-login-prompt">
      <RouterLink :to="{ path: '/login', query: { redirect: $route.fullPath } }"
        >登录后参与评论</RouterLink
      >
    </div>

    <!-- 评论列表 -->
    <div v-if="loading && comments.length === 0" class="comments-empty" role="status">
      正在加载评论…
    </div>
    <div v-else-if="error" class="comments-empty comments-error" role="alert">
      <span>{{ error }}</span>
      <button class="comments-submit comments-retry" type="button" @click="loadComments">
        重试
      </button>
    </div>
    <div v-else-if="comments.length === 0" class="comments-empty">暂无评论，来抢沙发吧~</div>
    <div v-else class="comments-list">
      <template v-for="comment in comments" :key="comment.id">
        <!-- 父评论 -->
        <div class="comment-item">
          <img
            v-if="comment.avatarUrl"
            class="comment-avatar"
            :src="resolveUrl(comment.avatarUrl)"
            alt=""
          />
          <div
            v-else
            class="comment-avatar"
            :style="{ background: comment.avatarColor || '#6366f1' }"
          >
            {{ comment.author.charAt(0) }}
          </div>
          <div class="comment-body">
            <div class="comment-head">
              <span class="comment-author">{{ comment.author }}</span>
              <span v-if="comment.author === 'Starlit'" class="comment-owner-tag">作者</span>
              <span class="comment-date">{{ comment.date }}</span>
            </div>
            <p class="comment-content">{{ comment.content }}</p>
            <button
              v-if="auth.isLoggedIn"
              class="comment-reply-btn"
              :disabled="interactionDisabled"
              @click="startReply(comment)"
            >
              回复
            </button>
            <button
              v-if="comment.canDelete"
              class="comment-delete-btn"
              :disabled="interactionDisabled"
              @click="removeComment(comment)"
            >
              {{ deletingId === comment.id ? '删除中…' : '删除' }}
            </button>
          </div>
        </div>

        <!-- 子回复 -->
        <div
          v-if="comment.children.length > 0"
          :id="replyListId(comment.id)"
          class="comment-replies"
        >
          <div
            v-for="reply in visibleReplies(comment)"
            :key="reply.id"
            class="comment-item comment-item--child"
          >
            <img
              v-if="reply.avatarUrl"
              class="comment-avatar"
              :src="resolveUrl(reply.avatarUrl)"
              alt=""
            />
            <div
              v-else
              class="comment-avatar"
              :style="{ background: reply.avatarColor || '#6366f1' }"
            >
              {{ reply.author.charAt(0) }}
            </div>
            <div class="comment-body">
              <div class="comment-head">
                <span class="comment-author">{{ reply.author }}</span>
                <span v-if="reply.author === 'Starlit'" class="comment-owner-tag">作者</span>
                <span v-if="reply.replyToAuthor" class="comment-date">
                  回复 @{{ reply.replyToAuthor }}
                </span>
                <span class="comment-date">{{ reply.date }}</span>
              </div>
              <p class="comment-content">{{ reply.content }}</p>
              <button
                v-if="auth.isLoggedIn"
                class="comment-reply-btn"
                :disabled="interactionDisabled"
                @click="startReply(reply, comment.id)"
              >
                回复
              </button>
              <button
                v-if="reply.canDelete"
                class="comment-delete-btn"
                :disabled="interactionDisabled"
                @click="removeComment(reply)"
              >
                {{ deletingId === reply.id ? '删除中…' : '删除' }}
              </button>
            </div>
          </div>
          <button
            v-if="comment.children.length > COLLAPSED_REPLY_LIMIT"
            class="comment-reply-btn comment-thread-toggle"
            type="button"
            :aria-expanded="expandedThreads.has(comment.id)"
            :aria-controls="replyListId(comment.id)"
            :disabled="interactionDisabled"
            @click="toggleThread(comment.id)"
          >
            {{
              expandedThreads.has(comment.id)
                ? '收起回复'
                : `展开剩余 ${comment.children.length - COLLAPSED_REPLY_LIMIT} 条回复`
            }}
          </button>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, watch, onBeforeUnmount, useId } from 'vue'
import { RouterLink } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  fetchComments,
  postComment,
  deleteComment,
  type CommentItem as ApiCommentItem,
} from '@/api/comments'
import { resolveUrl } from '@/api/client'
import { useAuthStore } from '@/stores/auth'

/** 评论数据结构（兼容 API 返回的 snake_case 和前端的 camelCase） */
interface CommentItem {
  id: number
  author: string
  date: string
  content: string
  avatarColor: string
  avatarUrl?: string
  canDelete?: boolean
  parentId: number | null
  replyToAuthor: string
  children: CommentItem[]
}

// 接收页面标识 prop，默认为 about 页
const props = withDefaults(defineProps<{ pageKey?: string }>(), {
  pageKey: 'about',
})
const auth = useAuthStore()
/** 每个讨论串初始展示三条回复，其余由读者展开。 */
const COLLAPSED_REPLY_LIMIT = 3
const componentId = useId()
const expandedThreads = ref(new Set<number>())

const comments = ref<CommentItem[]>([])
const inputText = ref('')
const inputRef = ref<HTMLInputElement | null>(null)
const replyTo = ref<{ id: number; author: string; rootId: number } | null>(null)
const loading = ref(false)
const error = ref('')
const submitting = ref(false)
const deletingId = ref<number | null>(null)
let loadSeq = 0
let contextVersion = 0
const interactionDisabled = computed(
  () => loading.value || Boolean(error.value) || submitting.value || deletingId.value !== null,
)

/** 将 API 返回的 snake_case 字段映射为前端 camelCase */
function mapApiComment(item: ApiCommentItem): CommentItem {
  return {
    id: item.id,
    author: item.author,
    date: item.date,
    content: item.content,
    avatarColor: item.avatar_color || '#6366f1',
    avatarUrl: item.avatar_url,
    canDelete: item.can_delete,
    parentId: item.parent_id ?? null,
    replyToAuthor: item.reply_to_author ?? '',
    children: [],
  }
}

const totalCount = computed(() => {
  let count = 0
  for (const c of comments.value) {
    count += 1 + (c.children?.length || 0)
  }
  return count
})

/** 只展示真实评论；失败时保留明确错误态，不回退演示数据。 */
async function loadComments() {
  const seq = ++loadSeq
  loading.value = true
  error.value = ''
  try {
    const items = await fetchComments(props.pageKey)
    if (seq !== loadSeq) return
    comments.value = items.map((item) => ({
      ...mapApiComment(item),
      children: (item.children ?? []).map(mapApiComment),
    }))
  } catch (err: unknown) {
    if (seq !== loadSeq) return
    comments.value = []
    error.value = err instanceof Error ? err.message : '评论加载失败，请稍后重试'
  } finally {
    if (seq === loadSeq) loading.value = false
  }
}

function startReply(comment: CommentItem, rootId = comment.id) {
  if (interactionDisabled.value) return
  replyTo.value = { id: comment.id, author: comment.author, rootId }
  nextTick(() => {
    inputRef.value?.focus()
  })
}

function cancelReply() {
  replyTo.value = null
}

async function submitComment() {
  if (!auth.isLoggedIn || interactionDisabled.value) return
  const text = inputText.value.trim()
  if (!text) return
  if (text.length > 2000) return
  const version = contextVersion
  const pageKey = props.pageKey

  const parentId = replyTo.value?.id || null
  const rootId = replyTo.value?.rootId
  submitting.value = true
  try {
    // 调用后端 API 发表评论
    const newItem = await postComment(pageKey, text, parentId)
    if (version !== contextVersion) return
    const mapped = mapApiComment(newItem)

    if (parentId !== null) {
      if (rootId !== undefined) expandedThreads.value.add(rootId)
      const root = comments.value.find((item) => item.id === rootId)
      if (root) {
        root.children.push(mapped)
      } else {
        await loadComments()
        if (version !== contextVersion) return
      }
    } else {
      comments.value.push(mapped)
    }
  } catch (err: unknown) {
    if (version !== contextVersion) return
    // 失败时保留输入与回复对象，方便用户重试。
    ElMessage.error(err instanceof Error ? err.message : '评论发送失败')
    return
  } finally {
    if (version === contextVersion) submitting.value = false
  }

  inputText.value = ''
  replyTo.value = null
  nextTick(() => {
    inputRef.value?.focus()
  })
}

/** 删除本人评论并重新加载评论树。 */
async function removeComment(comment: CommentItem) {
  if (interactionDisabled.value) return
  deletingId.value = comment.id
  const version = contextVersion
  try {
    await deleteComment(comment.id)
    if (version !== contextVersion) return
    await loadComments()
    ElMessage.success('评论已删除')
  } catch (err: unknown) {
    if (version !== contextVersion) return
    ElMessage.error(err instanceof Error ? err.message : '删除失败')
  } finally {
    if (version === contextVersion) deletingId.value = null
  }
}

function replyListId(rootId: number): string {
  return `${componentId}-replies-${rootId}`
}

function visibleReplies(comment: CommentItem): CommentItem[] {
  return expandedThreads.value.has(comment.id)
    ? comment.children
    : comment.children.slice(0, COLLAPSED_REPLY_LIMIT)
}

function toggleThread(rootId: number) {
  if (expandedThreads.value.has(rootId)) expandedThreads.value.delete(rootId)
  else expandedThreads.value.add(rootId)
}

// 页面标识或登录状态变化后重新加载，并清理上一页面的草稿与回复对象。
watch(
  () => [props.pageKey, auth.isLoggedIn, auth.user?.id] as const,
  () => {
    ++contextVersion
    comments.value = []
    submitting.value = false
    deletingId.value = null
    inputText.value = ''
    replyTo.value = null
    expandedThreads.value.clear()
    void loadComments()
  },
  { immediate: true },
)

onBeforeUnmount(() => {
  ++contextVersion
  ++loadSeq
})
</script>

<style scoped>
.about-comments {
  padding: 1.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.comments-title {
  margin: 0 0 1rem;
  color: var(--text-primary);
  font-size: 1.1rem;
  font-weight: 700;
}

/* ===== 输入区 ===== */
.comments-input-wrap {
  margin-bottom: 0.25rem;
}

.comments-login-prompt {
  margin-bottom: 1rem;
  padding: 0.8rem 1rem;
  border: 1px dashed rgba(140, 185, 255, 0.28);
  border-radius: 0.75rem;
  text-align: center;
}

.comments-login-prompt a {
  color: rgba(180, 210, 255, 0.9);
  font-size: 0.82rem;
}

.comments-input-row {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.comments-input {
  flex: 1;
  padding: 0.6rem 1rem;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 0.75rem;
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-primary);
  font-size: 0.85rem;
  outline: none;
  transition: border-color 0.2s ease;
}

.comments-input:focus {
  border-color: rgba(140, 185, 255, 0.4);
}

.comments-input::placeholder {
  color: var(--text-muted);
}

.comments-replying-to {
  margin-top: 0.4rem;
  margin-left: 0.25rem;
  font-size: 0.75rem;
  color: var(--text-muted);
}

.comments-replying-to strong {
  color: var(--text-secondary);
}

.comments-cancel-reply {
  flex-shrink: 0;
  width: 2rem;
  height: 2rem;
  border: none;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.08);
  color: var(--text-muted);
  font-size: 0.75rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s ease;
}

.comments-cancel-reply:hover {
  background: rgba(255, 80, 80, 0.15);
  color: rgba(255, 100, 100, 0.9);
}

.comments-submit {
  flex-shrink: 0;
  padding: 0.6rem 1.2rem;
  border: 1px solid rgba(140, 185, 255, 0.3);
  border-radius: 0.75rem;
  background: rgba(100, 150, 255, 0.12);
  color: rgba(180, 210, 255, 0.9);
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.comments-submit:hover:not(:disabled) {
  background: rgba(100, 150, 255, 0.22);
  border-color: rgba(140, 185, 255, 0.5);
}

.comments-submit:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* ===== 空状态 ===== */
.comments-empty {
  text-align: center;
  padding: 2rem 0;
  color: var(--text-muted);
  font-size: 0.85rem;
}

.comments-error {
  overflow-wrap: anywhere;
}

.comments-error .comments-submit {
  margin-left: 0.75rem;
}

/* ===== 评论列表 ===== */
.comments-list {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  margin-top: 1.5rem;
}

.comment-item {
  display: flex;
  gap: 0.75rem;
  padding: 0.85rem 1rem;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 0.85rem;
}

/* 子回复缩进 */
.comment-replies {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  margin-top: -0.25rem;
  margin-left: 2.75rem;
  padding-left: 1rem;
  border-left: 2px solid rgba(255, 255, 255, 0.08);
}

.comment-item--child {
  background: rgba(255, 255, 255, 0.025);
  padding: 0.7rem 0.85rem;
  border-radius: 0.7rem;
}

/* ===== 评论内容 ===== */
.comment-avatar {
  flex-shrink: 0;
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 0.8rem;
  font-weight: 700;
}

.comment-item--child .comment-avatar {
  width: 1.6rem;
  height: 1.6rem;
  font-size: 0.7rem;
}

.comment-body {
  flex: 1;
  min-width: 0;
}

.comment-head {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
}

.comment-author {
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--text-primary);
}

.comment-owner-tag {
  font-size: 0.65rem;
  padding: 0.08rem 0.4rem;
  border-radius: 999px;
  background: rgba(100, 150, 255, 0.2);
  color: rgba(150, 200, 255, 0.9);
  font-weight: 600;
  line-height: 1.4;
}

.comment-date {
  font-size: 0.68rem;
  color: var(--text-muted);
  margin-left: auto;
}

.comment-content {
  margin: 0;
  font-size: 0.85rem;
  line-height: 1.6;
  color: var(--text-secondary);
}

.comment-reply-btn {
  display: inline-block;
  margin-top: 0.4rem;
  padding: 0;
  border: none;
  background: none;
  color: var(--text-muted);
  font-size: 0.72rem;
  cursor: pointer;
  transition: color 0.2s ease;
}

.comment-thread-toggle {
  align-self: flex-start;
  margin-top: 0.2rem;
}

.comment-delete-btn {
  margin: 0.4rem 0 0 0.7rem;
  padding: 0;
  border: none;
  background: none;
  color: rgba(255, 120, 120, 0.75);
  font-size: 0.72rem;
  cursor: pointer;
}

.comment-reply-btn:hover {
  color: rgba(140, 185, 255, 0.85);
}

/* ===== 响应式 ===== */
@media (min-width: 768px) {
  .about-comments {
    padding: 2rem 2.5rem;
  }

  .comment-replies {
    margin-left: 3rem;
    padding-left: 1.25rem;
  }
}
</style>

<!-- Light 主题适配 -->
<style>
[data-theme='light'] .about-comments {
  border-top-color: rgba(0, 0, 0, 0.06);
}

[data-theme='light'] .about-comments .comments-input {
  background: rgba(0, 0, 0, 0.03);
  border-color: rgba(0, 0, 0, 0.1);
}

[data-theme='light'] .about-comments .comments-input:focus {
  border-color: rgba(50, 100, 220, 0.35);
}

[data-theme='light'] .about-comments .comments-cancel-reply {
  background: rgba(0, 0, 0, 0.06);
}

[data-theme='light'] .about-comments .comments-cancel-reply:hover {
  background: rgba(255, 80, 80, 0.12);
}

[data-theme='light'] .about-comments .comments-submit {
  background: rgba(50, 100, 220, 0.1);
  border-color: rgba(50, 100, 220, 0.3);
  color: rgba(30, 70, 180, 1);
}

[data-theme='light'] .about-comments .comments-submit:hover:not(:disabled) {
  background: rgba(50, 100, 220, 0.18);
}

[data-theme='light'] .about-comments .comment-item {
  background: rgba(0, 0, 0, 0.02);
  border-color: rgba(0, 0, 0, 0.06);
}

[data-theme='light'] .about-comments .comment-replies {
  border-left-color: rgba(0, 0, 0, 0.08);
}

[data-theme='light'] .about-comments .comment-item--child {
  background: rgba(0, 0, 0, 0.013);
}

[data-theme='light'] .about-comments .comment-owner-tag {
  background: rgba(50, 100, 220, 0.12);
  color: rgba(30, 70, 180, 0.85);
}

[data-theme='light'] .about-comments .comment-reply-btn:hover {
  color: rgba(50, 100, 220, 0.8);
}
</style>
