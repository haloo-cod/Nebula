<template>
  <article class="moment-card" @click="handleCardClick">
    <!-- 头部:相对时间 + 心情标签 -->
    <div class="moment-card__head">
      <span class="moment-card__time">{{ relativeTime(moment.date) }}</span>
      <span v-if="moment.mood" class="moment-card__mood">{{ moodEmoji(moment.mood) }} {{ moment.mood }}</span>
    </div>

    <!-- 正文:最多 2 行,超出省略 -->
    <p class="moment-card__content">{{ moment.content }}</p>

    <!-- 底部指示条:图片数 + 评论数 + 点赞 -->
    <div class="moment-card__footer">
      <span v-if="moment.images.length > 0" class="moment-card__indicator">
        📷 {{ moment.images.length }}
      </span>
      <span class="moment-card__indicator">💬 {{ commentCount }}</span>
      <button
        class="moment-card__like-btn"
        :class="{ 'moment-card__like-btn--active': isLiked }"
        @click.stop="toggleLike"
      >
        <span class="moment-card__heart" :class="{ 'moment-card__heart--pop': justLiked }">♥</span>
        <span>{{ displayLikes }}</span>
      </button>
    </div>
  </article>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { Moment } from '@/types'
import { likeMoment } from '@/api/moments'

const props = defineProps<{
  moment: Moment
}>()

const emit = defineEmits<{
  (e: 'select', moment: Moment): void
}>()

// ============ 点击卡片 → 弹出详情 ============

function handleCardClick() {
  emit('select', props.moment)
}

// ============ 点赞逻辑(localStorage 持久化) ============

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

onMounted(() => {
  isLiked.value = getLikedIds().has(props.moment.id)
})

const displayLikes = computed(() => props.moment.likes + localLikeDelta.value)

function toggleLike() {
  const ids = getLikedIds()
  if (isLiked.value) {
    // 取消点赞（本地记忆，API 不支持取消）
    ids.delete(props.moment.id)
    localLikeDelta.value--
    isLiked.value = false
  } else {
    ids.add(props.moment.id)
    localLikeDelta.value++
    isLiked.value = true
    justLiked.value = true
    setTimeout(() => { justLiked.value = false }, 400)
    // 调用后端 API 点赞（静默，不阻塞 UI）
    likeMoment(props.moment.id).catch(() => {})
  }
  saveLikedIds(ids)
}

// ============ 评论数（从 API 响应的 commentCount 字段获取） ============

const commentCount = computed(() => props.moment.commentCount || 0)

// ============ 工具函数 ============

/** 相对时间显示 */
function relativeTime(dateStr: string): string {
  const now = Date.now()
  const d = new Date(dateStr).getTime()
  const diff = now - d
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 3) return `${days}天前`

  const date = new Date(dateStr)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
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
  return map[mood] || '📝'
}
</script>

<style scoped>
.moment-card {
  width: 100%;
  padding: 1.1rem 1.3rem;
  cursor: pointer;
  overflow: hidden;
  min-width: 0;
  box-sizing: border-box;
  transition: background 0.2s ease;
}

.moment-card:hover {
  background: rgba(255, 255, 255, 0.03);
}

.moment-card__head {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-bottom: 0.5rem;
  flex-wrap: wrap;
}

.moment-card__time {
  font-size: 0.75rem;
  color: var(--text-muted);
  font-variant-numeric: tabular-nums;
}

.moment-card__mood {
  font-size: 0.72rem;
  color: rgba(180, 220, 255, 0.7);
  background: rgba(140, 200, 255, 0.08);
  padding: 0.12rem 0.45rem;
  border-radius: 999px;
  border: 1px solid rgba(140, 200, 255, 0.15);
}

/* 正文:最多 2 行省略 */
.moment-card__content {
  margin: 0;
  color: var(--text-primary);
  font-size: 0.92rem;
  line-height: 1.7;
  white-space: normal;
  word-break: break-all;
  overflow-wrap: break-word;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
}

/* 底部指示条 */
.moment-card__footer {
  display: flex;
  align-items: center;
  gap: 0.9rem;
  margin-top: 0.7rem;
  padding-top: 0.55rem;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.moment-card__indicator {
  font-size: 0.75rem;
  color: var(--text-muted);
  user-select: none;
}

.moment-card__like-btn {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  margin-left: auto;
  padding: 0.25rem 0.55rem;
  border: none;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-secondary);
  font-size: 0.78rem;
  cursor: pointer;
  transition:
    color 0.2s ease,
    background 0.2s ease;
}

.moment-card__like-btn:hover {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.08);
}

.moment-card__like-btn--active {
  color: #f87171;
}

.moment-card__like-btn--active:hover {
  color: #f87171;
}

/* 点赞心跳动画 */
.moment-card__heart--pop {
  animation: heartPop 0.4s cubic-bezier(0.17, 0.67, 0.29, 1.3);
}

@keyframes heartPop {
  0% { transform: scale(1); }
  50% { transform: scale(1.4); }
  100% { transform: scale(1); }
}
</style>
