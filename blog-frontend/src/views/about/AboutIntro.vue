<template>
  <div class="about-intro">
    <div v-if="loading" class="intro-loading">正在加载...</div>
    <div v-else class="intro-prose" v-html="html"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

// 导入 about.md 原始内容
import aboutRaw from '@/assets/md/about.md?raw'

const html = ref('')
const loading = ref(true)

// 懒加载 marked（复用项目现有模式）
let markedPromise: Promise<typeof import('marked').marked> | null = null

onMounted(async () => {
  if (!markedPromise) {
    markedPromise = import('marked').then((m) => m.marked)
  }
  const marked = await markedPromise
  html.value = await marked.parse(aboutRaw)
  loading.value = false
})
</script>

<style scoped>
.about-intro {
  padding: 0 1.5rem 1.5rem;
}

.intro-loading {
  text-align: center;
  padding: 3rem 0;
  color: var(--text-muted);
  font-size: 0.85rem;
}

/* Prose 排版样式 */
.intro-prose {
  color: var(--text-primary);
  font-size: 0.95rem;
  line-height: 1.8;
}

.intro-prose :deep(h2) {
  font-size: 1.5rem;
  font-weight: 800;
  margin: 2rem 0 1rem;
  color: var(--text-primary);
}

.intro-prose :deep(h3) {
  font-size: 1.2rem;
  font-weight: 700;
  margin: 1.5rem 0 0.75rem;
  color: var(--text-primary);
}

.intro-prose :deep(p) {
  margin: 0.75rem 0;
  color: var(--text-secondary);
  line-height: 1.8;
}

.intro-prose :deep(ul) {
  padding-left: 1.5rem;
  margin: 0.75rem 0;
}

.intro-prose :deep(li) {
  margin-bottom: 0.4rem;
  color: var(--text-secondary);
  line-height: 1.7;
}

.intro-prose :deep(li::marker) {
  color: rgba(140, 185, 255, 0.6);
}

.intro-prose :deep(code) {
  padding: 0.15rem 0.4rem;
  border-radius: 0.3rem;
  background: rgba(140, 185, 255, 0.1);
  color: rgba(180, 210, 255, 0.9);
  font-size: 0.85em;
}

.intro-prose :deep(a) {
  color: rgba(140, 185, 255, 0.9);
  text-decoration: none;
  border-bottom: 1px dashed rgba(140, 185, 255, 0.4);
  transition: all 0.2s ease;
}

.intro-prose :deep(a:hover) {
  color: rgba(180, 210, 255, 1);
  border-bottom-style: solid;
}

.intro-prose :deep(blockquote) {
  margin: 1.5rem 0;
  padding: 0.75rem 1.2rem;
  border-left: 3px solid rgba(140, 185, 255, 0.4);
  background: rgba(140, 185, 255, 0.05);
  border-radius: 0 0.75rem 0.75rem 0;
}

.intro-prose :deep(blockquote p) {
  margin: 0;
  font-style: italic;
  color: var(--text-muted);
}

@media (min-width: 768px) {
  .about-intro {
    padding: 0 2.5rem 2rem;
  }

  .intro-prose {
    font-size: 1.05rem;
  }

  .intro-prose :deep(h2) {
    font-size: 1.8rem;
  }

  .intro-prose :deep(h3) {
    font-size: 1.35rem;
  }
}
</style>

<!-- Light 主题适配 -->
<style>
[data-theme='light'] .intro-prose code {
  background: rgba(50, 100, 220, 0.08);
  color: rgba(40, 80, 160, 1);
}

[data-theme='light'] .intro-prose a {
  color: rgba(40, 80, 160, 1);
  border-bottom-color: rgba(40, 80, 160, 0.3);
}

[data-theme='light'] .intro-prose blockquote {
  border-left-color: rgba(50, 100, 220, 0.4);
  background: rgba(50, 100, 220, 0.04);
}
</style>
