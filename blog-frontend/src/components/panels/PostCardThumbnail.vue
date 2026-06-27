<template>
  <RouterLink :to="`/post/${post.slug}`" class="post-thumb">
    <div class="post-thumb-cover">
      <img v-if="thumbnail" :src="thumbnail" :alt="post.title" class="post-thumb-img" />
      <div v-else class="post-thumb-placeholder">
        <span class="placeholder-icon">📝</span>
      </div>
    </div>
    <div class="post-thumb-body">
      <h3 class="post-thumb-title">{{ post.title }}</h3>
      <span class="post-thumb-date">{{ post.date }}</span>
    </div>
  </RouterLink>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
import type { Post } from '@/types'

defineProps<{
  post: Post
  thumbnail?: string
}>()
</script>

<style scoped>
.post-thumb {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  border-radius: 1rem;
  overflow: hidden;
  text-decoration: none;
  transition:
    transform 0.25s ease,
    box-shadow 0.25s ease;
  min-height: 0;
}

.post-thumb:hover {
  transform: translateY(-3px);
}

.post-thumb-cover {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  border-radius: 0.75rem;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.04);
}

.post-thumb-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.post-thumb-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.06), rgba(255, 255, 255, 0.02));
}

.placeholder-icon {
  font-size: 2rem;
  opacity: 0.5;
}

.post-thumb-body {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  padding: 0 0.25rem;
}

.post-thumb-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.92);
  line-height: 1.4;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.post-thumb-date {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.45);
}
</style>