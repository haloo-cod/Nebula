<template>
  <PageBackground>
    <div class="relative flex justify-center min-h-screen w-full pt-28 pb-12 px-4">
      <div v-if="loading" class="text-white/50 mt-20">加载中...</div>
      <div v-else-if="post" class="post-content">
        <h1 class="post-title">{{ post.title }}</h1>
        <div class="post-meta" v-if="post.date">
          <span>{{ post.date }}</span>
          <span v-if="post.category">· {{ post.category }}</span>
        </div>
        <div class="prose" v-html="post.html"></div>
      </div>
      <div v-else class="text-white/50 mt-20">文章不存在</div>
    </div>
  </PageBackground>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import PageBackground from '@/components/PageBackground.vue'
import { getPost } from '@/data/posts'

const route = useRoute()
const post = ref(getPost(route.params.slug))
const loading = ref(false)
</script>

<style scoped>
.post-content {
  max-width: 48rem;
  width: 100%;
}

.post-title {
  font-size: 2rem;
  font-weight: 700;
  color: #fff;
  margin-bottom: 0.5rem;
  line-height: 1.3;
}

.post-meta {
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.45);
  margin-bottom: 2rem;
}

.prose {
  color: rgba(255, 255, 255, 0.8);
  line-height: 1.8;
  font-size: 1rem;
}

.prose :deep(h2) {
  font-size: 1.5rem;
  font-weight: 600;
  color: #fff;
  margin: 2rem 0 0.75rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.prose :deep(h3) {
  font-size: 1.2rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin: 1.5rem 0 0.5rem;
}

.prose :deep(p) {
  margin-bottom: 1rem;
}

.prose :deep(code:not(pre code)) {
  background: rgba(255, 255, 255, 0.1);
  padding: 0.15em 0.4em;
  border-radius: 0.25rem;
  font-size: 0.9em;
}

.prose :deep(pre) {
  background: rgba(0, 0, 0, 0.4);
  padding: 1rem;
  border-radius: 0.75rem;
  overflow-x: auto;
  margin-bottom: 1rem;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.prose :deep(pre code) {
  background: none;
  padding: 0;
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.8);
}

.prose :deep(ul),
.prose :deep(ol) {
  padding-left: 1.5rem;
  margin-bottom: 1rem;
}

.prose :deep(li) {
  margin-bottom: 0.25rem;
}

.prose :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 1rem;
}

.prose :deep(th),
.prose :deep(td) {
  padding: 0.5rem 0.75rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  text-align: left;
}

.prose :deep(th) {
  background: rgba(255, 255, 255, 0.05);
  font-weight: 600;
}

.prose :deep(a) {
  color: rgba(255, 255, 255, 0.7);
  text-decoration: underline;
}

.prose :deep(a:hover) {
  color: #fff;
}

.prose :deep(blockquote) {
  border-left: 3px solid rgba(255, 255, 255, 0.15);
  padding-left: 1rem;
  margin: 1rem 0;
  color: rgba(255, 255, 255, 0.55);
}

.prose :deep(hr) {
  border: none;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  margin: 2rem 0;
}
</style>
