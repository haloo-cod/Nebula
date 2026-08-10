<template>
    <main class="project-page">
      <RouterLink to="/gallery" class="back-link">返回展览</RouterLink>

      <article v-if="project" class="project-doc glass-strong">
        <header class="project-header">
          <span class="project-kicker">{{ project.year }} / {{ project.status }}</span>
          <h1>{{ project.title }}</h1>
          <p>{{ project.description }}</p>
          <div class="project-tags">
            <span v-for="tag in project.tags" :key="tag">{{ tag }}</span>
          </div>
        </header>

        <div v-if="loading" class="doc-state">文档加载中...</div>
        <div v-else class="markdown-body" v-html="html"></div>
      </article>

      <section v-else class="project-doc glass-strong not-found">
        <span class="project-kicker">Not Found</span>
        <h1>项目不存在或尚未公开</h1>
        <p>这个项目文档可能还在整理中,可以先返回展览页查看其他项目。</p>
      </section>
    </main>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { getGalleryProject, renderGalleryProject } from '@/data/gallery'
import { fetchGalleryProject } from '@/api/gallery'
import { renderMarkdown } from '@/data/posts'
import type { GalleryProject } from '@/types'

const route = useRoute()
const html = ref('')
const loading = ref(true)
const project = ref<GalleryProject | null>(getGalleryProject(String(route.params.slug)))

async function loadProject(slug: string) {
  loading.value = true
  try {
    // 优先从后端 API 获取
    const detail = await fetchGalleryProject(slug)
    project.value = {
      slug: detail.slug,
      title: detail.title,
      description: detail.description,
      tags: detail.tags,
      status: detail.status,
      year: detail.year,
      featured: detail.is_featured,
      content: detail.content_md,
    }
    html.value = detail.content_md ? await renderMarkdown(detail.content_md) : ''
  } catch {
    // 后端不可用时 fallback 到本地 glob
    project.value = getGalleryProject(slug)
    html.value = (await renderGalleryProject(slug)) || ''
  }
  loading.value = false
}

void loadProject(String(route.params.slug))
watch(
  () => route.params.slug,
  (slug) => {
    void loadProject(String(slug))
  },
)
</script>

<style scoped>
.project-page {
  position: relative;
  z-index: 10;
  width: min(100%, 64rem);
  margin: 0 auto;
  padding: 8rem 1rem 5rem;
}

.back-link {
  display: inline-flex;
  margin-bottom: 1rem;
  color: var(--text-muted);
  font-size: 0.86rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-decoration: none;
}

.back-link:hover {
  color: var(--text-primary);
}

.project-doc {
  border-radius: 1.25rem;
  padding: clamp(1.5rem, 4vw, 3rem);
}

.project-header {
  padding-bottom: 2rem;
  border-bottom: 1px solid rgba(214, 240, 255, 0.12);
}

.project-kicker {
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: rgba(140, 218, 214, 0.74);
}

.project-header h1,
.not-found h1 {
  margin-top: 0.85rem;
  font-size: clamp(2.4rem, 7vw, 5.5rem);
  line-height: 0.95;
  font-weight: 900;
  letter-spacing: -0.08em;
  color: var(--text-primary);
}

.project-header p,
.not-found p {
  max-width: 42rem;
  margin-top: 1.1rem;
  font-size: 1rem;
  line-height: 1.8;
  color: var(--text-secondary);
}

.project-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 1.25rem;
}

.project-tags span {
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.06);
  padding: 0.36rem 0.64rem;
  font-size: 0.72rem;
  color: var(--text-muted);
}

.doc-state {
  padding-top: 2rem;
  color: var(--text-muted);
}

.markdown-body {
  padding-top: 2rem;
  color: var(--text-primary);
  line-height: 1.9;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3) {
  margin-top: 1.7rem;
  margin-bottom: 0.8rem;
  color: var(--text-primary);
  font-weight: 800;
}

.markdown-body :deep(p),
.markdown-body :deep(li) {
  color: var(--text-secondary);
}

.markdown-body :deep(ul) {
  margin: 0.75rem 0 0 1.2rem;
}

.not-found {
  min-height: 20rem;
}
</style>
