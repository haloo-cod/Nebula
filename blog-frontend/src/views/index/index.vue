<template>
  <PageBackground>
    <div
      class="relative flex flex-col items-center justify-start pt-24 md:pt-0 w-full"
      :class="!isMobile && !showContent ? 'h-screen overflow-hidden' : ''"
    >
      <!-- 桌面端标题 -->
      <div
        class="hidden md:block absolute left-0 right-0 z-20 w-full text-center title-pos"
        :class="showContent ? 'title-up' : ''"
        translate="no"
      >
        <h1
          class="text-4xl sm:text-5xl md:text-7xl font-bold text-white tracking-wider select-none"
        >
          {{ displayedText }}<span class="animate-pulse">|</span>
        </h1>
      </div>

      <!-- 面板区域 -->
      <div
        class="panels-wrapper"
        :class="isMobile ? 'panels-expanded' : showContent ? 'panels-expanded' : 'panels-collapsed'"
      >
        <div class="panels-container md:flex md:gap-6">
          <!-- 左侧列 (现在是独立的) -->
          <div class="left-column sticky-panel w-full md:w-[20%] flex-shrink-0">
            <div class="flex flex-col gap-6">
              <!-- 个人信息面板 -->
              <div class="panel panel-compact flex flex-col items-center text-center">
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
              <div class="panel panel-placeholder flex flex-col items-center justify-center text-center">
                <span class="placeholder-icon">✦</span>
                <span class="placeholder-text">更多内容</span>
              </div>
            </div>
          </div>
          <!-- 右侧面板 - 博文列表 -->
          <div class="right-panel-wrapper w-full md:w-[80%]">
            <!-- 移动端标题 -->
            <div class="md:hidden text-center mb-4" translate="no">
              <h1 class="text-3xl font-bold text-white tracking-wider select-none">
                {{ displayedText }}<span class="animate-pulse">|</span>
              </h1>
            </div>
            <div class="panel right-panel">
              <div class="panel-body">
                <div v-if="posts.length === 0" class="text-white/50 text-sm">加载中...</div>
                <ul class="post-list">
                  <li v-for="post in posts" :key="post.slug">
                    <RouterLink :to="`/post/${post.slug}`" class="post-item">
                      <span class="post-title">{{ post.title }}</span>
                      <span class="post-date" v-if="post.date">{{ post.date }}</span>
                      <span class="post-desc" v-if="post.description">{{ post.description }}</span>
                    </RouterLink>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 上滑按钮（仅桌面端） -->
      <Transition name="arrow-fade">
        <button
          v-if="!isMobile && !showContent"
          class="absolute bottom-8 z-10 hidden md:flex flex-col items-center gap-2 cursor-pointer bg-transparent border-none"
          @click="handleSlideUp"
          aria-label="向上滑动"
        >
          <span class="arrow-text">向上滑动</span>
          <span class="arrow-icon">▲</span>
        </button>
      </Transition>
    </div>
  </PageBackground>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { RouterLink } from 'vue-router'
import PageBackground from '@/components/PageBackground.vue'
import avatarImage from '@/assets/img/test2.jpg'
import { getPosts } from '@/data/posts'

const fullText = "Starlitn'blog"
const displayedText = ref(fullText)
const showContent = ref(false)
const posts = ref([])
const isMobile = ref(window.innerWidth < 768)

const socialLinks = [
  { label: 'GitHub', icon: '🐙', url: 'https://github.com' },
  { label: 'Twitter', icon: '🐦', url: 'https://twitter.com' },
  { label: 'Email', icon: '✉️', url: 'mailto:example@example.com' },
  { label: 'RSS', icon: '📡', url: '/rss' },
]

function handleSlideUp() {
  if (showContent.value) return
  showContent.value = true
  removeListeners()
}

function removeListeners() {
  window.removeEventListener('wheel', onWheel)
  window.removeEventListener('mousedown', onStart)
  window.removeEventListener('mouseup', onEnd)
  window.removeEventListener('touchstart', onStart)
  window.removeEventListener('touchend', onEnd)
}

let startY = 0
let isDragging = false

function getClientY(e) {
  return e.touches ? e.touches[0].clientY : e.clientY
}

function onStart(e) {
  if (showContent.value) return
  startY = getClientY(e)
  isDragging = true
}

function onEnd(e) {
  if (!isDragging) return
  isDragging = false
  const endY = e.changedTouches ? e.changedTouches[0].clientY : e.clientY
  const deltaY = startY - endY
  if (deltaY > 50) {
    handleSlideUp()
  }
}

function onWheel(e) {
  if (e.deltaY < 0) {
    handleSlideUp()
  }
}

onMounted(() => {
  posts.value = getPosts()
  if (history.state?.showContent) {
    showContent.value = true
  }
  if (!isMobile.value) {
    window.addEventListener('wheel', onWheel, { passive: true })
    window.addEventListener('mousedown', onStart)
    window.addEventListener('mouseup', onEnd)
    window.addEventListener('touchstart', onStart, { passive: true })
    window.addEventListener('touchend', onEnd, { passive: true })
  }
})

onUnmounted(() => {
  removeListeners()
})
</script>

<style scoped>
/* ============================================
    右侧面板 - 博文内容
    ============================================ */
.panel-body {
  color: rgba(255, 255, 255, 0.7);
  padding-bottom: 800px;
}

/* 博文列表 */
.post-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.post-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 0.75rem 1rem;
  border-radius: 0.75rem;
  transition: background 0.2s ease;
  text-decoration: none;
}

.post-item:hover {
  background: rgba(255, 255, 255, 0.06);
}

/* 右侧面板 - 桌面端独立滚动 */
@media (min-width: 768px) {
  .sticky-panel {
    position: sticky;
    top: 120px; /* 导航栏高度 + 间距 */
    align-self: flex-start; /* 防止被拉伸 */
  }
}

.post-title {
  font-size: 1rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.post-date {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.4);
}

.post-desc {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.5);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* ============================================
   标题上移动画
   ============================================ */
.title-pos {
  top: 42vh;
  transform: translateY(-50%) translateZ(0);
  transition: transform 2s ease;
  will-change: transform;
}

.title-up {
  transform: translateY(calc(-50% - 160px));
}

/* ============================================
   内容面板 - 公共样式
   ============================================ */
.panel {
  background: rgba(0, 0, 0, 0.35); /* 面板背景透明度，越大越不透明 */
  backdrop-filter: blur(12px); /* 毛玻璃模糊程度 */
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 1rem; /* 圆角大小 */
  padding: 1.5rem; /* 面板内边距 */
  min-height: 200px; /* 面板最小高度 */
  transform: translateZ(0); /* 强制 GPU 合成层，消除模糊延迟 */
  will-change: backdrop-filter;
}

/* ============================================
   头像、名字、简介、社交图标
   ============================================ */
.avatar {
  width: 100px; /* 头像尺寸 */
  height: 100px;
  border-radius: 50%; /* 50% = 圆形，0 = 方形 */
  object-fit: cover;
  border: 2px solid rgba(255, 255, 255, 0.2);
  margin-bottom: 1rem; /* 头像与名字的间距 */
}

/* 名字 */
.name {
  font-size: 1.25rem; /* 名字字号 */
  font-weight: 700;
  color: #fff;
  margin-bottom: 0.25rem; /* 名字与简介的间距 */
}

/* 简介 */
.bio {
  font-size: 0.8rem; /* 简介字号 */
  color: rgba(255, 255, 255, 0.55); /* 简介颜色透明度 */
  margin-bottom: 1rem; /* 简介与图标的间距 */
  line-height: 1.5;
}

/* 社交图标容器 */
.social-links {
  display: flex;
  gap: 0.75rem; /* 图标之间的间距 */
  justify-content: center;
  margin-top: auto;
}

.social-icon {
  font-size: 1.25rem; /* 图标大小 */
  color: rgba(255, 255, 255, 0.5); /* 图标颜色透明度 */
  transition:
    color 0.3s ease,
    transform 0.3s ease;
}

.social-icon:hover {
  color: rgba(255, 255, 255, 0.9); /* hover 时的图标颜色 */
  transform: translateY(-2px); /* hover 时上浮距离 */
}

/* 个人信息面板 - 紧凑版 */
.panel-compact {
  padding: 1.5rem;
}

.panel-compact .avatar {
  width: 80px;
  height: 80px;
  margin-bottom: 0.75rem;
}

.panel-compact .name {
  font-size: 1.1rem;
}

.panel-compact .bio {
  font-size: 0.75rem;
  margin-bottom: 0.75rem;
}

/* ============================================
    占位面板
    ============================================ */
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

/* 上滑按钮 */
.arrow-text {
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.5);
  letter-spacing: 0.1em;
  transition: color 0.3s ease;
}

.arrow-icon {
  font-size: 1.5rem;
  color: rgba(255, 255, 255, 0.5);
  animation: bounce 1.5s ease-in-out infinite;
  transition: color 0.3s ease;
}

button:hover .arrow-text,
button:hover .arrow-icon {
  color: rgba(255, 255, 255, 0.85);
}

@keyframes bounce {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-8px);
  }
}

/* ============================================
   面板包装器 - max-height 裁剪隐藏（面板始终 opaque，backdrop-filter 不丢）
   ============================================ */
.panels-wrapper {
  position: relative;
  z-index: 10;
  width: 100%;
  margin-left: auto;
  margin-right: auto;
  margin-top: calc(42vh - 80px);
  max-height: 2000px;
  max-width: 90rem; /* 面板区域最大宽度 */
  padding-left: 0.5rem; /* 距屏幕左边 */
  padding-right: 0.5rem; /* 距屏幕右边 */
  transition: transform 2s ease; /* 展开速度，越大越慢 */
  will-change: transform;
}

.panels-collapsed {
  opacity: 0;
  transform: translateY(200px);
  pointer-events: none;
}

.panels-expanded {
  opacity: 1;
  transform: translateY(0);
}



/* 箭头淡出 */
.arrow-fade-leave-active {
  transition: all 0.4s ease;
}

.arrow-fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
}
</style>
