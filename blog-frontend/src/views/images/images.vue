<template>
    <main class="gallery-images-page">
      <!-- 概览:相册网格 -->
      <template v-if="!currentAlbum">
        <RouterLink to="/" class="back-link">返回首页</RouterLink>

        <section class="section-heading">
          <span class="gallery-kicker">{{ siteText.images.kicker }}</span>
          <h1>{{ siteText.images.title }}</h1>
          <p>{{ siteText.images.subtitle }}</p>
        </section>

        <div class="album-grid">
          <AlbumCard v-for="album in albums" :key="album.id" :album="album" @open="openAlbum" />
        </div>
      </template>

      <!-- 相册详情:瀑布流 -->
      <template v-else>
        <section class="album-detail">
          <div class="album-detail__header">
            <div class="album-detail__meta">
              <div class="album-detail__nav">
                <button class="album-detail__back" @click="closeAlbum">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2.5"
                      d="M10 19l-7-7m0 0l7-7m-7 7h18"
                    />
                  </svg>
                  返回画廊
                </button>
                <span class="album-detail__dot"></span>
                <span class="album-detail__date">{{ currentAlbum.date }}</span>
              </div>
              <h1>{{ currentAlbum.title }}</h1>
              <p>{{ currentAlbum.description }}</p>
            </div>
            <div class="album-detail__count">
              共 <strong>{{ currentAlbum.photos.length }}</strong> 瞬间
            </div>
          </div>

          <div class="photo-masonry">
            <figure
              v-for="(photo, index) in currentAlbum.photos"
              :key="`${photo.url}-${index}`"
              class="photo-item"
              :style="{ animationDelay: `${index * 50}ms` }"
              @click="openLightbox(index)"
            >
              <img :src="photo.url" :alt="photo.caption || '照片'" loading="lazy" />
              <figcaption v-if="photo.caption" class="photo-item__caption">
                {{ photo.caption }}
              </figcaption>
            </figure>
          </div>
        </section>
      </template>
    </main>

    <!-- 灯箱:全屏查看,支持左右切换(Teleport 到 body 避免祖先 transform 影响 fixed 定位) -->
    <Teleport to="body">
      <div v-if="currentPhoto" class="lightbox" @click="closeLightbox">
        <button class="lightbox__close" aria-label="关闭" @click="closeLightbox">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>

        <button
          v-if="currentAlbum && currentAlbum.photos.length > 1"
          class="lightbox__arrow lightbox__arrow--prev"
          aria-label="上一张"
          @click.stop="prevPhoto"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2.5"
              d="M15 19l-7-7 7-7"
            />
          </svg>
        </button>

        <img
          class="lightbox__img"
          :src="currentPhoto.url"
          :alt="currentPhoto.caption || '全屏照片'"
          @click.stop
        />

        <button
          v-if="currentAlbum && currentAlbum.photos.length > 1"
          class="lightbox__arrow lightbox__arrow--next"
          aria-label="下一张"
          @click.stop="nextPhoto"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2.5"
              d="M9 5l7 7-7 7"
            />
          </svg>
        </button>

        <div v-if="currentPhoto.caption" class="lightbox__caption">{{ currentPhoto.caption }}</div>
      </div>
    </Teleport>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import AlbumCard from './AlbumCard.vue'
import { fetchAlbums, fetchAlbumDetail } from '@/api/albums'
import { siteText } from '@/data/site-text'
import type { Album } from '@/types'

const albums = ref<Album[]>([])

// ============ 相册详情状态(页内切换,不进路由) ============

const currentAlbum = ref<Album | null>(null)

async function openAlbum(album: Album) {
  currentAlbum.value = album
  window.scrollTo({ top: 0 })

  // 尝试从 API 获取完整照片列表（列表接口 photos 为空）
  try {
    const detail = await fetchAlbumDetail(Number(album.id))
    if (detail.photos.length > 0) {
      currentAlbum.value = detail
    }
  } catch {
    // API 失败时保持当前数据
  }
}

function closeAlbum() {
  currentAlbum.value = null
  closeLightbox()
  window.scrollTo({ top: 0 })
}

// ============ 灯箱逻辑 ============

/** 当前灯箱照片索引,null 表示灯箱关闭 */
const lightboxIndex = ref<number | null>(null)

/** 灯箱当前展示的照片 */
const currentPhoto = computed(() => {
  if (lightboxIndex.value === null || !currentAlbum.value) return null
  return currentAlbum.value.photos[lightboxIndex.value] || null
})

function openLightbox(index: number) {
  lightboxIndex.value = index
}

function closeLightbox() {
  lightboxIndex.value = null
}

function prevPhoto() {
  if (lightboxIndex.value === null || !currentAlbum.value) return
  const len = currentAlbum.value.photos.length
  lightboxIndex.value = (lightboxIndex.value - 1 + len) % len
}

function nextPhoto() {
  if (lightboxIndex.value === null || !currentAlbum.value) return
  const len = currentAlbum.value.photos.length
  lightboxIndex.value = (lightboxIndex.value + 1) % len
}

function handleKeydown(e: KeyboardEvent) {
  if (lightboxIndex.value === null) return
  if (e.key === 'Escape') closeLightbox()
  if (e.key === 'ArrowLeft') prevPhoto()
  if (e.key === 'ArrowRight') nextPhoto()
}

onMounted(async () => {
  document.addEventListener('keydown', handleKeydown)

  // 尝试从后端 API 获取相册列表
  try {
    const apiAlbums = await fetchAlbums()
    albums.value = apiAlbums
  } catch {
    // API 失败时保持空状态
  }
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.gallery-images-page {
  position: relative;
  z-index: 10;
  width: min(100%, 76rem);
  margin: 0 auto;
  padding: 7rem 1rem 5rem;
}

.back-link {
  color: rgba(250, 221, 166, 0.82);
  font-size: 0.86rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-decoration: none;
}

[data-theme='light'] .back-link {
  color: rgba(180, 130, 40, 0.9);
}

.gallery-kicker {
  display: block;
  margin-top: 1.5rem;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: rgba(140, 218, 214, 0.74);
}

[data-theme='light'] .gallery-kicker {
  color: rgba(14, 116, 110, 0.74);
}

.section-heading h1 {
  margin-top: 0.75rem;
  font-size: clamp(2.5rem, 7vw, 5rem);
  line-height: 1;
  font-weight: 850;
  letter-spacing: -0.06em;
  color: var(--text-primary);
}

.section-heading p {
  margin-top: 1rem;
  color: var(--text-secondary);
}

/* ============ 相册网格(大行距给扇出留空间) ============ */
.album-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  column-gap: 2rem;
  row-gap: 5rem;
  margin-top: 2.5rem;
}

/* ============ 相册详情 ============ */
.album-detail {
  animation: fade-in-up 0.6s cubic-bezier(0.16, 1, 0.3, 1) both;
}

.album-detail__header {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding-bottom: 1.5rem;
  margin-bottom: 3rem;
  border-bottom: 1px solid var(--glass-border-subtle);
}

.album-detail__nav {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.album-detail__back {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0;
  border: none;
  background: none;
  color: var(--text-secondary);
  font-size: 0.875rem;
  font-weight: 700;
  cursor: pointer;
  transition: color 0.3s ease;
}

.album-detail__back svg {
  width: 1rem;
  height: 1rem;
  padding: 0.375rem;
  border-radius: 0.5rem;
  background: var(--glass-bg);
  border: 1px solid var(--glass-border-subtle);
  box-sizing: content-box;
}

.album-detail__back:hover {
  color: var(--text-primary);
}

.album-detail__dot {
  width: 0.375rem;
  height: 0.375rem;
  border-radius: 50%;
  background: var(--text-faint);
}

.album-detail__date {
  font-size: 0.75rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.album-detail__meta h1 {
  font-size: clamp(2rem, 5vw, 3rem);
  line-height: 1.1;
  font-weight: 850;
  letter-spacing: -0.04em;
  color: var(--text-primary);
}

.album-detail__meta p {
  margin-top: 0.5rem;
  font-size: 1rem;
  color: var(--text-secondary);
}

.album-detail__count {
  align-self: flex-start;
  padding: 0.625rem 1.25rem;
  border-radius: 1rem;
  background: var(--glass-bg);
  border: 1px solid var(--glass-border-subtle);
  color: var(--text-secondary);
  font-size: 0.875rem;
  font-weight: 700;
  white-space: nowrap;
}

.album-detail__count strong {
  color: rgba(140, 218, 214, 0.95);
  font-size: 1.125rem;
}

[data-theme='light'] .album-detail__count strong {
  color: rgba(14, 116, 110, 0.95);
}

/* ============ 瀑布流(CSS columns + 交错入场) ============ */
.photo-masonry {
  columns: 1;
  column-gap: 1.5rem;
}

.photo-item {
  position: relative;
  margin: 0 0 1.5rem;
  break-inside: avoid;
  border-radius: 1rem;
  overflow: hidden;
  cursor: zoom-in;
  box-shadow: 0 10px 30px rgba(3, 12, 22, 0.35);
  animation: fade-in-up 0.6s cubic-bezier(0.16, 1, 0.3, 1) both;
  transition:
    transform 0.5s ease,
    box-shadow 0.5s ease;
}

.photo-item:hover {
  transform: scale(1.02);
  box-shadow: 0 20px 45px rgba(3, 12, 22, 0.45);
}

.photo-item img {
  display: block;
  width: 100%;
  height: auto;
  transition: transform 0.7s ease;
}

.photo-item:hover img {
  transform: scale(1.05);
}

/* 悬停时说明文字从底部滑入 */
.photo-item__caption {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  padding: 1.25rem;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.8), rgba(0, 0, 0, 0.1), transparent);
  color: #fff;
  font-size: 0.875rem;
  font-weight: 500;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
  opacity: 0;
  transition: opacity 0.5s ease;
}

.photo-item:hover .photo-item__caption {
  opacity: 1;
}

/* ============ 灯箱 ============ */
.lightbox {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  background: rgba(0, 0, 0, 0.95);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  cursor: zoom-out;
  animation: fade-in 0.4s ease-out both;
}

.lightbox__img {
  max-width: 100%;
  max-height: 85vh;
  object-fit: contain;
  border-radius: 0.5rem;
  box-shadow: 0 25px 60px rgba(0, 0, 0, 0.6);
  cursor: default;
}

.lightbox__close {
  position: absolute;
  top: 1.5rem;
  right: 1.5rem;
  padding: 0.5rem;
  border: none;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.5);
  cursor: pointer;
  transition:
    color 0.3s ease,
    background 0.3s ease;
}

.lightbox__close:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.2);
}

.lightbox__close svg {
  display: block;
  width: 1.5rem;
  height: 1.5rem;
}

.lightbox__arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  padding: 0.5rem;
  border: none;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.6);
  cursor: pointer;
  transition:
    color 0.3s ease,
    background 0.3s ease;
}

.lightbox__arrow:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.2);
}

.lightbox__arrow svg {
  display: block;
  width: 1.75rem;
  height: 1.75rem;
}

.lightbox__arrow--prev {
  left: 1.5rem;
}

.lightbox__arrow--next {
  right: 1.5rem;
}

.lightbox__caption {
  position: absolute;
  bottom: 2.5rem;
  left: 50%;
  transform: translateX(-50%);
  padding: 0.75rem 1.5rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  color: #fff;
  font-size: 0.875rem;
  font-weight: 500;
  letter-spacing: 0.04em;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
  white-space: nowrap;
}

/* ============ 动画关键帧 ============ */
@keyframes fade-in-up {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fade-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

/* ============ 响应式 ============ */
@media (min-width: 640px) {
  .photo-masonry {
    columns: 2;
  }
}

@media (min-width: 1024px) {
  .photo-masonry {
    columns: 3;
  }

  .album-detail__header {
    flex-direction: row;
    align-items: flex-end;
    justify-content: space-between;
  }
}

@media (max-width: 900px) {
  .album-grid {
    grid-template-columns: 1fr;
    row-gap: 4rem;
  }
}
</style>
