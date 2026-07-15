<template>
  <PageBackground>
    <div class="post-page">
      <GlassPanel class="post-panel">
        <div class="post-rise-inner">
          <div class="post-header">
            <button class="back-btn" @click="goBack" aria-label="返回">
              <span class="back-arrow">◀</span>
              <span>返回</span>
            </button>
          </div>

          <div v-if="loading" class="post-state">加载中...</div>

          <div v-else-if="currentPost">
            <div v-if="currentPost.cover" class="post-cover">
              <img :src="currentPost.cover" :alt="currentPost.title" />
            </div>

            <div class="post-meta">
              <h1 class="post-title">{{ currentPost.title }}</h1>
              <span v-if="currentPost.date" class="post-date">{{ currentPost.date }}</span>
              <div class="post-tags-row">
                <span
                  v-if="currentPost.category"
                  class="post-cat"
                  :class="`cat-${catColorKey(currentPost.category)}`"
                >
                  {{ currentPost.category }}
                </span>
                <span v-for="tag in currentPost.tags.slice(0, 4)" :key="tag" class="post-tag">#{{ tag }}</span>
              </div>
            </div>

            <div class="prose" v-html="html"></div>
          </div>

          <div v-else class="post-state">文章不存在</div>
        </div>
      </GlassPanel>
    </div>
  </PageBackground>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import PageBackground from '@/components/PageBackground.vue'
import GlassPanel from '@/components/panels/GlassPanel.vue'
import { getPost, renderPost } from '@/data/posts'
import type { Post } from '@/types'

const route = useRoute()
const router = useRouter()
const currentPost = ref<Post | null>(null)
const html = ref('')
const loading = ref(true)

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

function catColorKey(cat: string): string {
  return categoryColors[cat] || 'slate'
}

async function load(slug: string) {
  loading.value = true
  const post = getPost(slug)
  if (!post) {
    currentPost.value = null
    html.value = ''
    loading.value = false
    return
  }
  currentPost.value = post
  html.value = (await renderPost(slug)) || ''
  loading.value = false
}

load(String(route.params.slug))
watch(
  () => route.params.slug,
  (slug) => {
    if (slug) load(String(slug))
  },
)

function goBack() {
  // 从归档页进入时路径以 /archive/ 开头,应返回归档页
  if (route.path.startsWith('/archive/')) {
    router.push('/archive')
  } else {
    router.push('/blog')
  }
}
</script>

<style scoped>
.post-page {
  position: relative;
  z-index: 10;
  width: 100%;
  max-width: 68rem;
  margin: 0 auto;
  padding: 6rem 1rem 3rem;
}

@media (min-width: 768px) {
  .post-page {
    padding-top: 8rem;
  }
}

.post-rise-inner {
  animation: contentRise 0.55s cubic-bezier(0.22, 1, 0.36, 1) both;
}

@keyframes contentRise {
  from {
    opacity: 0;
    transform: translateY(40px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (prefers-reduced-motion: reduce) {
  .post-rise-inner {
    animation: none;
  }
}

.post-header {
  margin-bottom: 1.5rem;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 8px 18px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.06);
  cursor: pointer;
  color: var(--text-muted);
  font-size: 13px;
  font-weight: 500;
  transition:
    color 0.3s ease,
    background 0.3s ease;
}

.back-btn:hover {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.12);
}

.back-arrow {
  font-size: 11px;
}

.post-state {
  margin-top: 2rem;
  text-align: center;
  color: var(--text-muted);
  font-size: 0.9rem;
}

/* ===== 文章封面 ===== */
.post-cover {
  width: 100%;
  aspect-ratio: 16 / 8;
  border-radius: 1rem;
  overflow: hidden;
  margin-bottom: 1.5rem;
  background: rgba(255, 255, 255, 0.04);
}

.post-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

/* ===== 文章元信息 ===== */
.post-meta {
  margin-bottom: 2rem;
}

.post-title {
  font-size: clamp(1.8rem, 4vw, 2.8rem);
  font-weight: 800;
  line-height: 1.2;
  letter-spacing: -0.02em;
  color: var(--text-primary);
  margin: 0 0 0.5rem;
}

.post-date {
  font-size: 0.85rem;
  letter-spacing: 0.08em;
  color: var(--text-muted);
}

.post-tags-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.8rem;
}

.post-cat {
  display: inline-block;
  padding: 0.25rem 0.7rem;
  border: 1px solid;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 600;
}

.post-tag {
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.06);
  padding: 0.25rem 0.6rem;
  font-size: 0.75rem;
  color: var(--text-muted);
}

.cat-cyan { color: #67e8f9; border-color: rgba(103, 232, 249, 0.5); }
.cat-violet { color: #c4b5fd; border-color: rgba(196, 181, 253, 0.5); }
.cat-pink { color: #f9a8d4; border-color: rgba(249, 168, 212, 0.5); }
.cat-emerald { color: #6ee7b7; border-color: rgba(110, 231, 183, 0.5); }
.cat-blue { color: #93c5fd; border-color: rgba(147, 197, 253, 0.5); }
.cat-sky { color: #7dd3fc; border-color: rgba(125, 211, 252, 0.5); }
.cat-indigo { color: #a5b4fc; border-color: rgba(165, 180, 252, 0.5); }
.cat-purple { color: #d8b4fe; border-color: rgba(216, 180, 254, 0.5); }
.cat-orange { color: #fdba74; border-color: rgba(253, 186, 116, 0.5); }
.cat-teal { color: #5eead4; border-color: rgba(94, 234, 212, 0.5); }
.cat-rose { color: #fda4af; border-color: rgba(253, 164, 175, 0.5); }
.cat-amber { color: #fcd34d; border-color: rgba(252, 211, 77, 0.5); }
.cat-slate { color: #cbd5e1; border-color: rgba(203, 213, 225, 0.4); }

/* ===== Markdown 正文 ===== */
.prose {
  color: var(--text-primary);
  line-height: 1.8;
  font-size: 1rem;
}

.prose :deep(h1) {
  font-size: 1.85rem;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.3;
  margin: 0 0 1rem;
}

.prose :deep(h2) {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 2rem 0 0.75rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.prose :deep(h3) {
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 1.5rem 0 0.5rem;
}

.prose :deep(p) {
  margin-bottom: 1rem;
}

.prose :deep(code:not(pre code)) {
  background: rgba(255, 255, 255, 0.1);
  padding: 0.15em 0.4em;
  border-radius: 0.25rem;
  font-size: 0.9em;
}

.prose :deep(pre) {
  background: rgba(0, 0, 0, 0.4);
  padding: 1rem;
  border-radius: 0.75rem;
  overflow-x: auto;
  margin-bottom: 1rem;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.prose :deep(pre code) {
  background: none;
  padding: 0;
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.8);
}

.prose :deep(ul),
.prose :deep(ol) {
  padding-left: 1.5rem;
  margin-bottom: 1rem;
}

.prose :deep(li) {
  margin-bottom: 0.25rem;
}

.prose :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 1rem;
}

.prose :deep(th),
.prose :deep(td) {
  padding: 0.5rem 0.75rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  text-align: left;
}

.prose :deep(th) {
  background: rgba(255, 255, 255, 0.05);
  font-weight: 600;
}

.prose :deep(a) {
  color: var(--text-secondary);
  text-decoration: underline;
}

.prose :deep(a:hover) {
  color: var(--text-primary);
}

.prose :deep(blockquote) {
  border-left: 3px solid rgba(255, 255, 255, 0.15);
  padding-left: 1rem;
  margin: 1rem 0;
  color: var(--text-muted);
}

.prose :deep(hr) {
  border: none;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  margin: 2rem 0;
}
</style>
