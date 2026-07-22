<template>
  <RouterLink :to="`/gallery/project/${project.slug}`" class="project-link">
    <LiquidGlass
      v-if="ui.liquidGlassEnabled"
      class="project-glass"
      :theme="ui.theme"
      :corner-radius="28"
      :blur-radius="ui.liquidGlassBlur"
      :glass-thickness="36"
      :highlight-width="3"
      ripple-trail
    >
      <ProjectSpecimenCard :project="project" :specimen-index="specimenIndex" />
    </LiquidGlass>

    <PanelFallbackGlass v-else tag="div" class="project-glass project-glass--fallback">
      <ProjectSpecimenCard :project="project" :specimen-index="specimenIndex" />
    </PanelFallbackGlass>
  </RouterLink>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
import LiquidGlass from '@/components/liquid-glass/LiquidGlass.vue'
import PanelFallbackGlass from '@/components/panels/PanelFallbackGlass.vue'
import ProjectSpecimenCard from '@/components/gallery/ProjectSpecimenCard.vue'
import { useUIStore } from '@/stores/ui'
import type { GalleryProject } from '@/types'

const ui = useUIStore()

defineProps<{
  project: GalleryProject
  specimenIndex: string
}>()
</script>

<style scoped>
.project-link {
  min-height: 20rem;
  display: block;
  color: inherit;
  text-decoration: none;
}

.project-glass {
  width: 100%;
  height: 100%;
  min-height: inherit;
  border-radius: 1.25rem;
}

.project-glass--fallback {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  transition:
    transform 0.24s ease,
    filter 0.24s ease;
}

@media (hover: hover) and (pointer: fine) {
  .project-link:hover .project-glass--fallback {
    transform: translateY(-3px);
    filter: drop-shadow(0 8px 24px rgba(80, 140, 255, 0.14));
  }
}
</style>
