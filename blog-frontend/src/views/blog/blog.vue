<template>
    <main class="blog-page">
      <div class="blog-header">
        <p class="blog-kicker">{{ siteText.blog.kicker }}</p>
        <h1 class="blog-title">{{ siteText.blog.title }}</h1>
        <p class="blog-desc">{{ siteText.blog.subtitle }}</p>
        <div class="blog-filter">
          <button
            class="filter-btn"
            :class="{ active: !activeCategory }"
            @click="activeCategory = ''"
          >
            全部
          </button>
          <button
            v-for="cat in categories"
            :key="cat"
            class="filter-btn"
            :class="{ active: activeCategory === cat }"
            @click="activeCategory = activeCategory === cat ? '' : cat"
          >
            {{ cat }}
          </button>
        </div>
      </div>

      <TransitionGroup name="grid-item" tag="div" class="blog-grid">
        <RouterLink
          v-for="post in visiblePosts"
          :key="post.slug"
          :to="`/post/${post.slug}`"
          class="blog-link"
        >
          <LiquidGlass
            v-if="ui.liquidGlassEnabled"
            :cornerRadius="18"
            :theme="ui.theme"
            :blur-radius="ui.liquidGlassBlur"
            :ripple-trail="true"
            class="blog-glass"
          >
            <article class="post-card post-card--liquid">
              <span v-if="post.pinned" class="pinned-badge">
                <SvgIcon name="keep" class="pinned-badge__icon" />
                <span>置顶</span>
              </span>
              <span class="post-date">{{ post.date || '--' }}</span>
              <h2>{{ post.title }}</h2>
              <p>{{ post.description || '暂无摘要。' }}</p>
              <div class="post-meta">
                <span
                  v-if="post.category"
                  class="post-cat"
                  :class="`cat-${catColorKey(post.category)}`"
                >
                  {{ post.category }}
                </span>
                <span v-for="tag in tagsOf(post)" :key="tag" class="post-tag">#{{ tag }}</span>
              </div>
              <span class="comment-badge">💬 {{ getCommentCount(post.slug) }}</span>
            </article>
          </LiquidGlass>

          <PanelFallbackGlass v-else tag="article" class="post-card post-card-fallback">
            <span v-if="post.pinned" class="pinned-badge">
              <SvgIcon name="keep" class="pinned-badge__icon" />
              <span>置顶</span>
            </span>
            <span class="post-date">{{ post.date || '--' }}</span>
            <h2>{{ post.title }}</h2>
            <p>{{ post.description || '暂无摘要。' }}</p>
            <div class="post-meta">
              <span
                v-if="post.category"
                class="post-cat"
                :class="`cat-${catColorKey(post.category)}`"
              >
                {{ post.category }}
              </span>
              <span v-for="tag in tagsOf(post)" :key="tag" class="post-tag">#{{ tag }}</span>
            </div>
            <span class="comment-badge">💬 {{ getCommentCount(post.slug) }}</span>
          </PanelFallbackGlass>
        </RouterLink>
      </TransitionGroup>

      <div v-if="totalPages > 1" class="blog-pagination">
        <button class="page-btn" type="button" :disabled="currentPage === 1" @click="goPrevPage">
          上一页
        </button>
        <button
          v-for="page in pageNumbers"
          :key="page"
          class="page-btn"
          :class="{ 'page-btn-active': page === currentPage }"
          type="button"
          @click="currentPage = page"
        >
          {{ page }}
        </button>
        <button
          class="page-btn"
          type="button"
          :disabled="currentPage === totalPages"
          @click="goNextPage"
        >
          下一页
        </button>
      </div>
    </main>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import PanelFallbackGlass from '@/components/panels/PanelFallbackGlass.vue'
import LiquidGlass from '@/components/liquid-glass/LiquidGlass.vue'
import SvgIcon from '@/components/SvgIcon.vue'
import { getPosts } from '@/data/posts'
import { fetchPosts, toFrontendPost } from '@/api/posts'
import { siteText } from '@/data/site-text'
import { useUIStore } from '@/stores/ui'
import { fetchBatchCommentCount } from '@/api/comments'
import type { Post } from '@/types'

const ui = useUIStore()
const PAGE_SIZE = 12
const allPosts = ref<Post[]>(getPosts().filter((post) => !post.draft))
const activeCategory = ref('')
const currentPage = ref(1)

// 启动时尝试从后端 API 加载文章列表（fallback 到 glob）
onMounted(async () => {
  try {
    const res = await fetchPosts(1, 200)
    if (res.items.length > 0) {
      allPosts.value = res.items.map(toFrontendPost)
    }
  } catch {
    // 后端不可用时保持 glob 数据
  }
})

// 提取去重分类列表（排除空字符串）
const categories = computed(() => [
  ...new Set(allPosts.value.map((p) => p.category).filter(Boolean)),
])

// 根据分类筛选后的文章列表
const posts = computed(() =>
  activeCategory.value
    ? allPosts.value.filter((p) => p.category === activeCategory.value)
    : allPosts.value,
)

const categoryColors: Record<string, string> = {
  技术: 'cyan',
  生活: 'violet',
  随笔: 'pink',
  项目: 'emerald',
  教程: 'blue',
  前端: 'sky',
  后端: 'indigo',
  AI: 'purple',
  Rust: 'orange',
  工具: 'teal',
  算法: 'rose',
  日记: 'amber',
}

const totalPages = computed(() => Math.max(1, Math.ceil(posts.value.length / PAGE_SIZE)))

const visiblePosts = computed(() => {
  const start = (currentPage.value - 1) * PAGE_SIZE
  return posts.value.slice(start, start + PAGE_SIZE)
})

const pageNumbers = computed(() =>
  Array.from({ length: totalPages.value }, (_, index) => index + 1),
)

function catColorKey(cat: string): string {
  return categoryColors[cat] || 'slate'
}

function tagsOf(post: Post): string[] {
  return post.tags.slice(0, 4)
}

/** 每篇文章的评论数（从后端批量获取） */
const commentCounts = ref<Record<string, number>>({})

/** 获取指定文章的评论数 */
function getCommentCount(slug: string): number {
  return commentCounts.value[`post:${slug}`] || 0
}

/** visiblePosts 变化时批量加载评论数 */
watch(
  visiblePosts,
  async (posts) => {
    if (posts.length === 0) return
    const keys = posts.map((p) => `post:${p.slug}`)
    try {
      commentCounts.value = await fetchBatchCommentCount(keys)
    } catch {
      // 后端不可用时静默忽略
    }
  },
  { immediate: true },
)

function goPrevPage() {
  if (currentPage.value <= 1) return
  currentPage.value -= 1
}

function goNextPage() {
  if (currentPage.value >= totalPages.value) return
  currentPage.value += 1
}

watch(activeCategory, () => {
  currentPage.value = 1
})

watch(totalPages, (nextTotal) => {
  if (currentPage.value > nextTotal) currentPage.value = nextTotal
})
</script>

<style scoped>
.blog-page {
  position: relative;
  z-index: 10;
  width: min(100%, 78rem);
  margin: 0 auto;
  padding: 7rem 1rem 4rem;
}

.blog-header {
  margin-bottom: 1.8rem;
}

.blog-kicker {
  margin-bottom: 0.3rem;
  color: rgba(170, 215, 255, 0.74);
  font-size: 0.72rem;
  letter-spacing: 0.2em;
  text-transform: uppercase;
}

.blog-title {
  color: var(--text-primary);
  font-size: clamp(1.7rem, 3vw, 2.6rem);
  font-weight: 700;
  letter-spacing: 0.08em;
}

.blog-desc {
  margin-top: 0.5rem;
  color: var(--text-secondary);
  font-size: 0.9rem;
  line-height: 1.7;
}

.blog-filter {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 1.2rem;
}

.filter-btn {
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.06);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 0.8rem;
  padding: 0.35rem 0.9rem;
  transition:
    background 0.2s ease,
    color 0.2s ease,
    border-color 0.2s ease;
}

.filter-btn:hover {
  background: rgba(255, 255, 255, 0.12);
  color: var(--text-primary);
}

.filter-btn.active {
  background: rgba(110, 165, 255, 0.22);
  border-color: rgba(145, 196, 255, 0.42);
  color: var(--text-primary);
}

.blog-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.blog-pagination {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.65rem;
  margin-top: 1.6rem;
}

.page-btn {
  min-width: 2.7rem;
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  color: var(--text-primary);
  cursor: pointer;
  font-size: 0.82rem;
  padding: 0.52rem 0.9rem;
  transition:
    background 0.2s ease,
    color 0.2s ease,
    border-color 0.2s ease;
}

.page-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.14);
  color: var(--text-primary);
}

.page-btn:disabled {
  cursor: not-allowed;
  opacity: 0.38;
}

.page-btn-active {
  border-color: rgba(145, 196, 255, 0.42);
  background: rgba(110, 165, 255, 0.22);
  color: #fff;
}

.blog-link {
  display: block;
  color: inherit;
  text-decoration: none;
}

.blog-glass {
  width: 100%;
  height: 100%;
  transition:
    transform 0.24s ease,
    filter 0.24s ease;
}

.post-card {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  min-height: 14rem;
  border-radius: 1.15rem;
  padding: 1.5rem 1.6rem;
  position: relative;
}

.post-card--liquid {
  border: none;
  background: transparent;
  backdrop-filter: none;
  -webkit-backdrop-filter: none;
  box-shadow: none;
}

.post-card-fallback {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow:
    0 8px 28px rgba(0, 0, 0, 0.18),
    inset 0 1px 0 rgba(255, 255, 255, 0.24),
    inset 0 0 20px rgba(255, 255, 255, 0.06);
  transition:
    border-color 0.25s ease,
    box-shadow 0.25s ease;
}

@media (hover: hover) and (pointer: fine) {
  .blog-link:hover .post-card-fallback {
    border-color: rgba(140, 185, 255, 0.2);
    box-shadow:
      0 12px 36px rgba(80, 120, 255, 0.1),
      inset 0 1px 0 rgba(255, 255, 255, 0.24),
      inset 0 0 20px rgba(255, 255, 255, 0.06);
  }
}

.post-date {
  font-size: 0.72rem;
  letter-spacing: 0.12em;
  color: var(--text-muted);
}

.post-card h2 {
  margin: 0;
  font-size: 1.3rem;
  font-weight: 600;
  line-height: 1.45;
  color: var(--text-primary);
}

.post-card p {
  margin: 0;
  line-height: 1.7;
  color: var(--text-secondary);
  font-size: 0.88rem;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.post-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.45rem;
  margin-top: auto;
  padding-top: 0.5rem;
}

.post-cat {
  display: inline-block;
  padding: 0.2rem 0.6rem;
  border: 1px solid;
  border-radius: 999px;
  font-size: 0.75rem;
}

.post-tag {
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.06);
  padding: 0.28rem 0.55rem;
  font-size: 0.72rem;
  color: var(--text-muted);
}

.post-comments {
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.06);
  padding: 0.28rem 0.55rem;
  font-size: 0.72rem;
  color: var(--text-muted);
}

.comment-badge {
  position: absolute;
  right: 1.25rem;
  bottom: 1.15rem;
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.28rem 0.65rem;
  border-radius: 999px;
  background: rgba(140, 185, 255, 0.1);
  border: 1px solid rgba(140, 185, 255, 0.18);
  font-size: 0.78rem;
  color: rgba(180, 210, 255, 0.85);
  letter-spacing: 0.03em;
}

.cat-cyan {
  color: #67e8f9;
  border-color: rgba(103, 232, 249, 0.5);
}

.cat-violet {
  color: #c4b5fd;
  border-color: rgba(196, 181, 253, 0.5);
}

.cat-pink {
  color: #f9a8d4;
  border-color: rgba(249, 168, 212, 0.5);
}

.cat-emerald {
  color: #6ee7b7;
  border-color: rgba(110, 231, 183, 0.5);
}

.cat-blue {
  color: #93c5fd;
  border-color: rgba(147, 197, 253, 0.5);
}

.cat-sky {
  color: #7dd3fc;
  border-color: rgba(125, 211, 252, 0.5);
}

.cat-indigo {
  color: #a5b4fc;
  border-color: rgba(165, 180, 252, 0.5);
}

.cat-purple {
  color: #d8b4fe;
  border-color: rgba(216, 180, 254, 0.5);
}

.cat-orange {
  color: #fdba74;
  border-color: rgba(253, 186, 116, 0.5);
}

.cat-teal {
  color: #5eead4;
  border-color: rgba(94, 234, 212, 0.5);
}

.cat-rose {
  color: #fda4af;
  border-color: rgba(253, 164, 175, 0.5);
}

.cat-amber {
  color: #fcd34d;
  border-color: rgba(252, 211, 77, 0.5);
}

.cat-slate {
  color: #cbd5e1;
  border-color: rgba(203, 213, 225, 0.4);
}

.pinned-badge {
  position: absolute;
  top: 1.25rem;
  right: 1.25rem;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.35rem 0.85rem;
  border-radius: 999px;
  font-size: 0.8rem;
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.18);
}

.pinned-badge__icon {
  width: 1.1em;
  height: 1.1em;
}

@media (max-width: 900px) {
  .blog-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 767px) {
  .blog-page {
    padding-top: 6rem;
  }
}

/* ===== TransitionGroup 切换动画 ===== */
.grid-item-enter-active {
  transition: transform 0.3s ease;
}

.grid-item-leave-active {
  transition:
    opacity 0.2s ease,
    transform 0.2s ease;
  position: absolute;
}

.grid-item-enter-from {
  transform: translateY(16px);
}

.grid-item-leave-to {
  opacity: 0;
  transform: scale(0.95);
}

.grid-item-move {
  transition: transform 0.3s ease;
}
</style>

<!-- Light 主题适配 -->
<style>
[data-theme='light'] .blog-kicker {
  color: rgba(50, 80, 130, 0.6);
}

[data-theme='light'] .filter-btn {
  border-color: rgba(0, 0, 0, 0.1);
  background: rgba(0, 0, 0, 0.04);
  color: rgba(0, 0, 0, 0.6);
}

[data-theme='light'] .filter-btn:hover {
  background: rgba(0, 0, 0, 0.08);
  color: rgba(0, 0, 0, 0.8);
}

[data-theme='light'] .filter-btn.active {
  background: rgba(50, 100, 220, 0.12);
  border-color: rgba(50, 100, 220, 0.3);
  color: rgba(30, 70, 180, 0.9);
}

[data-theme='light'] .post-tag {
  background: rgba(0, 0, 0, 0.04);
  color: rgba(0, 0, 0, 0.5);
}

[data-theme='light'] .comment-badge {
  background: rgba(50, 100, 220, 0.08);
  border-color: rgba(50, 100, 220, 0.15);
  color: rgba(30, 70, 180, 0.75);
}

[data-theme='light'] .pinned-badge {
  background: rgba(0, 0, 0, 0.06);
  border-color: rgba(0, 0, 0, 0.1);
  color: rgba(0, 0, 0, 0.7);
}

[data-theme='light'] .page-btn {
  border-color: rgba(0, 0, 0, 0.1);
  background: rgba(0, 0, 0, 0.04);
  color: rgba(0, 0, 0, 0.6);
}

[data-theme='light'] .page-btn:hover:not(:disabled) {
  background: rgba(0, 0, 0, 0.08);
}

[data-theme='light'] .page-btn-active {
  border-color: rgba(50, 100, 220, 0.3);
  background: rgba(50, 100, 220, 0.12);
  color: rgba(30, 70, 180, 0.9);
}
</style>
