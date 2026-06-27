<template>
  <div class="home-profile">
    <!-- 顶部：头像 + 信息 -->
    <div class="hp-top">
      <img :src="avatar" alt="avatar" class="hp-avatar" translate="no" />
      <div class="hp-info">
        <h2 class="hp-name">{{ name }}</h2>
        <p class="hp-bio">{{ bio }}</p>
      </div>
    </div>

    <!-- 底部：统计格子（左）+ 社交链接（右） -->
    <div class="hp-bottom">
      <div class="hp-stats">
        <div class="stat-box">
          <span class="stat-value">{{ totalPosts }}</span>
          <span class="stat-label">文章</span>
        </div>
        <div class="stat-box">
          <span class="stat-value">{{ totalTags }}</span>
          <span class="stat-label">标签</span>
        </div>
        <div class="stat-box">
          <span class="stat-value">{{ totalCategories }}</span>
          <span class="stat-label">分类</span>
        </div>
        <div class="stat-box">
          <span class="stat-value">{{ daysActive }}</span>
          <span class="stat-label">活跃天数</span>
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
        >{{ link.icon }}</a>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { SocialLink } from '@/types'
import { getPosts } from '@/data/posts'

const posts = getPosts()

const totalPosts = computed(() => posts.length)

const totalTags = computed(() => {
  const tagSet = new Set<string>()
  for (const p of posts) {
    for (const tag of p.tags) {
      tagSet.add(tag)
    }
  }
  return tagSet.size
})

const totalCategories = computed(() => {
  const catSet = new Set<string>()
  for (const p of posts) {
    if (p.category) catSet.add(p.category)
  }
  return catSet.size
})

const daysActive = computed(() => {
  const dates = new Set<string>()
  for (const p of posts) {
    if (p.date) dates.add(p.date)
  }
  return dates.size
})

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
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 1.25rem 1.5rem;
  box-sizing: border-box;
  border-radius: 16px;
  overflow: hidden;
  min-height: 0;
  height: 100%;
}

/* 顶部：头像 + 信息 */
.hp-top {
  display: flex;
  align-items: center;
  gap: 1.25rem;
}

.hp-avatar {
  width: 96px;
  height: 96px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid rgba(255, 255, 255, 0.2);
  flex-shrink: 0;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
}

.hp-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.hp-name {
  font-size: 1.35rem;
  font-weight: 700;
  color: #ffffff;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.7);
  margin: 0 0 0.35rem;
  letter-spacing: 0.02em;
}

.hp-bio {
  font-size: 0.88rem;
  color: rgba(255, 255, 255, 0.65);
  line-height: 1.55;
  margin: 0;
}

/* 底部 */
.hp-bottom {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 1rem;
}

/* 统计格子（毛玻璃效果） */
.hp-stats {
  display: grid;
  grid-template-columns: repeat(4, auto);
  gap: 0.55rem;
}

.stat-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
  padding: 0.75rem 1.1rem;
  border-radius: 0.5rem;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  min-width: 0;
}

.stat-value {
  font-size: 1.35rem;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
  line-height: 1.1;
}

.stat-label {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.6);
  letter-spacing: 0.06em;
}

/* 社交链接（右下角） */
.hp-social {
  display: flex;
  gap: 0.65rem;
}

.hp-social-icon {
  font-size: 1.15rem;
  color: rgba(255, 255, 255, 0.5);
  text-decoration: none;
  transition:
    color 0.3s ease,
    transform 0.3s ease;
}

.hp-social-icon:hover {
  color: rgba(255, 255, 255, 0.95);
  transform: translateY(-2px);
}
</style>
