<template>
  <PageBackground>
    <div
      class="relative flex flex-col items-center justify-start pt-24 md:pt-0 md:justify-center min-h-screen w-full"
    >
      <!-- 面板区域（始终展开） -->
      <div class="panels-wrapper panels-expanded">
        <div class="panels-inner flex flex-col md:flex-row gap-6 items-start">
          <!-- 左侧列 -->
          <div class="left-column w-full md:w-[20%] flex flex-col gap-6">
            <!-- 个人信息面板 -->
            <div class="panel flex flex-col items-center text-center">
              <img :src="avatarImage" alt="avatar" class="avatar" translate="no" />
              <h2 class="name">Starlit</h2>
              <p class="bio">分享技术、生活和思考的个人博客</p>
              <div class="social-links" translate="no">
                <a
                  v-for="link in socialLinks"
                  :key="link.label"
                  :href="link.url"
                  :title="link.label"
                  target="_blank"
                  rel="noopener"
                  class="social-icon"
                  >{{ link.icon }}</a
                >
              </div>
            </div>

            <!-- 占位面板 -->
            <div
              class="panel panel-placeholder flex flex-col items-center justify-center text-center"
            >
              <span class="placeholder-icon">✦</span>
              <span class="placeholder-text">更多内容</span>
            </div>
          </div>

          <!-- 右侧面板 - 博文内容 -->
          <div class="panel panel-right w-full md:w-[80%]">
            <!-- 顶行：标题 + 返回按钮 -->
            <div class="post-header">
              <div class="post-header-left" v-if="post">
                <h1 class="post-title">{{ post.title }}</h1>
                <div class="post-meta" v-if="post.date">
                  <span>{{ post.date }}</span>
                  <span v-if="post.category">· {{ post.category }}</span>
                </div>
              </div>
              <button class="back-btn" @click="goBack" aria-label="返回首页">
                <span class="back-arrow">◀</span>
                <span>返回</span>
              </button>
            </div>

            <!-- 文章内容 -->
            <div v-if="loading" class="text-white/50 mt-8">加载中...</div>
            <div v-else-if="post" class="prose" v-html="post.html"></div>
            <div v-else class="text-white/50 mt-8">文章不存在</div>
          </div>
        </div>
      </div>
    </div>
  </PageBackground>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import PageBackground from '@/components/PageBackground.vue'
import avatarImage from '@/assets/img/test2.jpg'
import { getPost } from '@/data/posts'

const route = useRoute()
const router = useRouter()
const post = ref(getPost(route.params.slug))
const loading = ref(false)

const socialLinks = [
  { label: 'GitHub', icon: '🐙', url: 'https://github.com' },
  { label: 'Twitter', icon: '🐦', url: 'https://twitter.com' },
  { label: 'Email', icon: '✉️', url: 'mailto:example@example.com' },
  { label: 'RSS', icon: '📡', url: '/rss' },
]

function goBack() {
  router.push({ path: '/', state: { showContent: true } })
}
</script>

<style scoped>
/* ============================================
   面板包装器（始终展开，无滑动交互）
   ============================================ */
.panels-wrapper {
  position: relative;
  z-index: 10;
  width: 100%;
  margin-left: auto;
  margin-right: auto;
  margin-top: 5rem;
  max-width: 90rem;
  padding-left: 2rem;
  padding-right: 2rem;
  overflow: hidden;
}

.panels-expanded {
  max-height: none;
  overflow: visible;
}

.panels-inner {
  opacity: 1;
  padding-bottom: 1rem;
}

/* ============================================
   公共面板样式
   ============================================ */
.panel {
  background: rgba(0, 0, 0, 0.35);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 1rem;
  padding: 1.5rem;
  min-height: 200px;
  transform: translateZ(0);
  will-change: backdrop-filter;
}

/* ============================================
   左侧面板 - 头像、名字、简介、社交图标
   ============================================ */
.avatar {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid rgba(255, 255, 255, 0.2);
  margin-bottom: 1rem;
}

.name {
  font-size: 1.25rem;
  font-weight: 700;
  color: #fff;
  margin-bottom: 0.25rem;
}

.bio {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.55);
  margin-bottom: 1rem;
  line-height: 1.5;
}

.social-links {
  display: flex;
  gap: 0.75rem;
  justify-content: center;
  margin-top: auto;
}

.social-icon {
  font-size: 1.25rem;
  color: rgba(255, 255, 255, 0.5);
  transition:
    color 0.3s ease,
    transform 0.3s ease;
}

.social-icon:hover {
  color: rgba(255, 255, 255, 0.9);
  transform: translateY(-2px);
}

/* ============================================
   右侧面板 - 博文内容
   ============================================ */
.panel-right {
  overflow-y: auto;
  max-height: calc(100vh - 12rem);
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 255, 255, 0.12) transparent;
}

.panel-right::-webkit-scrollbar {
  width: 6px;
}

.panel-right::-webkit-scrollbar-track {
  background: transparent;
}

.panel-right::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.12);
  border-radius: 3px;
}

.panel-right::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.22);
}

/* 占位面板 */
.panel-placeholder {
  min-height: 200px;
}

.placeholder-icon {
  font-size: 1.5rem;
  color: rgba(255, 255, 255, 0.15);
  margin-bottom: 0.5rem;
}

.placeholder-text {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.25);
}

.post-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.post-header-left {
  flex: 1;
  min-width: 0;
}

.post-title {
  font-size: 2rem;
  font-weight: 700;
  color: #fff;
  line-height: 1.3;
  margin-bottom: 0.25rem;
}

.post-meta {
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.45);
}

/* 返回按钮（面板内部右上角） */
.back-btn {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 8px 18px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(20px);
  cursor: pointer;
  color: rgba(255, 255, 255, 0.6);
  font-size: 13px;
  font-weight: 500;
  transition:
    color 0.3s ease,
    background 0.3s ease;
}

.back-btn:hover {
  color: rgba(255, 255, 255, 0.95);
  background: rgba(255, 255, 255, 0.12);
}

.back-arrow {
  font-size: 11px;
  line-height: 1;
}

@media (max-width: 767px) {
  .post-header {
    flex-direction: column;
  }

  .back-btn {
    align-self: flex-end;
  }
}

/* ============================================
   文章正文排版
   ============================================ */
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
