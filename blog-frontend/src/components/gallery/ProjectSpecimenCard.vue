<template>
  <article class="project-card">
    <div class="project-meta">
      <span>Project {{ specimenIndex }}</span>
      <span>{{ project.year }} / {{ project.status }}</span>
    </div>

    <div class="project-body">
      <h3>{{ project.title }}</h3>
      <p class="project-desc">{{ project.description }}</p>
    </div>

    <div class="project-footer">
      <div class="project-tags">
        <span v-for="tag in project.tags" :key="tag">{{ tag }}</span>
      </div>
      <span class="project-action">查看文档 -></span>
    </div>
  </article>
</template>

<script setup lang="ts">
import type { GalleryProject } from '@/types'

defineProps<{
  project: GalleryProject
  specimenIndex: string
}>()
</script>

<style scoped>
.project-card {
  min-height: 20rem;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: clamp(1.25rem, 3vw, 1.85rem);
}

.project-meta {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.project-body {
  margin-top: 0rem;
  transform: translateY(-0.75rem);
}

.project-body h3 {
  font-size: clamp(1.65rem, 4vw, 3rem);
  line-height: 1;
  font-weight: 800;
  letter-spacing: -0.05em;
  color: var(--text-primary);
}

.project-desc {
  max-width: 33rem;
  margin-top: 1rem;
  font-size: 0.96rem;
  line-height: 1.8;
  color: var(--text-secondary);
}

.project-footer {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 1.5rem;
  margin-top: 2rem;
}

.project-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.project-tags span {
  border: 1px solid rgba(210, 238, 255, 0.14);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.055);
  padding: 0.35rem 0.62rem;
  font-size: 0.72rem;
  color: rgba(235, 249, 255, 0.68);
}

.project-action {
  flex-shrink: 0;
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: rgba(250, 221, 166, 0.82);
}

@media (max-width: 767px) {
  .project-footer {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
