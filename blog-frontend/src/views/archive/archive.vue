<template>
  <PageBackground>
    <div class="relative flex flex-col items-center justify-start pt-24 md:pt-0 w-full">
      <div class="panels-wrapper">
        <div class="panels-container md:flex md:gap-6">
          <!-- 左侧列 -->
          <div
            class="sticky-panel w-full md:w-[22%] flex-shrink-0"
            :class="fromHome ? '' : 'side-rise'"
            style="--rise-delay: 0s"
          >
            <div class="flex flex-col gap-6">
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
          </div>

          <!-- 中间面板 - 时间轴归档 -->
          <div class="w-full md:w-[56%] flex-shrink-0">
            <GlassPanel class="archive-panel">
              <div class="post-rise-inner">
                <h2 class="archive-heading">归档</h2>
                <div class="timeline">
                  <template v-for="group in groups" :key="group.year">
                    <!-- 年份节点 -->
                    <div class="year-node">
                      <div class="year-line-top"></div>
                      <div class="year-badge">{{ group.year }}</div>
                      <div class="year-line-bottom"></div>
                    </div>

                    <!-- 该年文章：左右交替 -->
                    <div
                      v-for="(post, i) in group.posts"
                      :key="post.slug"
                      class="post-row"
                      :class="i % 2 === 0 ? 'post-row-left' : 'post-row-right'"
                    >
                      <RouterLink
                        :to="`/post/${post.slug}`"
                        class="post-card"
                        :class="i % 2 === 0 ? 'card-left' : 'card-invisible'"
                      >
                        <span class="post-date">{{ formatDate(post.date) }}</span>
                        <h3 class="post-title">{{ post.title }}</h3>
                        <p v-if="post.description" class="post-desc">{{ post.description }}</p>
                        <div v-if="post.category" class="post-cat">{{ post.category }}</div>
                      </RouterLink>

                      <div class="axis">
                        <div class="axis-line axis-line-top"></div>
                        <div class="axis-dot"></div>
                        <div class="axis-line axis-line-bottom"></div>
                      </div>

                      <RouterLink
                        :to="`/post/${post.slug}`"
                        class="post-card"
                        :class="i % 2 === 1 ? 'card-right' : 'card-invisible'"
                      >
                        <span class="post-date">{{ formatDate(post.date) }}</span>
                        <h3 class="post-title">{{ post.title }}</h3>
                        <p v-if="post.description" class="post-desc">{{ post.description }}</p>
                        <div v-if="post.category" class="post-cat">{{ post.category }}</div>
                      </RouterLink>
                    </div>
                  </template>

                  <!-- 底部收尾线 -->
                  <div class="timeline-end">
                    <div class="end-line"></div>
                    <div class="end-dot"></div>
                  </div>
                </div>
              </div>
            </GlassPanel>
          </div>

          <!-- 右侧列 -->
          <div
            class="sticky-panel hidden md:block w-full md:w-[22%] flex-shrink-0"
            :class="fromHome ? '' : 'side-rise'"
            style="--rise-delay: 0.05s"
          >
            <div class="flex flex-col gap-6">
              <CalendarPanel flat />
              <PostStatsChart flat />
            </div>
          </div>
        </div>
      </div>
    </div>
  </PageBackground>
</template>

<script setup>
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import PageBackground from '@/components/PageBackground.vue'
import GlassPanel from '@/components/panels/GlassPanel.vue'
import ProfilePanel from '@/components/panels/ProfilePanel.vue'
import PlaceholderPanel from '@/components/panels/PlaceholderPanel.vue'
import CalendarPanel from '@/components/panels/CalendarPanel.vue'
import PostStatsChart from '@/components/panels/PostStatsChart.vue'
import { avatar, profile, socialLinks } from '@/data/profile'
import { getPosts } from '@/data/posts'

const fromHome = !!history.state?.back

const posts = getPosts()

const groups = computed(() => {
  const map = new Map()
  for (const p of posts) {
    if (p.draft) continue
    const year = p.date ? String(p.date).slice(0, 4) : '未知'
    if (!map.has(year)) map.set(year, [])
    map.get(year).push(p)
  }
  return [...map.entries()]
    .sort((a, b) => Number(b[0]) - Number(a[0]))
    .map(([year, posts]) => ({ year, posts }))
})

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  if (isNaN(d)) return dateStr
  return `${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}
</script>

<style scoped>
.panels-wrapper {
  position: relative;
  z-index: 10;
  width: 100%;
  margin-left: auto;
  margin-right: auto;
  margin-top: 4rem;
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

/* ===== 进入动画（与 post 页一致） ===== */
.post-rise-inner {
  animation: contentRise 0.6s cubic-bezier(0.22, 1, 0.36, 1) both;
  animation-delay: 0.15s;
}

.side-rise {
  animation: contentRise 0.55s cubic-bezier(0.22, 1, 0.36, 1) both;
  animation-delay: var(--rise-delay, 0s);
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

.archive-heading {
  font-size: 1.1rem;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.85);
  margin-bottom: 2rem;
  letter-spacing: 0.05em;
}

.timeline {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  padding-bottom: 1rem;
}

.year-node {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.year-line-top {
  width: 2px;
  height: 1.5rem;
  background: linear-gradient(to bottom, transparent, rgba(140, 185, 255, 0.4));
}

.year-badge {
  padding: 0.25rem 1.25rem;
  border-radius: 999px;
  background: rgba(120, 170, 255, 0.18);
  border: 1px solid rgba(140, 185, 255, 0.35);
  color: rgba(180, 215, 255, 0.95);
  font-size: 0.9rem;
  font-weight: 700;
  letter-spacing: 0.12em;
}

.year-line-bottom {
  width: 2px;
  height: 1.5rem;
  background: rgba(140, 185, 255, 0.35);
}

.post-row {
  display: grid;
  grid-template-columns: 1fr 2rem 1fr;
  align-items: stretch;
}

.axis {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
}

.axis-line {
  flex: 1;
  width: 2px;
  background: rgba(140, 185, 255, 0.35);
}

.axis-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: rgba(160, 200, 255, 0.9);
  border: 2px solid rgba(80, 120, 200, 0.6);
  box-shadow: 0 0 8px rgba(140, 185, 255, 0.5);
  flex-shrink: 0;
  margin: 0.25rem 0;
}

.post-card {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  padding: 0.75rem 1rem;
  margin: 0.4rem 0.5rem;
  border-radius: 0.75rem;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  text-decoration: none;
  transition:
    background 0.25s ease,
    border-color 0.25s ease,
    transform 0.25s ease,
    box-shadow 0.25s ease;
}

.post-card:hover {
  background: rgba(140, 185, 255, 0.1);
  border-color: rgba(140, 185, 255, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(80, 120, 255, 0.15);
}

.card-invisible {
  visibility: hidden;
  pointer-events: none;
}

.card-left {
  text-align: right;
}

.card-right {
  text-align: left;
}

.post-date {
  font-size: 0.82rem;
  color: rgba(160, 200, 255, 0.9);
  font-variant-numeric: tabular-nums;
}

.post-title {
  font-size: 1rem;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
  line-height: 1.4;
  margin: 0;
}

.post-desc {
  font-size: 0.82rem;
  color: rgba(255, 255, 255, 0.6);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin: 0;
}

.post-cat {
  font-size: 0.72rem;
  color: rgba(160, 205, 255, 0.85);
  padding: 0.15rem 0.6rem;
  border-radius: 999px;
  background: rgba(140, 185, 255, 0.14);
  border: 1px solid rgba(140, 185, 255, 0.28);
  display: inline-block;
  align-self: flex-end;
}

.card-left .post-cat {
  align-self: flex-start;
}

.timeline-end {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.end-line {
  width: 2px;
  height: 1.5rem;
  background: linear-gradient(to bottom, rgba(140, 185, 255, 0.35), transparent);
}

.end-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: rgba(140, 185, 255, 0.4);
}

@media (max-width: 767px) {
  .post-row {
    grid-template-columns: 0 2rem 1fr;
  }
  .card-invisible {
    display: none;
  }
  .post-row-left .card-left {
    display: none;
  }
  .post-row-right .card-right,
  .post-row-left .card-invisible {
    display: flex;
    visibility: visible;
    pointer-events: auto;
  }
}
</style>
