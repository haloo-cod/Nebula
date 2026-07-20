<template>
  <PageBackground>
    <main class="friends-page">
      <!-- 页面标题 -->
      <header class="friends-header">
        <p class="friends-kicker">{{ siteText.friends.kicker }}</p>
        <h1 class="friends-title">{{ siteText.friends.title }}</h1>
        <p class="friends-desc">{{ siteText.friends.subtitle }}</p>
      </header>

      <!-- 顶部液态玻璃鱼缸 -->
      <section class="aquarium-section" aria-label="友链头像墙">
        <LiquidGlass
          class="friends-aquarium"
          :theme="ui.theme"
          :corner-radius="24"
          :ripple-trail="true"
        >
          <div ref="aquariumRef" class="aquarium-content">
            <a
              v-for="item in floatingItems"
              :key="item.name"
              :href="item.url"
              target="_blank"
              rel="noopener noreferrer"
              class="floating-avatar"
              :style="item.style"
              @mouseenter="pause(item.name)"
              @mouseleave="resume(item.name)"
              @focus="pause(item.name)"
              @blur="resume(item.name)"
            >
              <img
                :src="item.avatar"
                :alt="`${item.name} avatar`"
                class="floating-avatar__img"
                loading="lazy"
              />
              <span class="floating-avatar__name">{{ item.name }}</span>
            </a>
          </div>
        </LiquidGlass>
      </section>

      <!-- 下方友链列表 -->
      <section class="friends-list-section" aria-label="友链列表">
        <div class="friends-grid">
          <a
            v-for="friend in friends"
            :key="friend.name"
            :href="friend.url"
            target="_blank"
            rel="noopener noreferrer"
            class="friend-link"
          >
            <LiquidGlass
              v-if="ui.liquidGlassEnabled"
              class="friend-card-glass"
              :theme="ui.theme"
              :corner-radius="16"
              :ripple-trail="true"
            >
              <article class="friend-card friend-card--liquid">
                <img
                  :src="friend.avatar"
                  :alt="`${friend.name} avatar`"
                  class="friend-avatar"
                  loading="lazy"
                />
                <div class="friend-info">
                  <h2 class="friend-name">{{ friend.name }}</h2>
                  <p class="friend-bio">{{ friend.bio }}</p>
                </div>
                <SvgIcon name="arrow_forward_ios" class="friend-external" />
              </article>
            </LiquidGlass>

            <PanelFallbackGlass v-else tag="article" class="friend-card friend-card-fallback">
              <img
                :src="friend.avatar"
                :alt="`${friend.name} avatar`"
                class="friend-avatar"
                loading="lazy"
              />
              <div class="friend-info">
                <h2 class="friend-name">{{ friend.name }}</h2>
                <p class="friend-bio">{{ friend.bio }}</p>
              </div>
              <SvgIcon name="arrow_forward_ios" class="friend-external" />
            </PanelFallbackGlass>
          </a>
        </div>
      </section>

      <!-- 交换友链 -->
      <section class="friends-exchange-section" aria-label="交换友链">
        <LiquidGlass
          v-if="ui.liquidGlassEnabled"
          class="exchange-glass"
          :theme="ui.theme"
          :corner-radius="16"
          :ripple-trail="true"
        >
          <article class="exchange-card exchange-card--liquid">
            <h2 class="exchange-title">交换友链</h2>

            <div class="exchange-site">
              <img
                :src="exchangeInfo.avatar"
                :alt="`${exchangeInfo.name} avatar`"
                class="exchange-avatar"
                loading="lazy"
              />
              <div class="exchange-site-info">
                <h3 class="exchange-site-name">{{ exchangeInfo.name }}</h3>
                <p class="exchange-site-url">{{ exchangeInfo.url }}</p>
                <p class="exchange-site-bio">{{ exchangeInfo.bio }}</p>
              </div>
            </div>

            <div class="exchange-block">
              <h3 class="exchange-block-title">申请要求</h3>
              <ul class="exchange-list">
                <li v-for="(req, index) in exchangeInfo.requirements" :key="index">
                  {{ req }}
                </li>
              </ul>
            </div>

            <div class="exchange-block">
              <h3 class="exchange-block-title">联系方式</h3>
              <p class="exchange-contact">{{ exchangeInfo.contact }}</p>
            </div>
          </article>
        </LiquidGlass>

        <PanelFallbackGlass v-else tag="article" class="exchange-card exchange-card-fallback">
          <h2 class="exchange-title">交换友链</h2>

          <div class="exchange-site">
            <img
              :src="exchangeInfo.avatar"
              :alt="`${exchangeInfo.name} avatar`"
              class="exchange-avatar"
              loading="lazy"
            />
            <div class="exchange-site-info">
              <h3 class="exchange-site-name">{{ exchangeInfo.name }}</h3>
              <p class="exchange-site-url">{{ exchangeInfo.url }}</p>
              <p class="exchange-site-bio">{{ exchangeInfo.bio }}</p>
            </div>
          </div>

          <div class="exchange-block">
            <h3 class="exchange-block-title">申请要求</h3>
            <ul class="exchange-list">
              <li v-for="(req, index) in exchangeInfo.requirements" :key="index">
                {{ req }}
              </li>
            </ul>
          </div>

          <div class="exchange-block">
            <h3 class="exchange-block-title">联系方式</h3>
            <p class="exchange-contact">{{ exchangeInfo.contact }}</p>
          </div>
        </PanelFallbackGlass>
      </section>
    </main>
  </PageBackground>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import PageBackground from '@/components/PageBackground.vue'
import LiquidGlass from '@/components/liquid-glass/LiquidGlass.vue'
import PanelFallbackGlass from '@/components/panels/PanelFallbackGlass.vue'
import SvgIcon from '@/components/SvgIcon.vue'
import { getFriends } from '@/data/friends'
import { fetchFriends, fetchFriendExchangeInfo, type FriendExchangeInfo } from '@/api/friends'
import { siteText } from '@/data/site-text'
import { useUIStore } from '@/stores/ui'
import { useFloatingAvatars } from '@/composables/useFloatingAvatars'

const ui = useUIStore()
const friends = ref(getFriends())
const aquariumRef = ref<HTMLElement | null>(null)

// 交换友链占位信息，后续替换为真实内容
const exchangeInfo = ref<FriendExchangeInfo>({
  name: '你的站点名称',
  url: 'https://example.com',
  avatar: 'https://api.dicebear.com/9.x/adventurer/svg?seed=myblog',
  bio: '这里填写你的站点简介。',
  requirements: ['原创内容优先', '站点稳定可访问', '无违法违规内容', '最好有定期更新'],
  contact: 'your-email@example.com',
})

const {
  items: floatingItems,
  pause,
  resume,
} = useFloatingAvatars({
  containerRef: aquariumRef,
  friends,
  mode: 'bounce',
  avatarSize: 72,
  speed: 0.8,
})

// 尝试从后端 API 加载友链列表
onMounted(async () => {
  try {
    const [apiFriends, apiExchangeInfo] = await Promise.all([
      fetchFriends(),
      fetchFriendExchangeInfo(),
    ])
    if (apiFriends.length > 0) {
      friends.value = apiFriends
    }
    exchangeInfo.value = apiExchangeInfo
  } catch {
    // API 失败，保留本地 fallback 数据
  }
})
</script>

<style scoped>
.friends-page {
  position: relative;
  z-index: 10;
  width: 100%;
  max-width: 72rem;
  margin: 0 auto;
  padding: 7rem 1rem 5rem;
}

/* ============ 液态玻璃鱼缸 ============ */
.aquarium-section {
  width: 100%;
  height: 55vh;
  min-height: 320px;
  margin-bottom: 4rem;
}

.friends-aquarium {
  width: 100%;
  height: 100%;
}

.aquarium-content {
  position: relative;
  width: 100%;
  height: 100%;
}

.floating-avatar {
  position: absolute;
  top: 0;
  left: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  text-decoration: none;
  will-change: transform;
  transition:
    transform 0.2s ease,
    filter 0.2s ease;
}

.floating-avatar:hover,
.floating-avatar:focus-visible {
  z-index: 10;
  filter: brightness(1.15);
}

.floating-avatar__img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.18);
  background: var(--glass-bg);
  object-fit: cover;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
  transition:
    transform 0.25s ease,
    box-shadow 0.25s ease;
}

.floating-avatar:hover .floating-avatar__img,
.floating-avatar:focus-visible .floating-avatar__img {
  transform: scale(1.12);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.35);
}

.floating-avatar__name {
  position: absolute;
  bottom: -1.75rem;
  left: 50%;
  transform: translateX(-50%);
  padding: 0.25rem 0.625rem;
  border-radius: 0.5rem;
  background: var(--glass-bg-strong);
  border: 1px solid var(--glass-border-subtle);
  color: var(--text-primary);
  font-size: 0.75rem;
  font-weight: 700;
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transition:
    opacity 0.2s ease,
    transform 0.2s ease;
}

.floating-avatar:hover .floating-avatar__name,
.floating-avatar:focus-visible .floating-avatar__name {
  opacity: 1;
  transform: translateX(-50%) translateY(-0.25rem);
}

/* ============ 列表区 ============ */
.friends-list-section {
  padding-top: 1rem;
}

.friends-header {
  margin-bottom: 1.5rem;
}

.friends-kicker {
  margin-bottom: 0.25rem;
  color: rgba(160, 205, 255, 0.7);
  font-size: 0.72rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

[data-theme='light'] .friends-kicker {
  color: rgba(14, 116, 110, 0.74);
}

.friends-title {
  color: var(--text-primary);
  font-size: 1.45rem;
  font-weight: 700;
  letter-spacing: 0.06em;
}

.friends-desc {
  margin-top: 0.45rem;
  color: var(--text-secondary);
  font-size: 0.86rem;
}

.friends-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1rem;
}

.friend-link {
  display: block;
  text-decoration: none;
}

.friend-card-glass {
  display: block;
  width: 100%;
  height: 100%;
}

.friend-card {
  position: relative;
  display: flex;
  align-items: center;
  gap: 0.9rem;
  min-height: 7.2rem;
  padding: 1rem;
  transition: transform 0.25s ease;
}

.friend-card--liquid {
  width: 100%;
  height: 100%;
}

.friend-card-fallback {
  overflow: hidden;
  border-radius: 1rem;
  border: 1px solid var(--glass-border-subtle);
  background: var(--glass-bg);
}

.friend-link:hover .friend-card {
  transform: translateY(-3px);
}

.friend-avatar {
  width: 3.8rem;
  height: 3.8rem;
  flex-shrink: 0;
  border-radius: 1rem;
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: var(--glass-bg-subtle);
  object-fit: cover;
}

.friend-info {
  position: relative;
  z-index: 1;
  min-width: 0;
  flex: 1;
}

.friend-name {
  margin-bottom: 0.35rem;
  color: var(--text-primary);
  font-size: 0.98rem;
  font-weight: 700;
}

.friend-bio {
  display: -webkit-box;
  overflow: hidden;
  color: var(--text-secondary);
  font-size: 0.76rem;
  line-height: 1.55;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.friend-external {
  width: 1.1rem;
  height: 1.1rem;
  flex-shrink: 0;
  color: var(--text-muted);
  transition: color 0.2s ease;
}

.friend-link:hover .friend-external {
  color: rgba(140, 218, 214, 0.95);
}

[data-theme='light'] .friend-link:hover .friend-external {
  color: rgba(14, 116, 110, 0.95);
}

/* ============ 交换友链 ============ */
.friends-exchange-section {
  margin-top: 4rem;
}

.exchange-glass {
  display: block;
  width: 100%;
}

.exchange-card {
  padding: 1.5rem;
}

.exchange-card--liquid {
  width: 100%;
  height: 100%;
}

.exchange-card-fallback {
  overflow: hidden;
  border-radius: 1rem;
  border: 1px solid var(--glass-border-subtle);
  background: var(--glass-bg);
}

.exchange-title {
  margin-bottom: 1.25rem;
  color: var(--text-primary);
  font-size: 1.15rem;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.exchange-site {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.25rem;
  padding-bottom: 1.25rem;
  border-bottom: 1px solid var(--glass-border-subtle);
}

.exchange-avatar {
  width: 4rem;
  height: 4rem;
  flex-shrink: 0;
  border-radius: 1rem;
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: var(--glass-bg-subtle);
  object-fit: cover;
}

.exchange-site-name {
  color: var(--text-primary);
  font-size: 1rem;
  font-weight: 700;
}

.exchange-site-url {
  margin-top: 0.2rem;
  color: rgba(140, 218, 214, 0.85);
  font-size: 0.8rem;
}

[data-theme='light'] .exchange-site-url {
  color: rgba(14, 116, 110, 0.85);
}

.exchange-site-bio {
  margin-top: 0.35rem;
  color: var(--text-secondary);
  font-size: 0.8rem;
  line-height: 1.55;
}

.exchange-block {
  margin-bottom: 1rem;
}

.exchange-block:last-child {
  margin-bottom: 0;
}

.exchange-block-title {
  margin-bottom: 0.5rem;
  color: var(--text-primary);
  font-size: 0.9rem;
  font-weight: 700;
}

.exchange-list {
  padding-left: 1.25rem;
  color: var(--text-secondary);
  font-size: 0.82rem;
  line-height: 1.7;
}

.exchange-contact {
  color: var(--text-secondary);
  font-size: 0.82rem;
}

@media (max-width: 767px) {
  .friends-page {
    padding-top: 6rem;
  }

  .aquarium-section {
    height: 45vh;
    min-height: 280px;
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
