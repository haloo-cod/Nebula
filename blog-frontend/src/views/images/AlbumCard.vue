<template>
  <div class="album-card" @click="emit('open', album)">
    <!-- 照片堆叠:三层"玻璃相框拍立得",悬停时扇形展开 -->
    <div class="photo-stack" :class="{ 'photo-stack--portrait': album.orientation === 'portrait' }">
      <!-- 底层照片(灰度+模糊,悬停向右飞出) -->
      <div v-if="album.photos[2]" class="stack-unit stack-unit--back">
        <LiquidGlass
          v-if="ui.liquidGlassEnabled"
          class="unit-glass"
          :theme="ui.theme"
          :corner-radius="8"
          :blur-radius="ui.liquidGlassBlur"
          :glass-thickness="28"
          :highlight-width="3"
          ripple-trail
        >
          <div class="unit-bezel">
            <div class="unit-mat">
              <img class="unit-img unit-img--back" :src="album.photos[2].url" alt="" loading="lazy" />
            </div>
          </div>
        </LiquidGlass>
        <div v-else class="unit-glass unit-glass--fallback">
          <div class="unit-bezel">
            <div class="unit-mat">
              <img class="unit-img unit-img--back" :src="album.photos[2].url" alt="" loading="lazy" />
            </div>
          </div>
        </div>
      </div>

      <!-- 中层照片(半灰度,悬停向左飞出) -->
      <div v-if="album.photos[1]" class="stack-unit stack-unit--mid">
        <LiquidGlass
          v-if="ui.liquidGlassEnabled"
          class="unit-glass"
          :theme="ui.theme"
          :corner-radius="8"
          :blur-radius="ui.liquidGlassBlur"
          :glass-thickness="28"
          :highlight-width="3"
          ripple-trail
        >
          <div class="unit-bezel">
            <div class="unit-mat">
              <img class="unit-img unit-img--mid" :src="album.photos[1].url" alt="" loading="lazy" />
            </div>
          </div>
        </LiquidGlass>
        <div v-else class="unit-glass unit-glass--fallback">
          <div class="unit-bezel">
            <div class="unit-mat">
              <img class="unit-img unit-img--mid" :src="album.photos[1].url" alt="" loading="lazy" />
            </div>
          </div>
        </div>
      </div>

      <!-- 封面(最上层,悬停上浮放大 + 遮罩淡入) -->
      <div class="stack-unit stack-unit--front">
        <LiquidGlass
          v-if="ui.liquidGlassEnabled"
          class="unit-glass"
          :theme="ui.theme"
          :corner-radius="8"
          :blur-radius="ui.liquidGlassBlur"
          :glass-thickness="28"
          :highlight-width="3"
          ripple-trail
        >
          <div class="unit-bezel">
            <div class="unit-mat">
              <img class="unit-img" :src="album.cover" :alt="album.title" loading="lazy" />
              <div class="unit-overlay">
                <span class="unit-overlay__count">{{ album.photos.length }} 张照片</span>
                <span class="unit-overlay__hint">Click to Open</span>
              </div>
            </div>
          </div>
        </LiquidGlass>
        <div v-else class="unit-glass unit-glass--fallback">
          <div class="unit-bezel">
            <div class="unit-mat">
              <img class="unit-img" :src="album.cover" :alt="album.title" loading="lazy" />
              <div class="unit-overlay">
                <span class="unit-overlay__count">{{ album.photos.length }} 张照片</span>
                <span class="unit-overlay__hint">Click to Open</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 相册信息 -->
    <div class="album-info">
      <div class="album-info__row">
        <h2 class="album-info__title">{{ album.title }}</h2>
        <span class="album-info__date">{{ album.date }}</span>
      </div>
      <p class="album-info__desc">{{ album.description }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import LiquidGlass from '@/components/liquid-glass/LiquidGlass.vue'
import { useUIStore } from '@/stores/ui'
import type { Album } from '@/types'

const ui = useUIStore()

defineProps<{
  album: Album
}>()

const emit = defineEmits<{
  open: [album: Album]
}>()
</script>

<style scoped>
.album-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
}

/* ============ 照片堆叠区 ============ */
.photo-stack {
  position: relative;
  width: 85%;
  aspect-ratio: 4 / 3;
  margin-bottom: 2rem;
}

/* 竖向堆叠:收窄宽度,宽高比改为 3/4 */
.photo-stack--portrait {
  width: 75%;
  aspect-ratio: 3 / 4;
}

/* 每一层 = 玻璃+照片整体单元,transform 作用于整个单元,玻璃随照片一起动 */
.stack-unit {
  position: absolute;
  inset: 0;
  transition: transform 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.stack-unit--back {
  transform: rotate(6deg) translate(1rem, 0.5rem);
  opacity: 0.6;
  filter: drop-shadow(0 4px 6px rgba(0, 0, 0, 0.25));
}

.stack-unit--mid {
  z-index: 10;
  transform: rotate(-3deg) translate(-0.5rem, -0.25rem);
  opacity: 0.8;
  filter: drop-shadow(0 10px 15px rgba(0, 0, 0, 0.3));
}

.stack-unit--front {
  z-index: 20;
  filter: drop-shadow(0 20px 25px rgba(0, 0, 0, 0.35));
}

/* 悬停扇出:底层右飞加大旋转,中层左飞,封面上浮放大 */
.album-card:hover .stack-unit--back {
  transform: rotate(12deg) translate(2rem, 0.5rem);
}

.album-card:hover .stack-unit--mid {
  transform: rotate(-6deg) translate(-1.5rem, -0.25rem);
}

.album-card:hover .stack-unit--front {
  transform: translateY(-0.5rem) scale(1.05);
}

/* ============ 玻璃相框单元 ============ */
.unit-glass {
  width: 100%;
  height: 100%;
  border-radius: 8px;
}

/* 玻璃关闭时的兜底:透明边框 + 白色相纸,即参考站原版观感 */
.unit-glass--fallback {
  display: block;
}

/* 玻璃包边:内缩出玻璃折射可见的边框区 */
.unit-bezel {
  box-sizing: border-box;
  width: 100%;
  height: 100%;
  padding: 10px;
}

/* 白色相纸(拍立得白边) */
.unit-mat {
  position: relative;
  box-sizing: border-box;
  width: 100%;
  height: 100%;
  padding: 6px;
  background: rgba(255, 255, 255, 0.92);
  border-radius: 4px;
  overflow: hidden;
}

.unit-img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 2px;
}

/* 底层/中层照片的做旧滤镜(只作用于照片本身,不影响玻璃包边) */
.unit-img--back {
  filter: grayscale(1) blur(2px);
}

.unit-img--mid {
  filter: grayscale(0.5);
}

/* ============ 封面悬停遮罩 ============ */
.unit-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  padding: 1.25rem;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.8), rgba(0, 0, 0, 0.2), transparent);
  opacity: 0;
  transition: opacity 0.5s ease;
}

.album-card:hover .unit-overlay {
  opacity: 1;
}

.unit-overlay__count {
  color: #fff;
  font-size: 1.125rem;
  font-weight: 700;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
  transform: translateY(0.5rem);
  transition: transform 0.5s ease;
}

.unit-overlay__hint {
  margin-top: 0.25rem;
  color: rgba(140, 218, 214, 0.9);
  font-size: 0.75rem;
  font-weight: 500;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
  transform: translateY(0.5rem);
  transition: transform 0.5s ease 75ms;
}

[data-theme='light'] .unit-overlay__hint {
  color: rgba(14, 116, 110, 0.9);
}

.album-card:hover .unit-overlay__count,
.album-card:hover .unit-overlay__hint {
  transform: translateY(0);
}

/* ============ 相册信息 ============ */
.album-info {
  width: 100%;
  padding: 0 1rem;
  text-align: center;
}

.album-info__row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
}

.album-info__title {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-primary);
  transition: color 0.3s ease;
}

.album-card:hover .album-info__title {
  color: rgba(140, 218, 214, 0.95);
}

/* 亮色主题下,青色悬停需加深以保证浅色背景对比度 */
[data-theme='light'] .album-card:hover .album-info__title {
  color: rgba(14, 116, 110, 0.95);
}

.album-info__date {
  padding: 0.125rem 0.5rem;
  border-radius: 0.25rem;
  background: var(--glass-bg);
  border: 1px solid var(--glass-border-subtle);
  color: var(--text-secondary);
  font-size: 0.625rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.album-info__desc {
  font-size: 0.875rem;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
