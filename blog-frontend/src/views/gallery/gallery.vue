<template>
  <PageBackground>
    <main class="gallery-page">
      <section id="gallery-projects" class="gallery-section">
        <div class="section-heading">
          <span class="gallery-kicker">Projects</span>
          <h2>项目</h2>
          <p>点击项目卡片进入独立 Markdown 文档,不进入博客归档和统计。</p>
        </div>

        <div class="project-grid">
          <GlassProjectLink
            v-for="(project, index) in projects"
            :key="project.slug"
            :project="project"
            :specimen-index="String(index + 1).padStart(2, '0')"
          />
        </div>
      </section>
    </main>
  </PageBackground>
</template>

<script setup lang="ts">
import PageBackground from '@/components/PageBackground.vue'
import GlassProjectLink from '@/components/gallery/GlassProjectLink.vue'
import { getGalleryProjects } from '@/data/gallery'

const projects = getGalleryProjects()
</script>

<style scoped>
.gallery-page {
  position: relative;
  z-index: 10;
  width: min(100%, 76rem);
  margin: 0 auto;
  padding: 7rem 1rem 5rem;
}

.gallery-kicker {
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: rgba(140, 218, 214, 0.74);
}

.section-heading h2 {
  margin-top: 0.75rem;
  font-weight: 850;
  letter-spacing: -0.06em;
  color: var(--text-primary);
}

.section-heading p {
  max-width: 42rem;
  margin-top: 1rem;
  font-size: 1rem;
  line-height: 1.8;
  color: var(--text-secondary);
}

.gallery-section {
  scroll-margin-top: 7rem;
  margin-top: 30px;
}

.section-heading {
  margin-bottom: 1.5rem;
}

.section-heading h2 {
  font-size: clamp(2rem, 5vw, 4rem);
  line-height: 1;
}

.project-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

@media (max-width: 900px) {
  .gallery-page {
    padding-top: 6.5rem;
  }

  .project-grid {
    grid-template-columns: 1fr;
  }
}
</style>
