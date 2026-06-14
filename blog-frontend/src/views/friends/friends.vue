<template>
  <PageBackground>
    <div class="relative flex flex-col items-center justify-start pt-24 md:pt-0 w-full">
      <div class="friends-wrapper">
        <GlassPanel class="friends-panel">
          <div class="friends-header">
            <p class="friends-kicker">Friends</p>
            <h1 class="friends-title">友链</h1>
            <p class="friends-desc">一些有趣、温和且持续发光的站点。</p>
          </div>

          <div class="friends-grid">
            <a
              v-for="friend in friends"
              :key="friend.name"
              :href="friend.url"
              class="friend-card"
              target="_blank"
              rel="noopener noreferrer"
            >
              <img :src="friend.avatar" :alt="`${friend.name} avatar`" class="friend-avatar" />
              <div class="friend-info">
                <h2 class="friend-name">{{ friend.name }}</h2>
                <p class="friend-bio">{{ friend.bio }}</p>
              </div>
            </a>
          </div>
        </GlassPanel>
      </div>
    </div>
  </PageBackground>
</template>

<script setup lang="ts">
import PageBackground from '@/components/PageBackground.vue'
import GlassPanel from '@/components/panels/GlassPanel.vue'

/** 友链条目 */
interface Friend {
  name: string // 站点名
  bio: string // 简介
  avatar: string // 头像 URL
  url: string // 站点地址
}

const friends: Friend[] = [
  {
    name: '暮色工坊',
    bio: '记录前端、设计和一些慢慢变好的日常。',
    avatar: 'https://api.dicebear.com/9.x/adventurer/svg?seed=twilight',
    url: 'https://example.com',
  },
  {
    name: '星河手札',
    bio: '关于 Vue、工程化和个人知识库的碎片笔记。',
    avatar: 'https://api.dicebear.com/9.x/adventurer/svg?seed=galaxy',
    url: 'https://vuejs.org',
  },
  {
    name: '北巷代码',
    bio: '偏爱干净代码，也喜欢把复杂问题讲清楚。',
    avatar: 'https://api.dicebear.com/9.x/adventurer/svg?seed=lane',
    url: 'https://vite.dev',
  },
  {
    name: '浮光档案',
    bio: '照片、旅行和那些值得被保存的小瞬间。',
    avatar: 'https://api.dicebear.com/9.x/adventurer/svg?seed=glimmer',
    url: 'https://developer.mozilla.org',
  },
  {
    name: '青柠实验室',
    bio: '折腾工具、自动化和效率系统的个人实验田。',
    avatar: 'https://api.dicebear.com/9.x/adventurer/svg?seed=lime',
    url: 'https://github.com',
  },
  {
    name: '半夏书房',
    bio: '读书、写作和偶尔出现的技术长文。',
    avatar: 'https://api.dicebear.com/9.x/adventurer/svg?seed=summer',
    url: 'https://www.wikipedia.org',
  },
]
</script>

<style scoped>
.friends-wrapper {
  position: relative;
  z-index: 10;
  width: 100%;
  max-width: 72rem;
  margin: 4rem auto 0;
  padding-left: 1rem;
  padding-right: 1rem;
}

.friends-panel {
  min-height: 60vh;
}

.friends-header {
  margin-bottom: 1.6rem;
}

.friends-kicker {
  margin-bottom: 0.25rem;
  color: rgba(160, 205, 255, 0.7);
  font-size: 0.72rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.friends-title {
  color: rgba(255, 255, 255, 0.92);
  font-size: 1.45rem;
  font-weight: 700;
  letter-spacing: 0.06em;
}

.friends-desc {
  margin-top: 0.45rem;
  color: rgba(255, 255, 255, 0.48);
  font-size: 0.86rem;
}

.friends-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1rem;
}

.friend-card {
  position: relative;
  display: flex;
  align-items: center;
  gap: 0.9rem;
  min-height: 7.2rem;
  overflow: hidden;
  border-radius: 1rem;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background:
    radial-gradient(circle at 18% 20%, rgba(140, 185, 255, 0.14), transparent 36%),
    rgba(255, 255, 255, 0.04);
  padding: 1rem;
  text-decoration: none;
  transition:
    transform 0.25s ease,
    border-color 0.25s ease,
    background 0.25s ease,
    box-shadow 0.25s ease;
}

.friend-card::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.08), transparent 45%);
  opacity: 0;
  transition: opacity 0.25s ease;
  pointer-events: none;
}

.friend-card:hover {
  transform: translateY(-3px);
  border-color: rgba(140, 185, 255, 0.3);
  background:
    radial-gradient(circle at 18% 20%, rgba(140, 185, 255, 0.2), transparent 40%),
    rgba(255, 255, 255, 0.06);
  box-shadow: 0 10px 28px rgba(80, 120, 255, 0.14);
}

.friend-card:hover::after {
  opacity: 1;
}

.friend-avatar {
  width: 3.8rem;
  height: 3.8rem;
  flex-shrink: 0;
  border-radius: 1rem;
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(255, 255, 255, 0.08);
  object-fit: cover;
}

.friend-info {
  position: relative;
  z-index: 1;
  min-width: 0;
}

.friend-name {
  margin-bottom: 0.35rem;
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.98rem;
  font-weight: 700;
}

.friend-bio {
  display: -webkit-box;
  overflow: hidden;
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.76rem;
  line-height: 1.55;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

@media (min-width: 768px) {
  .friends-wrapper {
    margin-top: 100px;
  }
}

@media (max-width: 767px) {
  .friends-wrapper {
    /* 移动端顶部导航是 fixed，预留安全间距，避免友链面板压到按钮。 */
    margin-top: 6rem;
  }

  .friends-grid {
    grid-template-columns: 1fr;
  }
}

@media (min-width: 768px) and (max-width: 1023px) {
  .friends-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
