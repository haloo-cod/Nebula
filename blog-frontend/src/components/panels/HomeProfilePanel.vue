<template>
  <div class="home-profile glass-surface">
    <div class="hp-top">
      <img :src="avatar" alt="avatar" class="hp-avatar" translate="no" />
      <div class="hp-info">
        <h2 class="hp-name">{{ name }}</h2>
        <p class="hp-bio">{{ bio }}</p>
      </div>
    </div>
    <div class="hp-social" translate="no">
      <a
        v-for="link in links"
        :key="link.label"
        :href="link.url"
        :title="link.label"
        target="_blank"
        rel="noopener"
        class="hp-social-icon"
        >{{ link.icon }}</a
      >
    </div>
  </div>
</template>

<script setup lang="ts">
import type { SocialLink } from '@/types'

withDefaults(
  defineProps<{
    avatar: string
    name?: string
    bio?: string
    links?: SocialLink[]
  }>(),
  {
    name: 'Starlit',
    bio: '分享技术、生活和思考的个人博客',
    links: () => [],
  },
)
</script>

<style scoped>
.home-profile {
  min-height: 350px;
  display: flex;
  flex-direction: column;
  padding: 1.5rem;
  box-sizing: border-box;
  border-radius: 16px;
}

.hp-top {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
}

.hp-avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid rgba(255, 255, 255, 0.2);
  flex-shrink: 0;
}

.hp-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.hp-name {
  font-size: 1.1rem;
  font-weight: 700;
  color: #ffffff;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.7);
  margin: 0 0 0.25rem;
}

.hp-bio {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.6);
  line-height: 1.5;
  margin: 0;
}

.hp-social {
  display: flex;
  gap: 0.75rem;
  justify-content: center;
  margin-top: auto;
  padding-top: 1rem;
}

.hp-social-icon {
  font-size: 1.25rem;
  color: rgba(255, 255, 255, 0.5);
  text-decoration: none;
  transition:
    color 0.3s ease,
    transform 0.3s ease;
}

.hp-social-icon:hover {
  color: rgba(255, 255, 255, 0.9);
  transform: translateY(-2px);
}
</style>
