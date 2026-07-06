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
import LiquidGlass from '@/components/LiquidGlass.vue'
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
  transition:
    border-color 0.28s ease,
    box-shadow 0.28s ease;
}

.project-link:hover .project-glass--fallback {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-color: rgba(177, 232, 229, 0.38);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.28),
    inset 0 0 24px rgba(255, 255, 255, 0.08),
    0 14px 38px rgba(3, 12, 22, 0.32);
}
</style>
