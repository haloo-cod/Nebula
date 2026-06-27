<template>
  <div class="social-post">
    <div class="sp-header">
      <span class="sp-mood">{{ mood }}</span>
      <span class="sp-time">{{ time }}</span>
    </div>
    <p class="sp-content">{{ content }}</p>
    <div v-if="image" class="sp-image">
      <img :src="image" :alt="content" />
    </div>
    <div class="sp-footer">
      <div class="sp-actions">
        <button class="sp-action-btn" @click="liked = !liked">
          <span class="sp-action-icon">{{ liked ? '❤️' : '🤍' }}</span>
          <span class="sp-action-count">{{ likes }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

withDefaults(
  defineProps<{
    mood: string
    time: string
    content: string
    image?: string
    likes?: number
  }>(),
  {
    image: '',
    likes: 0,
  },
)

const liked = ref(false)
</script>

<style scoped>
.social-post {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  padding: 1.25rem 1.5rem;
  height: 100%;
  box-sizing: border-box;
  min-height: 0;
}

.sp-header {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.sp-mood {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.85);
  background: rgba(120, 180, 255, 0.15);
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
}

.sp-time {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.45);
}

.sp-content {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.85);
  line-height: 1.65;
  margin: 0;
}

.sp-image {
  width: 100%;
  max-height: 180px;
  border-radius: 0.75rem;
  overflow: hidden;
}

.sp-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.sp-footer {
  margin-top: auto;
}

.sp-actions {
  display: flex;
  gap: 1rem;
}

.sp-action-btn {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.85rem;
  transition: color 0.2s ease;
}

.sp-action-btn:hover {
  color: rgba(255, 255, 255, 0.9);
}

.sp-action-icon {
  font-size: 1rem;
}

.sp-action-count {
  font-size: 0.8rem;
}
</style>