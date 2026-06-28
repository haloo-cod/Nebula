<template>
  <PageBackground>
    <div class="relative flex flex-col items-center justify-start pt-24 md:pt-0 w-full">
      <div class="panels-wrapper">
        <div class="panels-inner flex flex-col md:flex-row gap-6 items-start">
          <!-- 左侧列 -->
          <div class="sticky-panel hidden md:flex w-full md:w-[22%] flex-shrink-0 flex-col gap-6">
            <ProfilePanel
              :avatar="avatar"
              :name="profile.name"
              :bio="profile.bio"
              :links="socialLinks"
              square
              flat
            />
            <PlaceholderPanel class="hidden md:flex" flat />
          </div>

          <!-- 中间面板：玻璃本身静止，内部内容滑入 -->
          <div class="w-full md:w-[56%] flex-shrink-0">
            <GlassPanel class="panel-right">
              <div class="post-rise-inner">
                <div class="post-header">
                  <button class="back-btn" @click="goBack" aria-label="返回首页">
                    <span class="back-arrow">◀</span>
                    <span>返回</span>
                  </button>
                </div>
                <div v-if="loading" class="text-white/50 mt-8">加载中...</div>
                <div v-else-if="html" class="prose" v-html="html"></div>
                <div v-else class="text-white/50 mt-8">文章不存在</div>
              </div>
            </GlassPanel>
          </div>

          <!-- 右侧列 -->
          <div class="sticky-panel hidden md:flex w-full md:w-[22%] flex-shrink-0 flex-col gap-6">
            <CalendarPanel flat />
            <PostStatsChart flat />
          </div>
        </div>
      </div>
    </div>
  </PageBackground>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import PageBackground from '@/components/PageBackground.vue'
import GlassPanel from '@/components/panels/GlassPanel.vue'
import ProfilePanel from '@/components/panels/ProfilePanel.vue'
import PlaceholderPanel from '@/components/panels/PlaceholderPanel.vue'
import CalendarPanel from '@/components/panels/CalendarPanel.vue'
import PostStatsChart from '@/components/panels/PostStatsChart.vue'
import { avatar, profile, socialLinks } from '@/data/profile'
import { getPost, renderPost } from '@/data/posts'

const route = useRoute()
const router = useRouter()
const html = ref('')
const loading = ref(true)

// 从首页已下滑状态跳来 → 侧边栏已在位，只动中间内容
async function load(slug: string) {
  loading.value = true
  if (!getPost(slug)) {
    html.value = ''
    loading.value = false
    return
  }
  html.value = (await renderPost(slug)) || ''
  loading.value = false
}

// 路由参数可能是字符串或数组,统一取字符串
load(String(route.params.slug))
watch(
  () => route.params.slug,
  (slug) => {
    if (slug) load(String(slug))
  },
)

function goBack() {
  // 按来源返回:/archive/post/* 回归档页,其余回首页(并恢复首页已展开状态)
  if (route.path.startsWith('/archive/')) {
    router.push({ path: '/archive' })
  } else {
    router.push({ path: '/', state: { showContent: true, skipLiquidGlassReveal: true } })
  }
}
</script>

<style scoped>
.panels-wrapper {
  position: relative;
  z-index: 10;
  width: 100%;
  margin-left: auto;
  margin-right: auto;
  margin-top: 0;
  max-width: 96rem;
  padding-left: 0.25rem;
  padding-right: 0.25rem;
}

@media (min-width: 768px) {
  .panels-wrapper {
    margin-top: 100px;
  }
  .sticky-panel {
    position: sticky;
    top: 100px;
    align-self: flex-start;
  }
}

@media (max-width: 767px) {
  .panels-wrapper {
    /* 移动端顶部导航是 fixed，预留与归档页一致的安全间距，避免文章面板压到按钮。 */
    margin-top: 6rem;
  }
}

.panels-inner {
  padding-bottom: 1rem;
}

/* 中间内容滑入，无延迟避免空玻璃闪烁 */
.post-rise-inner {
  animation: contentRise 0.55s cubic-bezier(0.22, 1, 0.36, 1) both;
}

@keyframes contentRise {
  from {
    opacity: 0;
    transform: translateY(40px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (prefers-reduced-motion: reduce) {
  .post-rise-inner,
  .side-rise {
    animation: none;
  }
}

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

.post-header {
  display: flex;
  align-items: flex-start;
  justify-content: flex-end;
  margin-bottom: 1.5rem;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 8px 18px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.06);
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
}

.prose {
  color: rgba(255, 255, 255, 0.8);
  line-height: 1.8;
  font-size: 1rem;
}
.prose :deep(h1) {
  font-size: 1.85rem;
  font-weight: 700;
  color: #fff;
  line-height: 1.3;
  margin: 0 0 1rem;
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

@media (max-width: 767px) {
  .panel-right {
    max-height: none;
    overflow-y: visible;
  }
}
</style>
