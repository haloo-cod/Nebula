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
      >
        <SiteTitle :instant="instantTitle" />
      </div>

      <!-- 面板区域 -->
      <div
        class="panels-wrapper"
        :class="isMobile ? 'panels-expanded' : showContent ? 'panels-expanded' : 'panels-collapsed'"
      >
        <!-- 移动端标题（打字机），位于面板上方 -->
        <div class="md:hidden mb-4 mt-16">
          <SiteTitle size="sm" :instant="instantTitle" />
        </div>
        <div class="panels-container md:flex md:gap-6">
          <!-- 左侧列 -->
          <div class="left-column sticky-panel w-full md:w-[22%] flex-shrink-0">
            <div class="flex flex-col gap-6">
              <ProfilePanel
                :avatar="avatar"
                :name="profile.name"
                :bio="profile.bio"
                :links="socialLinks"
                :compact="false"
                square
                flat
              />
              <PlaceholderPanel class="hidden md:flex" flat />
            </div>
          </div>
          <!-- 中间面板 - 博文列表（卡片样式） -->
          <div
            class="right-panel-wrapper w-full md:w-[56%] flex-shrink-0"
            :class="cameFromInApp ? 'panels-arrive' : ''"
          >
            <GlassPanel class="right-panel">
              <div class="panel-body">
                <div class="post-list">
                  <PostCard v-for="post in pagedPosts" :key="post.slug" :post="post" />
                </div>
                <!-- 分页栏 -->
                <div v-if="totalPages > 1" class="pagination">
                  <button class="page-btn" :disabled="currentPage === 1" @click="currentPage--">
                    ‹
                  </button>
                  <button
                    v-for="p in totalPages"
                    :key="p"
                    class="page-btn"
                    :class="{ 'page-btn-active': p === currentPage }"
                    @click="currentPage = p"
                  >
                    {{ p }}
                  </button>
                  <button
                    class="page-btn"
                    :disabled="currentPage === totalPages"
                    @click="currentPage++"
                  >
                    ›
                  </button>
                </div>
              </div>
            </GlassPanel>
          </div>
          <!-- 右侧列 (与左侧对称，移动端隐藏) -->
          <div class="right-column sticky-panel hidden md:block w-full md:w-[22%] flex-shrink-0">
            <div class="flex flex-col gap-6">
              <CalendarPanel flat />
              <PostStatsChart flat />
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

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import PageBackground from '@/components/PageBackground.vue'
import SiteTitle from '@/components/SiteTitle.vue'
import GlassPanel from '@/components/panels/GlassPanel.vue'
import ProfilePanel from '@/components/panels/ProfilePanel.vue'
import PlaceholderPanel from '@/components/panels/PlaceholderPanel.vue'
import CalendarPanel from '@/components/panels/CalendarPanel.vue'
import PostCard from '@/components/panels/PostCard.vue'
import PostStatsChart from '@/components/panels/PostStatsChart.vue'
import { avatar, profile, socialLinks } from '@/data/profile'
import { getPosts } from '@/data/posts'
import type { Post } from '@/types'

const isMobile = ref(window.innerWidth < 768)

// 是否从站内其它页面跳转进来（router 会写入 history.state.back）
// 刷新或直接打开首页时 back 为 null，此时才需要上滑进入动画
const cameFromInApp = !!history.state?.back || history.state?.showContent === true
const showContent = ref(isMobile.value || cameFromInApp)
// 仅站内跳转时直接显示完整标题；刷新/直接进入则播放打字机
const instantTitle = cameFromInApp

const posts = ref<Post[]>([])
const currentPage = ref(1)
const PAGE_SIZE = 8

const totalPages = computed(() => Math.ceil(posts.value.length / PAGE_SIZE))
const pagedPosts = computed(() => {
  const start = (currentPage.value - 1) * PAGE_SIZE
  return posts.value.slice(start, start + PAGE_SIZE)
})

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

// 兼容鼠标与触摸事件,取纵向坐标
function getClientY(e: MouseEvent | TouchEvent): number {
  return 'touches' in e ? e.touches[0].clientY : e.clientY
}

function onStart(e: MouseEvent | TouchEvent) {
  if (showContent.value) return
  startY = getClientY(e)
  isDragging = true
}

function onEnd(e: MouseEvent | TouchEvent) {
  if (!isDragging) return
  isDragging = false
  const endY = 'changedTouches' in e ? e.changedTouches[0].clientY : e.clientY
  const deltaY = startY - endY
  if (deltaY > 50) {
    handleSlideUp()
  }
}

function onWheel(e: WheelEvent) {
  if (e.deltaY < 0) {
    handleSlideUp()
  }
}

onMounted(() => {
  posts.value = getPosts()
  // 仅当需要上滑进入时（桌面 + 全新加载）才挂载监听
  if (!isMobile.value && !showContent.value) {
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
  padding-bottom: 2rem;
}

/* 博文列表（卡片网格） */
.post-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* 分页栏 */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.4rem;
  margin-top: 1.5rem;
}

.page-btn {
  min-width: 2rem;
  height: 2rem;
  padding: 0 0.6rem;
  border-radius: 0.5rem;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.04);
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.85rem;
  cursor: pointer;
  transition:
    background 0.2s,
    border-color 0.2s,
    color 0.2s;
}

.page-btn:hover:not(:disabled) {
  background: rgba(140, 185, 255, 0.12);
  border-color: rgba(140, 185, 255, 0.35);
  color: rgba(255, 255, 255, 0.95);
}

.page-btn:disabled {
  opacity: 0.3;
  cursor: default;
}

.page-btn-active {
  background: rgba(140, 185, 255, 0.2);
  border-color: rgba(140, 185, 255, 0.5);
  color: rgba(200, 225, 255, 1);
  font-weight: 600;
}

/* 右侧面板 - 桌面端独立滚动 */
@media (min-width: 768px) {
  .sticky-panel {
    position: sticky;
    top: 100px; /* 导航栏高度 + 间距 */
    align-self: flex-start; /* 防止被拉伸 */
  }
}

/* ============================================
   标题上移动画
   ============================================ */
.title-pos {
  top: 42vh;
  transform: translateY(-90%) translateZ(0);
  transition: transform 1.1s cubic-bezier(0.22, 1, 0.36, 1);
  will-change: transform;
}

.title-up {
  transform: translateY(calc(-90% - 160px));
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
  margin-top: 4rem; /* 移动端紧贴顶部（pt-24 已留出导航空间） */
  max-height: 2000px;
  max-width: 96rem; /* 面板区域最大宽度 */
  padding-left: 0.25rem; /* 距屏幕左边 */
  padding-right: 0.25rem; /* 距屏幕右边 */
  transition:
    transform 1.1s cubic-bezier(0.22, 1, 0.36, 1),
    opacity 1.1s cubic-bezier(0.22, 1, 0.36, 1); /* 展开动画：位移+淡入同步 */
  will-change: transform, opacity;
}

/* 桌面端：面板从屏幕中部偏下起始，配合上滑展开动画 */
@media (min-width: 768px) {
  .panels-wrapper {
    margin-top: calc(42vh - 80px);
  }
}

/* 移动端：与归档页起始位置对齐 */
@media (max-width: 767px) {
  .panels-wrapper {
    margin-top: 6rem;
  }
}

.panels-collapsed {
  opacity: 0;
  transform: translateY(60px);
  pointer-events: none;
}

.panels-expanded {
  opacity: 1;
  transform: translateY(0);
}

/* 从站内（如博文页）返回首页时的淡入动画，仅用 opacity 不影响毛玻璃 */
.panels-arrive {
  animation: panelsArrive 0.5s ease both;
}

@keyframes panelsArrive {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@media (prefers-reduced-motion: reduce) {
  .panels-arrive {
    animation: none;
  }
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
