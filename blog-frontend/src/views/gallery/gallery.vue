<template>
  <PageBackground>
    <main class="gallery-page">
      <section id="gallery-projects" class="gallery-section">
        <div class="section-heading">
          <span class="gallery-kicker">{{ siteText.gallery.kicker }}</span>
          <h2>{{ siteText.gallery.title }}</h2>
          <p>{{ siteText.gallery.subtitle }}</p>
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
import { onMounted, ref } from 'vue'
import PageBackground from '@/components/PageBackground.vue'
import GlassProjectLink from '@/components/gallery/GlassProjectLink.vue'
import { getGalleryProjects } from '@/data/gallery'
import { fetchGalleryProjects, toFrontendGalleryProject } from '@/api/gallery'
import { siteText } from '@/data/site-text'
import type { GalleryProject } from '@/types'

const projects = ref<GalleryProject[]>(getGalleryProjects())

// 启动时尝试从后端 API 加载（fallback 到 glob）
onMounted(async () => {
  try {
    const items = await fetchGalleryProjects()
    if (items.length > 0) {
      projects.value = items.map(toFrontendGalleryProject)
    }
  } catch {
    // 后端不可用时保持 glob 数据
  }
})
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
