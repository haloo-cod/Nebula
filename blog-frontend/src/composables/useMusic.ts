import { ref, computed, type Ref } from 'vue'

// =============================================================================
// Meting API 公共接口 — 通过 api.injahow.cn 获取网易云音乐数据
// 参考 https://github.com/metowolf/Meting
//
// API 说明:
//   type=playlist → 返回 JSON 数组,每项含 name/artist/url/pic/lrc(均为完整 URL)
//   type=url       → 返回 raw MP3 二进制,可直接作为 <audio> src
//   type=pic       → 返回 raw JPEG/PNG 二进制,可直接作为 <img> src
//   type=lrc       → 返回 raw LRC 歌词文本
// =============================================================================

const METING_BASE = 'https://api.injahow.cn/meting/'

/** 歌单 ID(网易云音乐),修改此值即可切换歌单 */
const PLAYLIST_ID = '17644926373'

/** 歌曲数据结构 */
export interface Song {
  id: string
  title: string
  artist: string
  cover: string
  src: string
  lrc: string
}

/** 播放模式 */
export type PlayMode = 'loop' | 'single' | 'random'

/** Meting playlist API 返回的原始轨道格式 */
interface RawTrack {
  name: string
  artist: string | string[]
  url: string
  pic: string
  lrc: string
}

// =============================================================================
// 模块级单例 state(所有组件共享同一份数据)
// =============================================================================

const playlist: Ref<Song[]> = ref([])
const currentIndex = ref(0)
const isPlaying = ref(false)
const progress = ref(0)
const currentTime = ref(0)
const duration = ref(0)
const currentLyric = ref('')
const isLoading = ref(true)
const volume = ref(0.8)
const isMuted = ref(false)
const playModeVal = ref<PlayMode>('loop')
const lyrics: Ref<{ time: number; text: string }[]> = ref([])
const lrcCache = new Map<string, string>()
let audioEl: HTMLAudioElement | null = null
let loadPromise: Promise<void> | null = null

// =============================================================================
// LRC 歌词解析
// =============================================================================

function parseLrc(lrcText: string): { time: number; text: string }[] {
  if (!lrcText || lrcText.length > 30000) return []
  const lines = lrcText.split(/\r?\n/)
  const result: { time: number; text: string }[] = []
  for (const line of lines) {
    const matches = [...line.matchAll(/\[(\d{2,}):(\d{2})(?:\.(\d{2,3}))?\]/g)]
    if (matches.length === 0) continue
    const text = line
      .replace(/\[\d{2,}:\d{2}(?:\.\d{2,3})?\]/g, '')
      .replace(/[\x00-\x1f\x7f-\x9f\u200b-\u200f\u2028-\u202f\uFEFF\u00AD]/g, '')
      .trim()
    if (!text) continue
    for (const match of matches) {
      const min = parseInt(match[1])
      const sec = parseInt(match[2])
      const ms = match[3] ? parseInt(match[3]) : 0
      const divisor = match[3] && match[3].length === 3 ? 1000 : 100
      result.push({ time: min * 60 + sec + ms / divisor, text })
    }
  }
  return result.sort((a, b) => a.time - b.time)
}

// =============================================================================
// API 请求
// =============================================================================

async function metingFetchJson(params: Record<string, string>): Promise<any> {
  const qs = new URLSearchParams(params).toString()
  const res = await fetch(`${METING_BASE}?${qs}`)
  if (!res.ok) throw new Error(`Meting API ${res.status}`)
  return res.json()
}

/** 从 url/pic 等 API URL 中提取歌曲 ID,用于唯一标识与缓存 */
function extractId(apiUrl: string): string {
  const m = apiUrl.match(/[?&]id=(\d+)/)
  return m ? m[1] : String(Math.random())
}

/** 拉取歌单:playlist API 已返回所有可直接使用的 url/pic/lrc,无需二次请求 */
async function fetchPlaylist(): Promise<Song[]> {
  const tracks = (await metingFetchJson({
    server: 'netease',
    type: 'playlist',
    id: PLAYLIST_ID,
  })) as RawTrack[]
  if (!Array.isArray(tracks) || tracks.length === 0) return []

  return tracks.map(
    (track): Song => ({
      id: extractId(track.url),
      title: track.name || '未知歌曲',
      artist: Array.isArray(track.artist)
        ? track.artist.join(', ')
        : String(track.artist || '未知歌手'),
      cover: track.pic, // 直接作为 img src,API 返回 raw 图片
      src: track.url, // 直接作为 audio src,API 返回 raw MP3
      lrc: '',
    }),
  )
}

// =============================================================================
// 音频控制 (模块级,因为需要跨组件共享 audio 实例)
// =============================================================================

function ensureAudio(): HTMLAudioElement {
  if (!audioEl) {
    audioEl = new Audio()
    audioEl.volume = isMuted.value ? 0 : volume.value
    audioEl.ontimeupdate = () => {
      if (!audioEl) return
      const ct = audioEl.currentTime
      const dur = audioEl.duration || 0
      currentTime.value = ct
      duration.value = dur
      progress.value = dur > 0 ? (ct / dur) * 100 : 0
      const l = lyrics.value
      if (l.length > 0) {
        const active = [...l].reverse().find((x) => ct >= x.time)
        if (active) currentLyric.value = active.text
      }
    }
    audioEl.onended = () => {
      if (playModeVal.value === 'single') {
        if (audioEl) {
          audioEl.currentTime = 0
          audioEl.play().catch(() => {})
        }
      } else {
        playNext()
      }
    }
  }
  return audioEl
}

function destroyAudio() {
  if (audioEl) {
    audioEl.pause()
    audioEl.src = ''
    audioEl.ontimeupdate = null
    audioEl.onended = null
    audioEl = null
  }
}

/** 拉取单首歌词(LRC 文本) */
async function fetchLyrics(song: Song) {
  if (song.lrc) {
    lyrics.value = parseLrc(song.lrc)
    return
  }
  if (lrcCache.has(song.id)) {
    lyrics.value = parseLrc(lrcCache.get(song.id)!)
    return
  }
  if (!song.src) return
  // 从 playlist API 返回的 lrc 字段是歌词 API URL
  try {
    // 需要从歌曲 meta 里获取 lrc URL(playlist API 已返回,但我们的 Song 未存)
    // 这里通过替换 url type 来获取:把 type=url 换成 type=lrc
    const lrcUrl = song.src.replace(/type=url/, 'type=lrc')
    const res = await fetch(lrcUrl)
    if (!res.ok) throw new Error(`lrc ${res.status}`)
    const lrcText = await res.text()
    if (lrcText && !lrcText.startsWith('{')) {
      lrcCache.set(song.id, lrcText)
      song.lrc = lrcText
      lyrics.value = parseLrc(lrcText)
    } else {
      lyrics.value = []
    }
  } catch {
    lyrics.value = []
  }
}

function play(index: number) {
  currentIndex.value = index
  const song = playlist.value[index]
  if (!song || !song.src) return

  lyrics.value = []
  currentLyric.value = ''

  const audio = ensureAudio()
  audio.src = song.src
  audio
    .play()
    .then(() => {
      isPlaying.value = true
      fetchLyrics(song)
    })
    .catch(() => {
      isPlaying.value = false
    })
}

function togglePlay() {
  if (playlist.value.length === 0) return
  const audio = ensureAudio()
  if (isPlaying.value) {
    audio.pause()
    isPlaying.value = false
  } else {
    if (!audio.src && currentSong.value) {
      play(currentIndex.value)
      return
    }
    audio
      .play()
      .then(() => {
        isPlaying.value = true
      })
      .catch(() => {
        isPlaying.value = false
      })
  }
}

function playNext() {
  if (playlist.value.length === 0) return
  let next: number
  if (playModeVal.value === 'random') {
    next = Math.floor(Math.random() * playlist.value.length)
  } else {
    next = (currentIndex.value + 1) % playlist.value.length
  }
  play(next)
}

function playPrev() {
  if (playlist.value.length === 0) return
  let prev: number
  if (playModeVal.value === 'random') {
    prev = Math.floor(Math.random() * playlist.value.length)
  } else {
    prev = (currentIndex.value - 1 + playlist.value.length) % playlist.value.length
  }
  play(prev)
}

function handleSeek(value: number) {
  progress.value = value
  if (audioEl?.duration) {
    audioEl.currentTime = (value / 100) * audioEl.duration
  }
}

function setVol(val: number) {
  volume.value = val
  if (isMuted.value && val > 0) isMuted.value = false
  if (audioEl) audioEl.volume = isMuted.value ? 0 : val
}

function toggleMute() {
  isMuted.value = !isMuted.value
  if (audioEl) audioEl.volume = isMuted.value ? 0 : volume.value
}

function toggleMode() {
  const modes: PlayMode[] = ['loop', 'single', 'random']
  const idx = modes.indexOf(playModeVal.value)
  playModeVal.value = modes[(idx + 1) % modes.length]
}

// =============================================================================
// 公开 composable(所有组件通过它共享同一份模块级 state)
// =============================================================================

const currentSong = computed<Song | undefined>(() => playlist.value[currentIndex.value])

export function useMusic() {
  if (!loadPromise) {
    loadPromise = (async () => {
      isLoading.value = true
      try {
        const songs = await fetchPlaylist()
        playlist.value = songs
        console.log(`[music] 歌单加载完成: ${songs.length} 首`)
      } catch (e) {
        console.warn('[music] 歌单加载失败:', e)
      } finally {
        isLoading.value = false
      }
    })()
  }

  return {
    playlist,
    currentIndex,
    currentSong,
    isPlaying,
    progress,
    currentTime,
    duration,
    currentLyric,
    isLoading,
    volume,
    isMuted,
    playMode: playModeVal,
    togglePlay,
    nextSong: playNext,
    prevSong: playPrev,
    handleSeek,
    play,
    setVolume: setVol,
    toggleMute,
    togglePlayMode: toggleMode,
  }
}

// 页面销毁时清理音频资源
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', destroyAudio)
}
