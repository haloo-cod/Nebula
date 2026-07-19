<template>
  <div class="about-comments">
    <h3 class="comments-title">评论 ({{ totalCount }})</h3>

    <!-- 输入区 -->
    <div class="comments-input-wrap">
      <div class="comments-input-row">
        <input
          ref="inputRef"
          v-model="inputText"
          class="comments-input"
          type="text"
          :placeholder="replyTo ? `回复 @${replyTo.author}...` : '写下你的想法...'"
          @keydown.enter="submitComment"
        />
        <button
          v-if="replyTo"
          class="comments-cancel-reply"
          type="button"
          @click="cancelReply"
          title="取消回复"
        >
          ✕
        </button>
        <button
          class="comments-submit"
          type="button"
          :disabled="!inputText.trim()"
          @click="submitComment"
        >
          发送
        </button>
      </div>
      <div v-if="replyTo" class="comments-replying-to">
        回复 <strong>@{{ replyTo.author }}</strong>
      </div>
    </div>

    <!-- 评论列表 -->
    <div v-if="comments.length === 0" class="comments-empty">暂无评论，来抢沙发吧~</div>
    <div v-else class="comments-list">
      <template v-for="comment in comments" :key="comment.id">
        <!-- 父评论 -->
        <div class="comment-item">
          <div class="comment-avatar" :style="{ background: comment.avatarColor }">
            {{ comment.author.charAt(0) }}
          </div>
          <div class="comment-body">
            <div class="comment-head">
              <span class="comment-author">{{ comment.author }}</span>
              <span v-if="comment.author === 'Starlit'" class="comment-owner-tag">作者</span>
              <span class="comment-date">{{ comment.date }}</span>
            </div>
            <p class="comment-content">{{ comment.content }}</p>
            <button class="comment-reply-btn" @click="startReply(comment)">回复</button>
          </div>
        </div>

        <!-- 子回复 -->
        <div v-if="comment.children && comment.children.length > 0" class="comment-replies">
          <div
            v-for="reply in comment.children"
            :key="reply.id"
            class="comment-item comment-item--child"
          >
            <div class="comment-avatar" :style="{ background: reply.avatarColor }">
              {{ reply.author.charAt(0) }}
            </div>
            <div class="comment-body">
              <div class="comment-head">
                <span class="comment-author">{{ reply.author }}</span>
                <span v-if="reply.author === 'Starlit'" class="comment-owner-tag">作者</span>
                <span class="comment-date">{{ reply.date }}</span>
              </div>
              <p class="comment-content">{{ reply.content }}</p>
              <button class="comment-reply-btn" @click="startReply(comment)">回复</button>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import {
  fetchComments,
  postComment,
  type CommentItem as ApiCommentItem,
} from '@/api/comments'

/** 评论数据结构（兼容 API 返回的 snake_case 和前端的 camelCase） */
interface CommentItem {
  id: number
  author: string
  date: string
  content: string
  avatarColor: string
  children?: CommentItem[]
}

// 接收页面标识 prop，默认为 about 页
const props = withDefaults(defineProps<{ pageKey?: string }>(), {
  pageKey: 'about',
})

const seedComments: CommentItem[] = [
  {
    id: 1,
    author: '访客A',
    date: '2026-07-15 14:22',
    content: '博客很漂亮，液态玻璃效果惊艳！一直在找这种风格的博客参考，学到很多。',
    avatarColor: '#6366f1',
  },
  {
    id: 2,
    author: 'Starlit',
    date: '2026-07-15 16:05',
    content: '谢谢喜欢！还在不断完善中，后续会加入更多有趣的功能~',
    avatarColor: '#ec4899',
  },
  {
    id: 3,
    author: '访客B',
    date: '2026-07-17 09:30',
    content: '请问自习室的番茄钟数据是存在本地的吗？还是会在后端上线后同步？',
    avatarColor: '#14b8a6',
    children: [
      {
        id: 5,
        author: 'Starlit',
        date: '2026-07-17 10:15',
        content: '目前是 localStorage 本地存储，后续后端上线后会支持云端同步，数据不会丢的。',
        avatarColor: '#ec4899',
      },
    ],
  },
  {
    id: 4,
    author: 'Starlit',
    date: '2026-07-17 22:08',
    content: '等后端上线后评论也会接入数据库，到时候就不怕刷新丢失啦~',
    avatarColor: '#ec4899',
  },
]

const comments = ref<CommentItem[]>([])
const inputText = ref('')
const inputRef = ref<HTMLInputElement | null>(null)
const replyTo = ref<{ id: number; author: string } | null>(null)
const loading = ref(false)

/** 将 API 返回的 snake_case 字段映射为前端 camelCase */
function mapApiComment(item: ApiCommentItem): CommentItem {
  return {
    id: item.id,
    author: item.author,
    date: item.date,
    content: item.content,
    avatarColor: item.avatar_color || '#6366f1',
    children: item.children?.map(mapApiComment) || [],
  }
}

const totalCount = computed(() => {
  let count = 0
  for (const c of comments.value) {
    count += 1 + (c.children?.length || 0)
  }
  return count
})

/** 从后端加载评论，失败时 fallback 到种子数据 */
async function loadComments() {
  loading.value = true
  try {
    const items = await fetchComments(props.pageKey)
    comments.value = items.map(mapApiComment)
  } catch {
    // 后端不可用时使用种子数据
    comments.value = JSON.parse(JSON.stringify(seedComments))
  } finally {
    loading.value = false
  }
}

function startReply(comment: CommentItem) {
  replyTo.value = { id: comment.id, author: comment.author }
  nextTick(() => {
    inputRef.value?.focus()
  })
}

function cancelReply() {
  replyTo.value = null
}

async function submitComment() {
  const text = inputText.value.trim()
  if (!text) return

  const parentId = replyTo.value?.id || null
  const author = '访客' + Math.floor(Math.random() * 900 + 100)

  try {
    // 调用后端 API 发表评论
    const newItem = await postComment(props.pageKey, author, text, parentId)
    const mapped = mapApiComment(newItem)

    if (parentId) {
      const parent = findCommentById(comments.value, parentId)
      if (parent) {
        if (!parent.children) parent.children = []
        parent.children.push(mapped)
      } else {
        comments.value.push(mapped)
      }
    } else {
      comments.value.push(mapped)
    }
  } catch {
    // API 失败时本地追加（降级体验）
    const fallbackComment: CommentItem = {
      id: Date.now(),
      author,
      date: formatDate(),
      content: text,
      avatarColor: '#6366f1',
    }
    if (parentId) {
      const parent = findCommentById(comments.value, parentId)
      if (parent) {
        if (!parent.children) parent.children = []
        parent.children.push(fallbackComment)
      } else {
        comments.value.push(fallbackComment)
      }
    } else {
      comments.value.push(fallbackComment)
    }
  }

  inputText.value = ''
  replyTo.value = null
  nextTick(() => {
    inputRef.value?.focus()
  })
}

function formatDate(): string {
  const d = new Date()
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function findCommentById(list: CommentItem[], id: number): CommentItem | null {
  for (const item of list) {
    if (item.id === id) return item
    if (item.children) {
      const found = findCommentById(item.children, id)
      if (found) return found
    }
  }
  return null
}

onMounted(() => {
  loadComments()
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
