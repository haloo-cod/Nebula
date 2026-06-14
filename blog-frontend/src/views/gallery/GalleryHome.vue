<template>
  <GlassPanel class="gallery-panel">
    <div class="gallery-grid">
      <RouterLink
        v-for="item in gallerySections"
        :key="item.slug"
        :to="`/gallery/${item.slug}`"
        class="gallery-card"
      >
        <span class="gallery-icon">{{ item.icon }}</span>
        <h2 class="gallery-title">{{ item.title }}</h2>
        <p class="gallery-desc">{{ item.description }}</p>
      </RouterLink>
    </div>
  </GlassPanel>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
import GlassPanel from '@/components/panels/GlassPanel.vue'

/** 展览分区卡片 */
interface GallerySection {
  slug: string // 路由 slug
  title: string // 标题
  description: string // 描述
  icon: string // 图标字符
}

const gallerySections: GallerySection[] = [
  { slug: 'projects', title: '项目', description: '正在构建与沉淀的作品。', icon: '✦' },
  { slug: 'skills', title: '技能', description: '技术栈、工具链与实践经验。', icon: '⌘' },
  { slug: 'timeline', title: '人生时间线', description: '走过的节点与故事。', icon: '◷' },
  { slug: 'essays', title: '随笔', description: '随手写下的想法与记录。', icon: '✎' },
  { slug: 'animation', title: '动画', description: '看过的番剧。', icon: '❖' },
  { slug: 'images', title: '图片', description: '生活片段与视觉记录。', icon: '◐' },
]
</script>

<style scoped>
.gallery-panel {
  min-height: 60vh;
}

.gallery-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1rem;
  min-height: calc(60vh - 3rem);
}

.gallery-card {
  position: relative;
  min-height: 11rem;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  overflow: hidden;
  border-radius: 0.9rem;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background:
    radial-gradient(circle at 30% 20%, rgba(140, 185, 255, 0.12), transparent 38%),
    rgba(255, 255, 255, 0.035);
  padding: 1.25rem;
  text-decoration: none;
  transition:
    transform 0.25s ease,
    border-color 0.25s ease,
    background 0.25s ease;
}

.gallery-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(to bottom, transparent, rgba(0, 0, 0, 0.18));
  pointer-events: none;
}

.gallery-card:hover {
  transform: translateY(-3px);
  border-color: rgba(140, 185, 255, 0.28);
  background:
    radial-gradient(circle at 30% 20%, rgba(140, 185, 255, 0.18), transparent 42%),
    rgba(255, 255, 255, 0.055);
}

.gallery-icon,
.gallery-title,
.gallery-desc {
  position: relative;
  z-index: 1;
}

.gallery-icon {
  width: 2.25rem;
  height: 2.25rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-bottom: auto;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.07);
  color: rgba(200, 225, 255, 0.85);
  font-size: 1.1rem;
}

.gallery-title {
  margin-top: 2rem;
  font-size: 1.05rem;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
  letter-spacing: 0.06em;
}

.gallery-desc {
  margin-top: 0.45rem;
  font-size: 0.78rem;
  line-height: 1.6;
  color: rgba(255, 255, 255, 0.48);
}

@media (max-width: 767px) {
  .gallery-grid {
    grid-template-columns: 1fr;
  }
}
</style>
