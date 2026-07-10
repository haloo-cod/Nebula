<template>
  <div v-if="post.cover" class="archive-card__media">
    <img :src="post.cover" :alt="post.title" class="archive-card__media-img" />
    <span class="archive-card__date">{{ formatDate(post.date) }}</span>
  </div>
  <div class="archive-card__body">
    <h3 class="archive-card__title">{{ post.title }}</h3>
    <p v-if="post.description" class="archive-card__desc">{{ post.description }}</p>
    <span
      v-if="post.category"
      class="archive-card__cat"
      :class="`cat-${catColorKey(post.category)}`"
    >
      {{ post.category }}
    </span>
  </div>
</template>

<script setup lang="ts">
import type { Post } from '@/types'

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

const props = defineProps<{
  post: Post
}>()

function catColorKey(cat: string): string {
  return categoryColors[cat] || 'slate'
}

function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  if (Number.isNaN(date.getTime())) return dateStr
  return `${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}
</script>

<style scoped>
.archive-card__media {
  position: relative;
  aspect-ratio: 16 / 10;
  overflow: hidden;
  border-radius: 0.85rem;
  background: rgba(255, 255, 255, 0.04);
  margin-bottom: 0.75rem;
}

.archive-card__media-img {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
}

.archive-card__date {
  position: absolute;
  right: 0.75rem;
  bottom: 0.75rem;
  font-size: 0.82rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.75);
  background: rgba(0, 0, 0, 0.4);
  padding: 3px 10px;
  border-radius: 4px;
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.04em;
}

.archive-card__body {
  display: flex;
  flex: 1;
  flex-direction: column;
  padding: 0 0.4rem 0.35rem;
}

.archive-card__title {
  margin: 0;
  padding: 0.75rem 0 0.35rem;
  overflow: hidden;
  color: var(--text-primary);
  font-size: 1.05rem;
  font-weight: 700;
  line-height: 1.45;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.archive-card__desc {
  flex: 1;
  margin: 0;
  overflow: hidden;
  color: var(--text-secondary);
  font-size: 0.85rem;
  line-height: 1.55;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.archive-card__cat {
  display: inline-block;
  align-self: flex-start;
  margin-top: 0.35rem;
  padding: 0.2rem 0.6rem;
  border: 1px solid;
  border-radius: 999px;
  font-size: 0.78rem;
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
</style>