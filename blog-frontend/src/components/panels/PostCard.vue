<template>
  <RouterLink :to="`/post/${post.slug}`" class="post-card">
    <div class="post-card-head">
      <span class="post-card-title">{{ post.title }}</span>
      <span v-if="post.date" class="post-card-date">{{ post.date }}</span>
    </div>

    <p v-if="post.description" class="post-card-desc">{{ post.description }}</p>

    <div class="post-card-meta" v-if="post.category || (post.tags && post.tags.length)">
      <span v-if="post.category" class="post-card-category">{{ post.category }}</span>
      <span v-for="tag in post.tags" :key="tag" class="post-card-tag">#{{ tag }}</span>
    </div>
  </RouterLink>
</template>

<script setup>
import { RouterLink } from 'vue-router'

defineProps({
  post: { type: Object, required: true },
})
</script>

<style scoped>
.post-card {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  min-height: 140px; /* 卡片高度可以大一点 */
  padding: 1.5rem 1.5rem;
  border-radius: 1rem;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.03);
  text-decoration: none;
  transition:
    background 0.25s ease,
    border-color 0.25s ease,
    transform 0.25s ease;
}

.post-card:hover {
  background: rgba(255, 255, 255, 0.07);
  border-color: rgba(255, 255, 255, 0.18);
  transform: translateY(-3px);
}

.post-card-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 1rem;
}

.post-card-title {
  font-size: 1.2rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.92);
  line-height: 1.5;
}

.post-card-date {
  flex-shrink: 0;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.45);
}

.post-card-desc {
  font-size: 0.92rem;
  color: rgba(255, 255, 255, 0.62);
  line-height: 1.7;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.post-card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: auto;
}

.post-card-category {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.8);
  background: rgba(255, 255, 255, 0.1);
  padding: 0.15rem 0.6rem;
  border-radius: 999px;
}

.post-card-tag {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
  background: rgba(255, 255, 255, 0.04);
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
}
</style>
