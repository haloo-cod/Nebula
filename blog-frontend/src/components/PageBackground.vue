<template>
  <div class="page-background">
    <!-- 背景层：fixed 定位，不使用 translateZ/will-change 以免阻断子元素 backdrop-filter 采样 -->
    <div v-if="!isVideo || videoFailed || reducedMotion" class="bg-layer" :style="bgLayerStyle"></div>
    <video
      v-else
      ref="videoRef"
      class="bg-video"
      :src="displayedBackground.src"
      :poster="displayedBackground.posterUrl"
      muted
      loop
      autoplay
      playsinline
      crossorigin="anonymous"
      preload="metadata"
      @error="videoFailed = true"
    ></video>
    <!-- 叠加层 -->
    <div class="overlay-layer" :style="{ background: `rgba(0,0,0,${overlay})` }"></div>
    <!-- 内容插槽 -->
    <div class="relative z-10">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, shallowRef, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useUIStore } from '@/stores/ui'
import { isVideoBackground } from '@/data/backgrounds'
import type { BackgroundItem } from '@/data/backgrounds'
import { bindVideoElement } from '@/components/liquid-glass/liquidGlassRenderer'

// overlay:遮罩层不透明度(0~1),数值越大背景越暗
withDefaults(defineProps<{ overlay?: number }>(), {
  overlay: 0.09,
})

const { backgroundBlur, backgroundBlurEnabled, currentBackground } = storeToRefs(useUIStore())
const videoRef = ref<HTMLVideoElement | null>(null)
const videoFailed = ref(false)
const reducedMotion = ref(false)
const displayedBackground = shallowRef<BackgroundItem>(currentBackground.value)
const background = computed(() => displayedBackground.value)
const isVideo = computed(() => isVideoBackground(background.value))

const bgLayerStyle = computed(() => {
  const blur = backgroundBlurEnabled.value ? backgroundBlur.value : 0
  const scale = blur > 0 ? 1 + Math.min(blur / 240, 0.08) : 1
  return {
    backgroundImage: !isVideo.value && background.value.src ? `url(${background.value.src})` : undefined,
    backgroundColor: 'var(--page-background)',
    filter: blur > 0 ? `blur(${blur}px)` : undefined,
    transform: scale !== 1 ? `scale(${scale})` : undefined,
  }
})

function playVideo() {
  videoFailed.value = false
  const video = videoRef.value
  if (!video) return
  // 让 WebGL 纹理复用页面上真正显示的 video，避免隐藏副本与背景播放进度漂移。
  if (!bindVideoElement(displayedBackground.value.src, video)) {
    video.addEventListener('loadeddata', () => {
      bindVideoElement(displayedBackground.value.src, video)
    }, { once: true })
  }
  void video.play().catch(() => { videoFailed.value = true })
}

let switchToken = 0
async function switchBackground(next: BackgroundItem) {
  const token = ++switchToken
  if (next.src === displayedBackground.value.src) return

  // 先在后台确认资源可用，准备完成前继续显示旧背景，避免切换瞬间黑屏。
  if (isVideoBackground(next)) {
    const probe = document.createElement('video')
    probe.muted = true
    probe.playsInline = true
    probe.preload = 'metadata'
    probe.src = next.src
    const ready = await new Promise<boolean>((resolve) => {
      const done = (ok: boolean) => {
        probe.removeEventListener('canplay', onReady)
        probe.removeEventListener('loadeddata', onReady)
        probe.removeEventListener('error', onError)
        resolve(ok)
      }
      const onReady = () => done(true)
      const onError = () => done(false)
      probe.addEventListener('canplay', onReady, { once: true })
      probe.addEventListener('loadeddata', onReady, { once: true })
      probe.addEventListener('error', onError, { once: true })
      probe.load()
    })
    probe.removeAttribute('src')
    probe.load()
    if (!ready || token !== switchToken) return
  } else {
    const ready = await new Promise<boolean>((resolve) => {
      const image = new Image()
      image.onload = () => resolve(true)
      image.onerror = () => resolve(false)
      image.src = next.src
    })
    if (!ready || token !== switchToken) return
  }

  displayedBackground.value = next
  videoFailed.value = false
  await nextTick()
  playVideo()
}

watch(currentBackground, (next) => { void switchBackground(next) }, { deep: true, immediate: true })
onMounted(() => {
  reducedMotion.value = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  playVideo()
})
onUnmounted(() => { videoRef.value?.pause() })
</script>

<style scoped>
.bg-layer {
  position: fixed;
  inset: 0;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  z-index: 0;
}

.page-background {
  position: fixed;
  inset: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  z-index: 0;
  pointer-events: none;
}

.bg-video {
  position: fixed;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  z-index: 0;
}

.overlay-layer {
  position: fixed;
  inset: 0;
  z-index: 1;
}
</style>
