<template>
  <PageBackground>
    <main class="gallery-images-page">
      <RouterLink to="/" class="back-link">返回首页</RouterLink>

      <section class="section-heading">
        <span class="gallery-kicker">Images</span>
        <h1>图片</h1>
        <p>这里先展示本地图片素材,后续可以替换为后端相册数据。</p>
      </section>

      <div class="image-grid">
        <figure v-for="image in images" :key="image.name" class="image-card glass-subtle">
          <img :src="image.url" :alt="image.name" />
          <figcaption>{{ image.name }}</figcaption>
        </figure>
      </div>
    </main>
  </PageBackground>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
import PageBackground from '@/components/PageBackground.vue'

const imageFiles = import.meta.glob<string>('../../assets/img2/*.{png,PNG,jpg,JPG,jpeg,jfif}', {
  query: '?url',
  import: 'default',
  eager: true,
})

const images = Object.entries(imageFiles).map(([path, url]) => ({
  name: path.split('/').pop() || 'image',
  url,
}))
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

.gallery-kicker {
  display: block;
  margin-top: 1.5rem;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: rgba(140, 218, 214, 0.74);
}

.section-heading h1 {
  margin-top: 0.75rem;
  font-size: clamp(2.5rem, 7vw, 5rem);
  line-height: 1;
  font-weight: 850;
  letter-spacing: -0.06em;
  color: rgba(255, 255, 255, 0.94);
}

.section-heading p {
  margin-top: 1rem;
  color: rgba(230, 246, 255, 0.6);
}

.image-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1rem;
  margin-top: 1.5rem;
}

.image-card {
  overflow: hidden;
  border-radius: 1rem;
}

.image-card img {
  display: block;
  width: 100%;
  aspect-ratio: 4 / 3;
  object-fit: cover;
}

.image-card figcaption {
  padding: 0.85rem 1rem;
  color: rgba(230, 246, 255, 0.68);
  font-size: 0.85rem;
}

@media (max-width: 900px) {
  .image-grid {
    grid-template-columns: 1fr;
  }
}
</style>
