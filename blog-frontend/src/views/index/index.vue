<template>
  <div
    class="relative min-h-screen w-full flex flex-col items-center justify-center bg-cover bg-center bg-no-repeat"
    :style="{ backgroundImage: `url(${bgImage})` }"
  >
    <div class="absolute inset-0 bg-black/45"></div>

    <!-- 标题 -->
    <div class="relative z-10 w-full text-center" :class="showContent ? 'title-up' : ''">
      <h1 class="text-4xl sm:text-5xl md:text-7xl font-bold text-white tracking-wider select-none">
        {{ displayedText }}<span class="animate-pulse">|</span>
      </h1>
    </div>

    <!-- 内容面板区域 -->
    <div class="panels-container" :class="showContent ? 'panels-visible' : 'panels-hidden'">
      <div class="flex flex-col md:flex-row gap-6">
        <!-- 左侧面板 - 个人信息（改 md:w-[25%] 调整宽度） -->
        <div class="panel w-full md:w-[25%] flex flex-col items-center text-center">
          <img :src="avatarImage" alt="avatar" class="avatar" />
          <h2 class="name">Starlit</h2>
          <p class="bio">分享技术、生活和思考的个人博客</p>
          <div class="social-links">
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
        <!-- 右侧面板 - 博文内容（改 md:w-[75%] 调整宽度，与左侧合计 100%） -->
        <div class="panel w-full md:w-[75%]">
          <h2 class="panel-title">博文标题</h2>
          <div class="panel-body">
            <p class="text-white/50 text-sm">博文标题列表将显示在这里...</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 上滑按钮 -->
    <Transition name="arrow-fade">
      <button
        v-if="!showContent"
        class="absolute bottom-8 z-10 flex flex-col items-center gap-2 cursor-pointer bg-transparent border-none"
        @click="handleSlideUp"
        aria-label="向上滑动"
      >
        <span class="arrow-text">向上滑动</span>
        <span class="arrow-icon">▲</span>
      </button>
    </Transition>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import bgImage from '@/assets/img/test.jfif'
import avatarImage from '@/assets/img/test2.jpg'

const fullText = "Starlitn'blog"
const displayedText = ref('')
const showContent = ref(false)
let timer = null

const socialLinks = [
  { label: 'GitHub', icon: '🐙', url: 'https://github.com' },
  { label: 'Twitter', icon: '🐦', url: 'https://twitter.com' },
  { label: 'Email', icon: '✉️', url: 'mailto:example@example.com' },
  { label: 'RSS', icon: '📡', url: '/rss' },
]

function startTyping() {
  let index = 0
  timer = setInterval(() => {
    if (index < fullText.length) {
      displayedText.value += fullText[index]
      index++
    } else {
      clearInterval(timer)
      timer = null
    }
  }, 100)
}

function handleSlideUp() {
  if (showContent.value) return
  showContent.value = true
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
  startTyping()
  window.addEventListener('wheel', onWheel, { passive: true })
  window.addEventListener('mousedown', onStart)
  window.addEventListener('mouseup', onEnd)
  window.addEventListener('touchstart', onStart, { passive: true })
  window.addEventListener('touchend', onEnd, { passive: true })
})

onUnmounted(() => {
  if (timer) {
    clearInterval(timer)
  }
  window.removeEventListener('wheel', onWheel)
  window.removeEventListener('mousedown', onStart)
  window.removeEventListener('mouseup', onEnd)
  window.removeEventListener('touchstart', onStart)
  window.removeEventListener('touchend', onEnd)
})
</script>

<style scoped>
/* ============================================
   右侧面板 - 博文内容
   ============================================ */
.panel-title {
  font-size: 1.125rem; /* 标题字号 */
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.panel-body {
  color: rgba(255, 255, 255, 0.7);
}

/* ============================================
   标题上移动画
   ============================================ */
.title-up {
  transform: translateY(-60px); /* 标题上移距离 */
  transition: transform 0.6s ease;
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

.panel-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.panel-body {
  color: rgba(255, 255, 255, 0.7);
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
   面板容器 - 始终渲染，CSS 控制显隐（避免 backdrop-filter 首次合成延迟）
   ============================================ */
.panels-container {
  position: relative;
  z-index: 10;
  width: 100%;
  margin-left: auto;
  margin-right: auto;
  margin-top: 3rem;
  max-width: 90rem; /* 面板区域最大宽度 */
  padding-left: 2rem; /* 距屏幕左边 */
  padding-right: 2rem; /* 距屏幕右边 */
  transition:
    opacity 0.5s ease 0.2s,
    transform 0.5s ease 0.2s;
}

.panels-hidden {
  opacity: 0;
  transform: translateY(30px);
  pointer-events: none; /* 隐藏时不可交互 */
}

.panels-visible {
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
