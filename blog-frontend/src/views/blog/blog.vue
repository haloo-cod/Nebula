<template>
  <PageBackground>
    <main class="gallery-blog-page">
      <RouterLink to="/" class="back-link">返回首页</RouterLink>

      <section class="section-heading">
        <span class="gallery-kicker">Blog</span>
        <h1>博文</h1>
        <p>这里按卡片列出博客文章,详情仍然进入原有文章页。</p>
      </section>

      <div class="post-grid">
        <RouterLink
          v-for="post in posts"
          :key="post.slug"
          :to="`/post/${post.slug}`"
          class="post-card glass-subtle"
        >
          <span class="post-date">{{ post.date || 'No date' }}</span>
          <h2>{{ post.title }}</h2>
          <p>{{ post.description || '暂无摘要。' }}</p>
          <div class="post-tags">
            <span v-for="tag in post.tags.slice(0, 4)" :key="tag">{{ tag }}</span>
          </div>
        </RouterLink>
      </div>
    </main>
  </PageBackground>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
import PageBackground from '@/components/PageBackground.vue'
import { getPosts } from '@/data/posts'

const posts = getPosts().filter((post) => !post.draft)
</script>

<style scoped>
.gallery-blog-page {
  position: relative;
  z-index: 10;
  width: min(100%, 76rem);
  margin: 0 auto;
  padding: 7rem 1rem 5rem;
}

.back-link {
  color: rgba(250, 221, 166, 0.82);
  font-size: 0.86rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-decoration: none;
}

.gallery-kicker {
  display: block;
  margin-top: 1.5rem;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: rgba(140, 218, 214, 0.74);
}

.section-heading h1 {
  margin-top: 0.75rem;
  font-size: clamp(2.5rem, 7vw, 5rem);
  line-height: 1;
  font-weight: 850;
  letter-spacing: -0.06em;
  color: rgba(255, 255, 255, 0.94);
}

.section-heading p {
  margin-top: 1rem;
  color: rgba(230, 246, 255, 0.6);
}

.post-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
  margin-top: 1.5rem;
}

.post-card {
  min-height: 13rem;
  border-radius: 1rem;
  padding: 1.25rem;
  color: inherit;
  text-decoration: none;
}

.post-date {
  font-size: 0.72rem;
  letter-spacing: 0.12em;
  color: rgba(219, 244, 255, 0.62);
}

.post-card h2 {
  margin-top: 1.2rem;
  font-size: 1.45rem;
  color: rgba(255, 255, 255, 0.92);
}

.post-card p {
  margin-top: 0.75rem;
  line-height: 1.7;
  color: rgba(230, 246, 255, 0.58);
}

.post-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  margin-top: 1rem;
}

.post-tags span {
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.055);
  padding: 0.3rem 0.55rem;
  font-size: 0.72rem;
  color: rgba(235, 249, 255, 0.68);
}

@media (max-width: 900px) {
  .post-grid {
    grid-template-columns: 1fr;
  }
}
</style>
