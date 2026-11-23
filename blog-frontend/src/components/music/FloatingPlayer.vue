<template>
  <div v-if="visible && currentSong" ref="panelRef" class="floating-player" :class="{ 'is-expanded': expanded }" @transitionend="onPanelTransitionEnd">
    <component
      :is="ui.liquidGlassEnabled ? LiquidGlass : PanelFallbackGlass"
      class="player-glass"
      :theme="ui.theme"
      :blur-radius="ui.liquidGlassBlur"
      :corner-radius="32"
    >
      <button
        v-if="!expanded"
        class="player-orb"
        type="button"
        aria-label="展开音乐播放器"
        aria-expanded="false"
        @click="expanded = true"
      >
        <img :src="currentSong.cover" alt="" draggable="false" />
        <span v-if="isPlaying" class="playing-indicator" aria-hidden="true"><i></i><i></i><i></i></span>
      </button>

      <section v-else class="player-panel" aria-label="音乐播放器">
        <header class="player-header">
          <div class="now-playing">NOW PLAYING <span class="header-line"></span></div>
          <div class="header-actions">
            <button
              class="icon-button playlist-toggle"
              type="button"
              :aria-label="showPlaylist ? '收起播放列表' : '打开播放列表'"
              :aria-expanded="showPlaylist"
              @click="showPlaylist = !showPlaylist"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><path d="M4 6h16M4 10h16M4 14h10M4 18h10" /></svg>
            </button>
            <button class="icon-button" type="button" aria-label="收起音乐播放器" @click="collapse">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><path d="M5 12h14M12 5l-7 7 7 7" /></svg>
            </button>
          </div>
        </header>

        <div class="track-heading">
          <img :src="currentSong.cover" alt="" class="track-cover" draggable="false" />
          <div class="track-copy">
            <div class="track-caption">此刻播放</div>
            <h2 class="track-title">{{ currentSong.title }}</h2>
            <p class="track-artist">{{ currentSong.artist }}</p>
          </div>
        </div>

        <div class="player-content">
          <div v-if="!showPlaylist" class="lyrics-view" aria-label="歌词">
            <div v-if="lyricsLoading" class="content-message">正在加载歌词…</div>
            <div v-else-if="!lyrics.length" class="content-message">暂无歌词，静静聆听</div>
            <div v-else ref="lyricsRef" class="lyrics-scroll">
              <p
                v-for="(line, index) in lyrics"
                :key="`${line.time}-${index}`"
                class="lyric-line"
                :class="{ 'is-current': index === currentLyricIndex }"
              >{{ line.text }}</p>
            </div>
          </div>
          <div v-else class="playlist-view" aria-label="播放列表">
            <div class="playlist-heading"><span>播放列表</span><span>{{ playlist.length }} 首</span></div>
            <div class="playlist-scroll">
              <button
                v-for="(song, index) in playlist"
                :key="song.id"
                class="playlist-item"
                :class="{ 'is-current': index === currentIndex }"
                type="button"
                @click="playSong(index)"
              >
                <span class="playlist-index">{{ String(index + 1).padStart(2, '0') }}</span>
                <span class="playlist-copy"><strong>{{ song.title }}</strong><small>{{ song.artist }}</small></span>
                <span v-if="index === currentIndex" class="playlist-current">{{ isPlaying ? '播放中' : '当前' }}</span>
              </button>
              <p v-if="!playlist.length" class="content-message">暂无歌曲</p>
            </div>
          </div>
        </div>

        <div class="player-footer">
          <div class="timeline">
            <span>{{ formatTime(currentTime) }}</span>
            <input type="range" min="0" max="100" step="0.1" :value="progress" :disabled="!duration" aria-label="播放进度" @input="handleSeek(Number(($event.target as HTMLInputElement).value))" />
            <span>{{ formatTime(duration) }}</span>
          </div>
          <div class="controls">
            <button class="icon-button mode-button" type="button" :title="modeLabel" :aria-label="modeLabel" @click="togglePlayMode">
              <svg v-if="playMode === 'random'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><path d="M18 4l3 3-3 3M18 20l3-3-3-3M3 7h3a5 5 0 0 1 5 5 5 5 0 0 0 5 5h5M21 7h-5a5 5 0 0 0-3 1M9 16a5 5 0 0 1-3 1H3" /></svg>
              <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><path d="M4 12V9a3 3 0 0 1 3-3h13m-3-3 3 3-3 3M20 12v3a3 3 0 0 1-3 3H4m3 3-3-3 3-3" /><path v-if="playMode === 'single'" d="M11 11l1-1v4" /></svg>
            </button>
            <div class="playback-buttons">
              <button class="icon-button" type="button" aria-label="上一首" @click="prevSong"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M6 6h2v12H6zm3.5 6 8.5 6V6z" /></svg></button>
              <button class="play-button" type="button" :aria-label="isPlaying ? '暂停' : '播放'" @click="togglePlay">
                <svg v-if="isPlaying" viewBox="0 0 24 24" fill="currentColor"><path d="M6 19h4V5H6zm8-14v14h4V5z" /></svg>
                <svg v-else viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z" /></svg>
              </button>
              <button class="icon-button" type="button" aria-label="下一首" @click="nextSong"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M6 18l8.5-6L6 6zm10-12v12h2V6z" /></svg></button>
            </div>
            <div class="volume-control">
              <button class="icon-button" type="button" :aria-label="isMuted ? '取消静音' : '静音'" @click="toggleMute">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><path d="M11 5 6 9H2v6h4l5 4z" /><path v-if="isMuted || volume === 0" d="m17 9 5 6m0-6-5 6" /><path v-else d="M15.5 8.5a5 5 0 0 1 0 7m3-10a9 9 0 0 1 0 13" /></svg>
              </button>
              <input type="range" min="0" max="1" step="0.01" :value="isMuted ? 0 : volume" aria-label="音量" @input="setVolume(Number(($event.target as HTMLInputElement).value))" />
            </div>
          </div>
        </div>
      </section>
    </component>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import LiquidGlass from '@/components/liquid-glass/LiquidGlass.vue'
import PanelFallbackGlass from '@/components/panels/PanelFallbackGlass.vue'
import { useMusic } from '@/composables/useMusic'
import { useUIStore } from '@/stores/ui'

const ui = useUIStore()
const {
  playlist, currentIndex, currentSong, isPlaying, progress, currentTime, duration,
  lyrics, lyricsLoading, currentLyricIndex, volume, isMuted, playMode,
  togglePlay, nextSong, prevSong, handleSeek, setVolume, toggleMute, togglePlayMode, play,
} = useMusic()

const expanded = ref(false)
const showPlaylist = ref(false)
const visible = ref(false)
const panelRef = ref<HTMLElement | null>(null)
const lyricsRef = ref<HTMLElement | null>(null)
let revealTimer: ReturnType<typeof setTimeout> | undefined

const modeLabel = computed(() => ({ loop: '列表循环', single: '单曲循环', random: '随机播放' })[playMode.value])

function formatTime(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds < 0) return '0:00'
  const total = Math.floor(seconds)
  return `${Math.floor(total / 60)}:${String(total % 60).padStart(2, '0')}`
}

function collapse() {
  expanded.value = false
  showPlaylist.value = false
}

function playSong(index: number) {
  play(index)
  showPlaylist.value = false
}

function onDocumentPointerDown(event: PointerEvent) {
  if (expanded.value && event.target instanceof Node && !panelRef.value?.contains(event.target)) collapse()
}

function onKeyDown(event: KeyboardEvent) {
  if (event.key === 'Escape' && expanded.value) collapse()
}

function scrollToCurrentLyric(behavior: ScrollBehavior = 'smooth') {
  if (!expanded.value || showPlaylist.value || currentLyricIndex.value < 0) return
  const container = lyricsRef.value
  const line = container?.querySelector<HTMLElement>('.lyric-line.is-current')
  if (container && line) {
    container.scrollTo({ top: line.offsetTop - container.clientHeight / 2 + line.clientHeight / 2, behavior })
  }
}

function onPanelTransitionEnd(event: TransitionEvent) {
  if (event.target === panelRef.value && event.propertyName === 'height') scrollToCurrentLyric('instant')
}

watch([currentLyricIndex, showPlaylist, expanded, lyrics], async () => {
  await nextTick()
  scrollToCurrentLyric()
})

onMounted(() => {
  revealTimer = setTimeout(() => { visible.value = true }, 600)
  document.addEventListener('pointerdown', onDocumentPointerDown)
  document.addEventListener('keydown', onKeyDown)
})
onUnmounted(() => {
  if (revealTimer) clearTimeout(revealTimer)
  document.removeEventListener('pointerdown', onDocumentPointerDown)
  document.removeEventListener('keydown', onKeyDown)
})
</script>

<style scoped src="@/assets/styles/floating-player.css"></style>
