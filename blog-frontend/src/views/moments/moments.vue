<template>
  <PageBackground>
    <div class="relative flex flex-col items-center justify-start pt-24 md:pt-0 w-full">
      <div class="moments-wrapper">
        <GlassPanel class="moments-panel">
          <div class="moments-header">
            <p class="moments-kicker">Moments</p>
            <h1 class="moments-title">说说</h1>
            <p class="moments-desc">一些碎碎念，和偶然闪过的灵感。</p>
          </div>

          <div v-if="moments.length === 0" class="moments-empty">
            还没有说过什么…
          </div>

          <div v-else class="moments-list">
            <article
              v-for="moment in moments"
              :key="moment.id"
              class="moment-card"
            >
              <div class="moment-head">
                <span class="moment-date">{{ moment.date }}</span>
                <span v-if="moment.tags.length" class="moment-tags">
                  <span v-for="tag in moment.tags" :key="tag" class="moment-tag">#{{ tag }}</span>
                </span>
              </div>
              <p class="moment-content">{{ moment.content }}</p>
              <div v-if="moment.images.length" class="moment-images">
                <img
                  v-for="(img, i) in moment.images"
                  :key="i"
                  :src="img"
                  :alt="`image ${i + 1}`"
                  class="moment-image"
                  loading="lazy"
                />
              </div>
            </article>
          </div>
        </GlassPanel>
      </div>
    </div>
  </PageBackground>
</template>

<script setup lang="ts">
import PageBackground from '@/components/PageBackground.vue'
import GlassPanel from '@/components/panels/GlassPanel.vue'

/** 一条说说/碎碎念 */
interface Moment {
  id: number
  date: string
  content: string
  tags: string[]
  images: string[]
}

const moments: Moment[] = [
  {
    id: 1,
    date: '2026-07-10',
    content: '阳光透过云层洒在桌上的那一刻，突然觉得代码也变得温柔了。',
    tags: ['日常'],
    images: [],
  },
  {
    id: 2,
    date: '2026-07-08',
    content: '在 Vue 里把一个 UI 拆成小组件的时候，就像在搭积木一样有成就感。',
    tags: ['前端', 'vue'],
    images: [],
  },
  {
    id: 3,
    date: '2026-07-05',
    content: '晚上路过河边，看见有人在桥下弹吉他，声音飘在水面上，像另一种波光粼粼。',
    tags: ['生活', '夜晚'],
    images: [],
  },
  {
    id: 4,
    date: '2026-07-01',
    content: '终于把博客的归档树做好了，看着那些树枝上挂着文章卡片的样子，七月快乐。',
    tags: ['博客', '开发'],
    images: [],
  },
]
</script>

<style scoped>
.moments-wrapper {
  position: relative;
  z-index: 10;
  width: 100%;
  max-width: 42rem;
  margin: 4rem auto 0;
  padding-left: 1rem;
  padding-right: 1rem;
}

.moments-panel {
  min-height: 60vh;
}

.moments-header {
  margin-bottom: 1.6rem;
}

.moments-kicker {
  margin-bottom: 0.25rem;
  color: rgba(160, 205, 255, 0.7);
  font-size: 0.72rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.moments-title {
  color: rgba(255, 255, 255, 0.92);
  font-size: 1.45rem;
  font-weight: 700;
  letter-spacing: 0.06em;
}

.moments-desc {
  margin-top: 0.45rem;
  color: rgba(255, 255, 255, 0.48);
  font-size: 0.86rem;
}

.moments-empty {
  padding: 3rem 0;
  text-align: center;
  color: rgba(255, 255, 255, 0.35);
  font-size: 0.9rem;
}

.moments-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.moment-card {
  position: relative;
  padding: 1.25rem 1.5rem;
  border-radius: 1rem;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.04);
  transition:
    border-color 0.25s ease,
    background 0.25s ease,
    box-shadow 0.25s ease;
}

.moment-card:hover {
  border-color: rgba(140, 185, 255, 0.25);
  background: rgba(255, 255, 255, 0.06);
  box-shadow: 0 8px 24px rgba(80, 120, 255, 0.1);
}

.moment-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.6rem;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.moment-date {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.4);
}

.moment-tags {
  display: flex;
  gap: 0.35rem;
  flex-wrap: wrap;
}

.moment-tag {
  font-size: 0.68rem;
  color: rgba(140, 205, 255, 0.6);
}

.moment-content {
  color: rgba(255, 255, 255, 0.82);
  font-size: 0.95rem;
  line-height: 1.8;
  margin: 0;
}

.moment-images {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.75rem;
  flex-wrap: wrap;
}

.moment-image {
  width: 6rem;
  height: 6rem;
  border-radius: 0.6rem;
  object-fit: cover;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

@media (min-width: 768px) {
  .moments-wrapper {
    margin-top: 100px;
  }
}

@media (max-width: 767px) {
  .moments-wrapper {
    margin-top: 6rem;
  }
}
</style>
