<template>
  <div class="detail-inner">
    <!-- 头部:时间 + 心情 -->
    <div class="detail-inner__head">
      <span class="detail-inner__time">{{ fullDate(moment.date) }}</span>
      <span v-if="moment.mood" class="detail-inner__mood">{{ moodDisplay(moment.mood) }}</span>
    </div>

    <!-- 完整正文(不截断) -->
    <p class="detail-inner__text">{{ moment.content }}</p>

    <!-- 图片九宫格 -->
    <ImageGrid v-if="moment.images.length > 0" :images="moment.images" />

    <!-- 标签 -->
    <div v-if="moment.tags.length > 0" class="detail-inner__tags">
      <span v-for="tag in moment.tags" :key="tag" class="detail-inner__tag">#{{ tag }}</span>
    </div>

    <!-- 交互栏:点赞 -->
    <div class="detail-inner__actions">
      <button
        class="detail-inner__like-btn"
        :class="{ 'detail-inner__like-btn--active': isLiked }"
        @click="toggleLike"
      >
        <span class="detail-inner__heart" :class="{ 'detail-inner__heart--pop': justLiked }"
          >♥</span
        >
        <span>{{ displayLikes }}</span>
      </button>
    </div>

    <!-- 评论区 -->
    <div class="detail-inner__comments">
      <h4 class="detail-inner__comments-title">评论 ({{ comments.length }})</h4>
      <div v-if="commentsLoading" class="detail-inner__comments-empty">正在加载评论...</div>
      <div v-else-if="comments.length === 0" class="detail-inner__comments-empty">
        {{ commentsError || '暂无评论，来留下第一条吧' }}
      </div>
      <div v-else class="detail-inner__comments-list">
        <div v-for="c in comments" :key="c.id" class="detail-inner__comment-item">
          <span class="detail-inner__comment-nick">{{ c.nickname }}</span>
          <span class="detail-inner__comment-date">{{ c.date }}</span>
          <p class="detail-inner__comment-text">{{ c.content }}</p>
        </div>
      </div>
      <div v-if="!auth.isLoggedIn" class="detail-inner__comment-login">
        <span>登录后参与评论</span>
        <RouterLink :to="loginLocation">登录</RouterLink>
        <RouterLink :to="registerLocation">注册</RouterLink>
      </div>
      <form v-else class="detail-inner__comment-form" @submit.prevent="submitComment">
        <div class="detail-inner__comment-author">
          以 {{ auth.user?.display_name || auth.user?.username || '当前账户' }} 的身份评论
        </div>
        <textarea
          v-model="commentText"
          class="detail-inner__comment-input detail-inner__comment-textarea"
          maxlength="500"
          rows="3"
          placeholder="写下你的想法..."
        ></textarea>
        <div class="detail-inner__comment-form-footer">
          <span class="detail-inner__comment-hint">已登录账户可发表评论</span>
          <button
            class="detail-inner__comment-submit"
            type="submit"
            :disabled="submitting || !commentText.trim()"
          >
            {{ submitting ? '发送中...' : '发表评论' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import type { Moment, MomentComment } from '@/types'
import ImageGrid from './ImageGrid.vue'
import { likeMoment, fetchMomentComments, postMomentComment } from '@/api/moments'
import { useAuthStore } from '@/stores/auth'

const props = defineProps<{
  moment: Moment
}>()

const route = useRoute()
const auth = useAuthStore()
const loginLocation = computed(() => ({ path: '/login', query: { redirect: route.fullPath } }))
const registerLocation = computed(() => ({
  path: '/register',
  query: { redirect: route.fullPath },
}))

// ============ 评论列表 ============

const comments = ref<MomentComment[]>([])
const commentText = ref('')
const commentsLoading = ref(false)
const commentsError = ref('')
const submitting = ref(false)

onMounted(async () => {
  isLiked.value = getLikedIds().has(props.moment.id)
  // 从 API 加载评论
  commentsLoading.value = true
  commentsError.value = ''
  try {
    comments.value = await fetchMomentComments(props.moment.id)
  } catch {
    commentsError.value = '评论暂时无法加载'
  } finally {
    commentsLoading.value = false
  }
})
// ============ 点赞逻辑(与 MomentCard 共享 localStorage key) ============

const LIKED_KEY = 'moments_liked_ids'

function getLikedIds(): Set<number> {
  try {
    const raw = localStorage.getItem(LIKED_KEY)
    return raw ? new Set(JSON.parse(raw) as number[]) : new Set()
  } catch {
    return new Set()
  }
}

function saveLikedIds(ids: Set<number>) {
  localStorage.setItem(LIKED_KEY, JSON.stringify([...ids]))
}

const isLiked = ref(false)
const localLikeDelta = ref(0)
const justLiked = ref(false)

const displayLikes = computed(() => props.moment.likes + localLikeDelta.value)

function toggleLike() {
  const ids = getLikedIds()
  if (isLiked.value) {
    ids.delete(props.moment.id)
    localLikeDelta.value--
    isLiked.value = false
  } else {
    ids.add(props.moment.id)
    localLikeDelta.value++
    isLiked.value = true
    justLiked.value = true
    setTimeout(() => {
      justLiked.value = false
    }, 400)
    // 调用后端 API 点赞（静默）
    likeMoment(props.moment.id).catch(() => {})
  }
  saveLikedIds(ids)
}

/** 提交说说评论，成功后插入当前列表顶部。 */
async function submitComment() {
  const text = commentText.value.trim()
  if (!auth.isLoggedIn || !text || submitting.value) return

  submitting.value = true
  try {
    const comment = await postMomentComment(props.moment.id, text)
    comments.value = [comment, ...comments.value]
    commentText.value = ''
  } catch (err: unknown) {
    commentsError.value = err instanceof Error ? err.message : '评论发送失败，请稍后重试'
  } finally {
    submitting.value = false
  }
}

// ============ 工具函数 ============

/** 完整日期格式(详情面板用) */
function fullDate(dateStr: string): string {
  const d = new Date(dateStr)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

/** 心情 → emoji 映射 */
function moodEmoji(mood: string): string {
  const map: Record<string, string> = {
    开心: '😊',
    平静: '😌',
    灵感: '💡',
    感动: '🥹',
    疲惫: '😴',
    思考: '🤔',
    满足: '😋',
    期待: '✨',
  }
  return map[mood] || mood || '📝'
}

/** 兼容旧的文字心情，并避免新 Emoji 被重复渲染。 */
function moodDisplay(mood: string): string {
  const emoji = moodEmoji(mood)
  return emoji === mood ? mood : `${emoji} ${mood}`
}
</script>

<style scoped>
.detail-inner {
  width: 100%;
  min-width: 0;
  overflow: hidden;
}

.detail-inner__head {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-bottom: 0.8rem;
  flex-wrap: wrap;
}

.detail-inner__time {
  font-size: 0.8rem;
  color: var(--text-muted);
  font-variant-numeric: tabular-nums;
}

.detail-inner__mood {
  font-size: 0.75rem;
  color: rgba(180, 220, 255, 0.7);
  background: rgba(140, 200, 255, 0.08);
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
  border: 1px solid rgba(140, 200, 255, 0.15);
}

/* 完整正文 */
.detail-inner__text {
  margin: 0 0 1rem;
  color: var(--text-primary);
  font-size: 0.95rem;
  line-height: 1.85;
  white-space: pre-wrap;
  word-break: break-word;
}

/* 标签 */
.detail-inner__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-top: 0.9rem;
}

.detail-inner__tag {
  font-size: 0.74rem;
  color: rgba(140, 205, 255, 0.65);
  background: rgba(140, 200, 255, 0.07);
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
}

/* 交互栏 */
.detail-inner__actions {
  display: flex;
  align-items: center;
  margin-top: 1rem;
  padding-top: 0.8rem;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.detail-inner__like-btn {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.3rem 0.7rem;
  border: none;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-secondary);
  font-size: 0.82rem;
  cursor: pointer;
  transition:
    color 0.2s ease,
    background 0.2s ease;
}

.detail-inner__like-btn:hover {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.1);
}

.detail-inner__like-btn--active {
  color: #f87171;
}

.detail-inner__like-btn--active:hover {
  color: #f87171;
}

.detail-inner__heart--pop {
  animation: heartPop 0.4s cubic-bezier(0.17, 0.67, 0.29, 1.3);
}

@keyframes heartPop {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.4);
  }
  100% {
    transform: scale(1);
  }
}

/* 评论区 */
.detail-inner__comments {
  margin-top: 1.2rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.detail-inner__comments-title {
  margin: 0 0 0.6rem;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-secondary);
}

.detail-inner__comments-empty {
  text-align: center;
  color: var(--text-faint);
  font-size: 0.8rem;
  padding: 1rem 0;
}

.detail-inner__comment-form {
  margin-top: 0.6rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.detail-inner__comment-login {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-top: 0.6rem;
  color: var(--text-faint);
  font-size: 0.76rem;
}

.detail-inner__comment-login a {
  color: rgba(140, 205, 255, 0.82);
  text-decoration: none;
}

.detail-inner__comment-author {
  color: var(--text-faint);
  font-size: 0.72rem;
}

.detail-inner__comment-input {
  width: 100%;
  padding: 0.6rem 0.9rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 0.6rem;
  background: rgba(255, 255, 255, 0.03);
  color: var(--text-secondary);
  font-size: 0.82rem;
  outline: none;
}

.detail-inner__comment-input:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.detail-inner__comment-input:focus {
  border-color: rgba(140, 200, 255, 0.38);
}

.detail-inner__comment-textarea {
  resize: vertical;
  min-height: 4.2rem;
  font-family: inherit;
}

.detail-inner__comment-form-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.detail-inner__comment-hint {
  color: var(--text-faint);
  font-size: 0.68rem;
}

.detail-inner__comment-submit {
  padding: 0.42rem 0.78rem;
  border: 1px solid rgba(140, 200, 255, 0.2);
  border-radius: 999px;
  background: rgba(140, 200, 255, 0.1);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 0.75rem;
  transition:
    background 0.2s ease,
    border-color 0.2s ease,
    opacity 0.2s ease;
}

.detail-inner__comment-submit:hover:not(:disabled) {
  background: rgba(140, 200, 255, 0.18);
  border-color: rgba(140, 200, 255, 0.38);
}

.detail-inner__comment-submit:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.detail-inner__comments-list {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.detail-inner__comment-item {
  padding: 0.6rem 0.8rem;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 0.6rem;
}

.detail-inner__comment-nick {
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-right: 0.5rem;
}

.detail-inner__comment-date {
  font-size: 0.68rem;
  color: var(--text-muted);
}

.detail-inner__comment-text {
  margin: 0.3rem 0 0;
  font-size: 0.82rem;
  line-height: 1.5;
  color: var(--text-secondary);
}
</style>

<style>
/* ============================================
   light 模式详情内容适配
   通过 .detail-inner 前缀限定,不泄漏到其他组件
   ============================================ */

/* 心情标签:改为深蓝色系 */
[data-theme='light'] .detail-inner .detail-inner__mood {
  color: rgba(30, 80, 140, 0.8);
  background: rgba(30, 100, 180, 0.08);
  border-color: rgba(30, 100, 180, 0.18);
}

/* #tag 标签:深蓝色系 */
[data-theme='light'] .detail-inner .detail-inner__tag {
  color: rgba(30, 80, 140, 0.75);
  background: rgba(30, 100, 180, 0.07);
}

/* 交互栏分隔线 */
[data-theme='light'] .detail-inner .detail-inner__actions {
  border-top-color: rgba(0, 0, 0, 0.08);
}

/* 点赞按钮 */
[data-theme='light'] .detail-inner .detail-inner__like-btn {
  background: rgba(0, 0, 0, 0.04);
}

[data-theme='light'] .detail-inner .detail-inner__like-btn:hover {
  background: rgba(0, 0, 0, 0.08);
}

/* 评论区分隔线 */
[data-theme='light'] .detail-inner .detail-inner__comments {
  border-top-color: rgba(0, 0, 0, 0.08);
}

/* 评论输入框 */
[data-theme='light'] .detail-inner .detail-inner__comment-input {
  border-color: rgba(0, 0, 0, 0.12);
  background: rgba(0, 0, 0, 0.03);
}

[data-theme='light'] .detail-inner .detail-inner__comment-submit {
  border-color: rgba(30, 100, 180, 0.2);
  background: rgba(30, 100, 180, 0.08);
  color: rgba(30, 70, 110, 0.82);
}
</style>
