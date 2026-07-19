<template>
  <div class="post-carousel" @mouseenter="pause" @mouseleave="resume">
    <!-- 所有 slide 绝对定位叠放,只有 active 可见 -->
    <div
      v-for="(post, i) in slides"
      :key="post.slug"
      class="slide"
      :class="slideClass(i)"
      @click="goPost(post)"
    >
      <div class="slide-meta">
        <span v-if="post.category" class="slide-cat" :style="{ color: catColor(post.category) }">
          {{ post.category }}
        </span>
        <span class="slide-date">{{ post.date || '未标注日期' }}</span>
      </div>
      <h3 class="slide-title">{{ post.title }}</h3>
      <p v-if="post.description" class="slide-desc">{{ post.description }}</p>
    </div>

    <!-- 圆点指示器 -->
    <div class="carousel-dots">
      <span
        v-for="(_, i) in slides"
        :key="i"
        class="dot"
        :class="{ active: i === current }"
        @click.stop="goTo(i)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { getPosts } from '@/data/posts'
import { fetchPosts, toFrontendPost } from '@/api/posts'
import type { Post } from '@/types'

const router = useRouter()

// 取最新 5 篇非草稿文章（先用 glob fallback）
const slides = ref<Post[]>(
  getPosts().filter((p) => !p.draft).slice(0, 5),
)

const current = ref(0)
const paused = ref(false)
let timer: number | null = null
const INTERVAL = 5000

// 启动时尝试从 API 获取
onMounted(async () => {
  try {
    const res = await fetchPosts(1, 5)
    if (res.items.length > 0) {
      slides.value = res.items.map(toFrontendPost)
    }
  } catch {
    // 后端不可用时保持 glob 数据
  }
  resetTimer()
})

/** 分类 → 颜色 */
const categoryColors: Record<string, string> = {
  技术: 'rgba(34,211,238,0.85)',
  生活: 'rgba(167,139,250,0.85)',
  随笔: 'rgba(244,114,182,0.85)',
  项目: 'rgba(52,211,153,0.85)',
  教程: 'rgba(96,165,250,0.85)',
  前端: 'rgba(56,189,248,0.85)',
  后端: 'rgba(129,140,248,0.85)',
  AI: 'rgba(192,132,252,0.85)',
  Rust: 'rgba(251,146,60,0.85)',
  工具: 'rgba(45,212,191,0.85)',
  算法: 'rgba(251,113,133,0.85)',
  日记: 'rgba(251,191,36,0.85)',
}

function catColor(cat: string): string {
  return categoryColors[cat] || 'rgba(148,163,184,0.85)'
}

/** 根据索引计算 slide 的 CSS class */
function slideClass(i: number): string {
  if (i === current.value) return 'slide--active'
  // 判断方向:上一张 or 下一张(支持循环)
  const prev = (current.value - 1 + slides.value.length) % slides.value.length
  if (i === prev) return 'slide--prev'
  return 'slide--next'
}

function next() {
  current.value = (current.value + 1) % slides.value.length
}

function goTo(i: number) {
  current.value = i
  resetTimer()
}

function resetTimer() {
  if (timer) clearInterval(timer)
  timer = window.setInterval(() => {
    if (!paused.value) next()
  }, INTERVAL)
}

function pause() {
  paused.value = true
}

function resume() {
  paused.value = false
}

function goPost(post: Post) {
  router.push('/post/' + post.slug)
}

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
.post-carousel {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  cursor: pointer;
}

/* 所有 slide 绝对定位叠放 */
.slide {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  padding: 1rem 1.4rem;
  box-sizing: border-box;
  opacity: 0;
  transform: translateX(40%);
  transition:
    opacity 0.5s ease,
    transform 0.5s ease;
  pointer-events: none;
}

.slide--active {
  opacity: 1;
  transform: translateX(0);
  pointer-events: auto;
}

.slide--prev {
  opacity: 0;
  transform: translateX(-40%);
}

.slide--next {
  opacity: 0;
  transform: translateX(40%);
}

/* 内容样式 */
.slide-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.82rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  margin-bottom: 0.35rem;
}

.slide-cat {
  font-weight: 700;
}

.slide-date {
  color: var(--text-muted, rgba(255, 255, 255, 0.4));
}

.slide-title {
  margin: 0;
  font-size: clamp(1.05rem, 2.4vw, 1.35rem);
  font-weight: 750;
  line-height: 1.35;
  color: var(--text-primary, rgba(255, 255, 255, 0.94));
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.slide-desc {
  margin: 0.3rem 0 0;
  font-size: 0.92rem;
  line-height: 1.65;
  color: var(--text-secondary, rgba(255, 255, 255, 0.55));
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 圆点 */
.carousel-dots {
  position: absolute;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 5px;
  z-index: 2;
}

.dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  cursor: pointer;
  transition: all 0.3s ease;
}

.dot.active {
  background: rgba(255, 255, 255, 0.9);
  width: 14px;
  border-radius: 3px;
}
</style>
