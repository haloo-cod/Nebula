<template>
  <div v-if="visible && currentSong" ref="panelRef" class="floating-player">
    <!-- 歌词:从下方滑入 -->
    <Transition name="lyric-up">
      <div v-if="expanded && currentLyric" class="lyric-bar">
        <span class="lyric-text">{{ currentLyric }}</span>
      </div>
    </Transition>

    <!-- 主体:封面 + 向右生长出按钮区 -->
    <div
      class="main-bar"
      :class="{ 'is-expanded': expanded }"
      @click="!expanded && (expanded = true)"
    >
      <!-- 封面圆(始终可见) -->
      <div class="cover-circle">
        <img :src="currentSong.cover" alt="" class="cover-img" draggable="false" />
        <div v-if="isPlaying && !expanded" class="pulse-overlay">
          <div
            v-for="i in 3"
            :key="i"
            class="pulse-bar"
            :style="{ height: `${10 + i * 5}px`, animationDelay: `${(i - 1) * 150}ms` }"
          />
        </div>
      </div>

      <!-- 按钮区:展开时显现 -->
      <div class="controls-group">
        <div class="song-info">
          <div class="song-title">{{ currentSong.title }}</div>
          <div class="song-artist">{{ currentSong.artist }}</div>
        </div>

        <button class="ctrl-btn" title="上一首" @click.stop="prevSong">
          <svg class="icon" fill="currentColor" viewBox="0 0 24 24">
            <path d="M6 6h2v12H6zm3.5 6l8.5 6V6z" />
          </svg>
        </button>
        <button
          class="ctrl-btn play-btn"
          :title="isPlaying ? '暂停' : '播放'"
          @click.stop="togglePlay"
        >
          <svg v-if="isPlaying" class="icon" fill="currentColor" viewBox="0 0 24 24">
            <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z" />
          </svg>
          <svg v-else class="icon ml-px" fill="currentColor" viewBox="0 0 24 24">
            <path d="M8 5v14l11-7z" />
          </svg>
        </button>
        <button class="ctrl-btn" title="下一首" @click.stop="nextSong">
          <svg class="icon" fill="currentColor" viewBox="0 0 24 24">
            <path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z" />
          </svg>
        </button>

        <button class="ctrl-btn" :title="modeLabel" @click.stop="togglePlayMode">
          <svg
            v-if="playMode === 'loop'"
            class="icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M4 12v-3a3 3 0 0 1 3 -3h13m-3 -3l3 3l-3 3" />
            <path d="M20 12v3a3 3 0 0 1 -3 3h-13m3 3l-3 -3l3 -3" />
          </svg>
          <svg
            v-else-if="playMode === 'single'"
            class="icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M4 12v-3a3 3 0 0 1 3 -3h13m-3 -3l3 3l-3 3" />
            <path d="M20 12v3a3 3 0 0 1 -3 3h-13m3 3l-3 -3l3 -3" />
            <path d="M11 11l1 -1v4" />
          </svg>
          <svg
            v-else
            class="icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M18 4l3 3l-3 3" />
            <path d="M18 20l3 -3l-3 -3" />
            <path d="M3 7h3a5 5 0 0 1 5 5a5 5 0 0 0 5 5h5" />
            <path d="M21 7h-5a4.978 4.978 0 0 0 -3 1m-4 8a4.984 4.984 0 0 1 -3 1h-3" />
          </svg>
        </button>

        <button class="ctrl-btn" :title="isMuted ? '取消静音' : '静音'" @click.stop="toggleMute">
          <svg
            v-if="isMuted || volume === 0"
            class="icon"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M11 5L6 9H2v6h4l5 4V5z" />
            <line x1="23" y1="9" x2="17" y2="15" />
            <line x1="17" y1="9" x2="23" y2="15" />
          </svg>
          <svg
            v-else-if="volume > 0.5"
            class="icon"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M11 5L6 9H2v6h4l5 4V5z" />
            <path d="M19.07 4.93a10 10 0 010 14.14M15.54 8.46a5 5 0 010 7.07" />
          </svg>
          <svg
            v-else
            class="icon"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M11 5L6 9H2v6h4l5 4V5z" />
            <path d="M15.54 8.46a5 5 0 010 7.07" />
          </svg>
        </button>
        <input
          type="range"
          min="0"
          max="1"
          step="0.01"
          :value="isMuted ? 0 : volume"
          title="音量"
          class="volume-slider"
          @input="setVolume(($event.target as HTMLInputElement).value as unknown as number)"
        />

        <button ref="playlistBtnRef" class="ctrl-btn" title="播放列表" @click.stop="togglePlaylist">
          <svg
            class="icon"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M4 6h16M4 10h16M4 14h10M4 18h10" />
          </svg>
        </button>

        <button class="ctrl-btn collapse-btn" title="收起" @click.stop="expanded = false">
          <svg
            class="icon"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M15 19l-7-7 7-7" />
          </svg>
        </button>
      </div>
    </div>

    <!-- 歌单下拉 -->
    <div
      v-if="showPlaylist"
      class="playlist-dropdown"
      :class="playlistUp ? 'bottom-full' : 'top-full'"
    >
      <button
        v-for="(song, i) in playlist"
        :key="song.id"
        class="playlist-item"
        :class="{ active: i === currentIndex }"
        @click.stop="playSong(i)"
      >
        <div class="pl-cover-wrap"><img :src="song.cover" alt="" class="pl-cover" /></div>
        <div class="pl-info">
          <div class="pl-title">{{ song.title }}</div>
          <div class="pl-artist">{{ song.artist }}</div>
        </div>
        <div v-if="i === currentIndex && isPlaying" class="pl-playing-bars">
          <div
            v-for="j in 3"
            :key="j"
            class="pl-bar"
            :style="{ height: `${8 + j * 5}px`, animationDelay: `${(j - 1) * 150}ms` }"
          />
        </div>
      </button>
      <div v-if="playlist.length === 0" class="pl-empty">暂无歌曲</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useMusic } from '@/composables/useMusic'

const {
  playlist,
  currentIndex,
  currentSong,
  isPlaying,
  currentLyric,
  volume,
  isMuted,
  playMode,
  togglePlay,
  nextSong,
  prevSong,
  setVolume,
  toggleMute,
  togglePlayMode,
  play,
} = useMusic()

const expanded = ref(false)
const showPlaylist = ref(false)
const playlistUp = ref(false)
const visible = ref(false)
const panelRef = ref<HTMLElement | null>(null)
const playlistBtnRef = ref<HTMLElement | null>(null)

const modeLabel = computed(() => {
  const map: Record<string, string> = { loop: '列表循环', single: '单曲循环', random: '随机播放' }
  return map[playMode.value] || '列表循环'
})

function playSong(index: number) {
  play(index)
  showPlaylist.value = false
}

onMounted(() => {
  setTimeout(() => {
    visible.value = true
  }, 600)
})

function onDocumentMouseDown(e: MouseEvent) {
  if (!expanded.value) return
  if (panelRef.value && !panelRef.value.contains(e.target as Node)) {
    expanded.value = false
    showPlaylist.value = false
  }
}

function togglePlaylist() {
  if (!showPlaylist.value) {
    nextTick(() => {
      if (playlistBtnRef.value) {
        const rect = playlistBtnRef.value.getBoundingClientRect()
        playlistUp.value = window.innerHeight - rect.bottom < 350
      }
    })
  }
  showPlaylist.value = !showPlaylist.value
}

onMounted(() => document.addEventListener('mousedown', onDocumentMouseDown))
onUnmounted(() => document.removeEventListener('mousedown', onDocumentMouseDown))
</script>

<style scoped>
/* ==================================================================
   FloatingPlayer — 左下角悬浮音乐播放器
   ================================================================== */

.floating-player {
  position: fixed;
  bottom: 2rem;
  left: 1.5rem;
  z-index: 110;
  user-select: none;
  touch-action: none;
}

/* ---- 歌词:从下向上滑入 ---- */
.lyric-up-enter-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.lyric-up-leave-active {
  transition: all 0.2s ease;
}
.lyric-up-enter-from {
  opacity: 0;
  transform: translateY(10px);
}
.lyric-up-leave-to {
  opacity: 0;
  transform: translateY(6px);
}

.lyric-bar {
  max-width: 400px;
  padding: 8px 18px;
  border-radius: 12px;
  background: rgba(0, 0, 0, 0.35);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
  word-break: break-all;
  margin-bottom: 8px;
}

.lyric-text {
  font-size: 13px;
  font-weight: 500;
  color: rgba(160, 200, 255, 0.9);
  line-height: 1.6;
}

/* ---- 主体容器:宽度生长动画 ---- */
.main-bar {
  display: flex;
  align-items: center;
  height: 64px;
  max-width: 64px;
  border-radius: 32px;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
  overflow: hidden;
  transition:
    max-width 0.4s cubic-bezier(0.4, 0, 0.2, 1),
    border-color 0.3s ease;
  cursor: pointer;
}

.main-bar.is-expanded {
  max-width: 540px;
  border-color: rgba(255, 255, 255, 0.08);
  cursor: default;
}

/* ---- 封面圆 ---- */
.cover-circle {
  width: 64px;
  height: 64px;
  flex-shrink: 0;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.cover-img {
  width: 48px;
  height: 48px;
  object-fit: cover;
  border-radius: 50%;
  pointer-events: none;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

.pulse-overlay {
  position: absolute;
  inset: 8px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 3px;
}

.pulse-bar {
  width: 4px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 3px 3px 0 0;
  animation: pulseAnim 0.8s ease-in-out infinite alternate;
}

@keyframes pulseAnim {
  0% {
    height: 6px;
  }
  100% {
    height: 16px;
  }
}

/* ---- 按钮区 ---- */
.controls-group {
  display: flex;
  align-items: center;
  gap: 5px;
  padding-right: 8px;
  white-space: nowrap;
  opacity: 0;
  transition: opacity 0.25s ease 0.18s;
}

.main-bar.is-expanded .controls-group {
  opacity: 1;
}

/* 歌曲信息 */
.song-info {
  min-width: 0;
  max-width: 100px;
  padding: 0 4px;
}

.song-title {
  font-size: 13px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.song-artist {
  font-size: 11px;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.45);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 1px;
}

/* 控制按钮 */
.ctrl-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  background: transparent;
  color: rgba(200, 210, 230, 0.7);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition:
    color 0.15s,
    background 0.15s;
}

.ctrl-btn:hover {
  color: rgba(160, 200, 255, 1);
  background: rgba(255, 255, 255, 0.08);
}

.ctrl-btn:active {
  transform: scale(0.92);
}

.play-btn {
  width: 40px;
  height: 40px;
  background: rgba(120, 160, 240, 0.45);
  color: #fff;
  border-radius: 50%;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

.play-btn:hover {
  background: rgba(120, 160, 240, 0.65);
  color: #fff;
}

.collapse-btn {
  color: rgba(255, 255, 255, 0.35);
}
.collapse-btn:hover {
  color: rgba(255, 255, 255, 0.7);
}

.icon {
  width: 20px;
  height: 20px;
}

.ml-px {
  margin-left: 1px;
}

/* 音量滑块 */
.volume-slider {
  width: 64px;
  height: 5px;
  accent-color: rgba(160, 200, 255, 0.85);
  cursor: pointer;
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 3px;
  appearance: none;
  -webkit-appearance: none;
}

.volume-slider::-webkit-slider-thumb {
  appearance: none;
  -webkit-appearance: none;
  width: 13px;
  height: 13px;
  border-radius: 50%;
  background: rgba(200, 220, 255, 0.9);
  cursor: pointer;
}

/* ---- 歌单下拉 ---- */
.playlist-dropdown {
  position: absolute;
  left: 0;
  width: 260px;
  max-height: 300px;
  overflow-y: auto;
  border-radius: 16px;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.5);
  padding: 8px;
  margin-top: 8px;
  margin-bottom: 8px;
}

.playlist-dropdown::-webkit-scrollbar {
  width: 0px;
  background: transparent;
}

.playlist-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 10px;
  border: none;
  background: transparent;
  cursor: pointer;
  text-align: left;
  transition: background 0.15s;
}

.playlist-item:hover {
  background: rgba(255, 255, 255, 0.06);
}
.playlist-item.active {
  background: rgba(120, 160, 240, 0.18);
}

.pl-cover-wrap {
  width: 38px;
  height: 38px;
  border-radius: 8px;
  overflow: hidden;
  flex-shrink: 0;
}

.pl-cover {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.pl-info {
  flex: 1;
  min-width: 0;
}

.pl-title {
  font-size: 13px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.playlist-item.active .pl-title {
  color: rgba(160, 200, 255, 0.95);
}

.pl-artist {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.pl-empty {
  text-align: center;
  padding: 16px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.3);
}

.pl-playing-bars {
  display: flex;
  align-items: flex-end;
  gap: 2px;
  height: 18px;
  flex-shrink: 0;
}

.pl-bar {
  width: 3px;
  background: rgba(140, 180, 240, 0.85);
  border-radius: 2px 2px 0 0;
  animation: pulseAnim 0.7s ease-in-out infinite alternate;
}
</style>
