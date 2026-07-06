<template>
  <div
    class="reader-page"
    :class="[
      `reader-page--${readingMode}`,
      `reader-page--${readerTheme}`,
      { 'reader-page--toc-open': tocOpen && tocItems.length > 0 },
    ]"
  >
    <div class="reader-bg"></div>
    <div class="reader-ambient reader-ambient-one"></div>
    <div class="reader-ambient reader-ambient-two"></div>

    <header class="reader-toolbar">
      <button class="reader-back" type="button" @click="goBack">返回书架</button>

      <div class="reader-title-wrap">
        <p class="reader-kicker">Glass Study</p>
        <h1 class="reader-title">{{ book?.title || '图书阅读器' }}</h1>
        <p v-if="book?.author" class="reader-author">{{ book.author }}</p>
      </div>

      <div class="reader-controls">
        <button
          class="reader-icon-btn reader-toc-btn"
          type="button"
          :disabled="tocItems.length === 0"
          @click="toggleToc"
        >
          目录
        </button>

        <div class="mode-switch" aria-label="阅读模式">
          <button
            class="mode-btn"
            :class="{ 'mode-btn-active': readingMode === 'paginated' }"
            type="button"
            :disabled="loading || isReaderBusy"
            @click="changeReadingMode('paginated')"
          >
            翻页
          </button>
          <button
            class="mode-btn"
            :class="{ 'mode-btn-active': readingMode === 'scrolled' }"
            type="button"
            :disabled="loading || isReaderBusy"
            @click="changeReadingMode('scrolled')"
          >
            滚动
          </button>
        </div>

        <button class="reader-icon-btn" type="button" @click="toggleReaderTheme">
          {{ readerTheme === 'light' ? '夜读' : '日间' }}
        </button>

        <div class="font-control">
          <button
            class="reader-icon-btn"
            type="button"
            aria-label="减小字号"
            @click="decreaseFontSize"
          >
            A-
          </button>
          <span class="font-scale">{{ fontScale }}%</span>
          <button
            class="reader-icon-btn"
            type="button"
            aria-label="增大字号"
            @click="increaseFontSize"
          >
            A+
          </button>
        </div>
      </div>
    </header>

    <main class="reader-main">
      <aside class="toc-panel" :class="{ 'toc-panel-open': tocOpen }">
        <div class="toc-head">
          <p>Table of Contents</p>
          <button class="reader-icon-btn toc-close" type="button" @click="toggleToc">收起</button>
        </div>
        <div v-if="tocItems.length === 0" class="toc-empty">目录整理中...</div>
        <button
          v-for="item in tocItems"
          :key="item.href + item.label + item.depth"
          class="toc-item"
          :class="{ 'toc-item-active': isTocItemActive(item.href) }"
          type="button"
          :style="{ '--toc-depth': item.depth }"
          @click="displayTocItem(item.href)"
        >
          {{ item.label }}
        </button>
      </aside>

      <section class="book-stage" :class="{ 'book-stage--loading': loading || error }">
        <button
          v-if="readingMode === 'paginated' && !loading && !error"
          class="page-turn page-turn-prev"
          type="button"
          aria-label="上一页"
          @click="prevPage"
        >
          <span>‹</span>
        </button>

        <div class="paper-shell">
          <div v-if="loading" class="reader-state">正在整理书页...</div>
          <div v-else-if="error" class="reader-state reader-state-error">
            <p>{{ error }}</p>
            <p class="reader-hint">
              请确认图书文件仍位于 src/assets/testepub/ 且构建后资源可正常访问。
            </p>
          </div>
          <div
            :key="viewerKey"
            ref="viewerRef"
            class="reader-viewer"
            :class="{ 'reader-viewer-hidden': loading || error }"
          ></div>
        </div>

        <button
          v-if="readingMode === 'paginated' && !loading && !error"
          class="page-turn page-turn-next"
          type="button"
          aria-label="下一页"
          @click="nextPage"
        >
          <span>›</span>
        </button>
      </section>
    </main>

    <footer class="reader-footer" v-if="!loading && !error">
      <button class="reader-btn" type="button" :disabled="!rendition" @click="prevPage">
        上一页
      </button>
      <button class="reader-btn" type="button" :disabled="!rendition" @click="nextPage">
        下一页
      </button>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getBook } from '@/data/books'
import { useUIStore } from '@/stores/ui'
import type { Book } from '@/types'
import type EpubBook from 'epubjs/types/book'
import type { NavItem } from 'epubjs/types/navigation'
import type Rendition from 'epubjs/types/rendition'

type ReadingMode = 'paginated' | 'scrolled'
type ReaderTheme = 'light' | 'night'

interface ReaderPreferences {
  mode: ReadingMode
  theme: ReaderTheme
  fontScale: number
}

interface ReaderLocation {
  start?: {
    cfi?: string
    href?: string
  }
  end?: {
    cfi?: string
    href?: string
  }
}

interface TocEntry {
  label: string
  href: string
  depth: number
}

interface ReaderAnchor {
  cfi?: string
  href?: string
}

const READER_PREFERENCES_KEY = 'starlit-blog.reader-preferences'
const defaultReaderPreferences: ReaderPreferences = {
  mode: 'paginated',
  theme: 'light',
  fontScale: 100,
}

const route = useRoute()
const router = useRouter()
const ui = useUIStore()
const viewerRef = ref<HTMLElement | null>(null)
const book = ref<Book | null>(null)
const loading = ref(true)
const error = ref('')
const isReaderBusy = ref(false)
const rendition = ref<Rendition | null>(null)
const viewerKey = ref(0)
const readingMode = ref<ReadingMode>(defaultReaderPreferences.mode)
const readerTheme = ref<ReaderTheme>(defaultReaderPreferences.theme)
const fontScale = ref(defaultReaderPreferences.fontScale)
const tocOpen = ref(false)
const tocItems = ref<TocEntry[]>([])
const activeTocHref = ref('')
let epubBook: EpubBook | null = null
let loadRunId = 0
let isUnmounted = false
let currentCfi: string | undefined
let currentHref: string | undefined

function isReadingMode(value: unknown): value is ReadingMode {
  return value === 'paginated' || value === 'scrolled'
}

function isReaderTheme(value: unknown): value is ReaderTheme {
  return value === 'light' || value === 'night'
}

function clampFontScale(value: unknown): number {
  if (typeof value !== 'number' || !Number.isFinite(value))
    return defaultReaderPreferences.fontScale
  return Math.min(130, Math.max(85, Math.round(value / 5) * 5))
}

function readReaderPreferences(): ReaderPreferences {
  try {
    const raw = localStorage.getItem(READER_PREFERENCES_KEY)
    if (!raw) return defaultReaderPreferences
    const parsed = JSON.parse(raw) as Partial<ReaderPreferences>
    return {
      mode: isReadingMode(parsed.mode) ? parsed.mode : defaultReaderPreferences.mode,
      theme: isReaderTheme(parsed.theme) ? parsed.theme : defaultReaderPreferences.theme,
      fontScale: clampFontScale(parsed.fontScale),
    }
  } catch (err) {
    console.warn('[books] 阅读偏好读取失败,使用默认设置:', err)
    return defaultReaderPreferences
  }
}

function saveReaderPreferences() {
  const preferences: ReaderPreferences = {
    mode: readingMode.value,
    theme: readerTheme.value,
    fontScale: fontScale.value,
  }
  localStorage.setItem(READER_PREFERENCES_KEY, JSON.stringify(preferences))
}

function restoreReaderPreferences() {
  const preferences = readReaderPreferences()
  readingMode.value = preferences.mode
  readerTheme.value = preferences.theme
  fontScale.value = preferences.fontScale
}

function waitForNextPaint(): Promise<void> {
  return new Promise((resolve) => {
    requestAnimationFrame(() => {
      requestAnimationFrame(() => resolve())
    })
  })
}

function isCurrentRun(runId: number): boolean {
  return !isUnmounted && runId === loadRunId
}

function getCurrentLocationCfi(): string | undefined {
  if (!rendition.value) return currentCfi
  const location = rendition.value.currentLocation() as ReaderLocation
  if (location.start?.cfi) return location.start.cfi
  return currentCfi
}

function getCurrentLocation(): ReaderLocation | null {
  if (!rendition.value) return null
  return rendition.value.currentLocation() as ReaderLocation
}

function getReaderAnchorForModeChange(from: ReadingMode, to: ReadingMode): ReaderAnchor {
  const location = getCurrentLocation()
  if (!location) return { cfi: currentCfi, href: currentHref }

  const anchorPoint =
    from === 'paginated' && to === 'scrolled' ? location.end || location.start : location.start
  currentCfi = anchorPoint?.cfi || currentCfi
  currentHref = anchorPoint?.href || currentHref
  return {
    cfi: anchorPoint?.cfi || currentCfi,
    href: anchorPoint?.href || currentHref,
  }
}

function getRenditionOptions() {
  if (readingMode.value === 'scrolled') {
    return {
      width: '100%',
      height: '100%',
      manager: 'default',
      flow: 'scrolled-doc',
      spread: 'none',
    }
  }

  return {
    width: '100%',
    height: '100%',
    manager: 'default',
    flow: 'paginated',
    spread: 'always',
    minSpreadWidth: 780,
  }
}

function applyReaderTheme() {
  if (!rendition.value) return
  const textColor = readerTheme.value === 'night' ? '#efe4cf' : '#2d2a24'
  rendition.value.themes.fontSize(`${fontScale.value}%`)
  rendition.value.themes.override('color', textColor)
  rendition.value.themes.override('background', 'transparent')
  rendition.value.themes.override('line-height', '1.78')
  rendition.value.themes.override('font-family', '"Noto Serif SC", "Songti SC", serif')
}

function flattenToc(items: NavItem[], depth = 0): TocEntry[] {
  return items.flatMap((item) => {
    const current = item.href && item.label ? [{ label: item.label, href: item.href, depth }] : []
    const children = item.subitems ? flattenToc(item.subitems, depth + 1) : []
    return [...current, ...children]
  })
}

function cleanupReader() {
  if (rendition.value) {
    rendition.value.destroy()
    rendition.value = null
  }
  if (epubBook) {
    epubBook.destroy()
    epubBook = null
  }
  if (viewerRef.value) viewerRef.value.replaceChildren()
}

async function displayReaderAnchor(anchor?: ReaderAnchor) {
  if (!rendition.value) return
  if (!anchor?.cfi && !anchor?.href) {
    await rendition.value.display()
    return
  }

  if (anchor.cfi) {
    try {
      await rendition.value.display(anchor.cfi)
      return
    } catch (err) {
      console.warn('[books] EPUB CFI 定位失败,尝试章节回退:', err)
    }
  }

  if (anchor.href) {
    try {
      await rendition.value.display(anchor.href)
      return
    } catch (err) {
      console.warn('[books] EPUB 章节定位失败,保持当前位置:', err)
      return
    }
  }
}

function goBack() {
  router.push('/books')
}

async function prevPage() {
  if (!rendition.value) return
  currentCfi = getCurrentLocationCfi()
  await rendition.value.prev()
}

async function nextPage() {
  if (!rendition.value) return
  currentCfi = getCurrentLocationCfi()
  await rendition.value.next()
}

async function changeReadingMode(mode: ReadingMode) {
  if (readingMode.value === mode || loading.value || isReaderBusy.value) return
  const anchor = getReaderAnchorForModeChange(readingMode.value, mode)
  tocOpen.value = false
  readingMode.value = mode
  saveReaderPreferences()
  await loadReader(anchor)
}

function toggleReaderTheme() {
  readerTheme.value = readerTheme.value === 'light' ? 'night' : 'light'
  saveReaderPreferences()
  applyReaderTheme()
}

function toggleToc() {
  if (tocItems.value.length === 0 || isReaderBusy.value) return
  tocOpen.value = !tocOpen.value
}

function normalizeTocHref(href: string): string {
  return href.split('#')[0]
}

function isTocItemActive(href: string): boolean {
  if (!activeTocHref.value) return false
  return (
    activeTocHref.value === href || normalizeTocHref(activeTocHref.value) === normalizeTocHref(href)
  )
}

async function displayTocItem(href: string) {
  if (!rendition.value || isReaderBusy.value) return
  isReaderBusy.value = true
  try {
    activeTocHref.value = href
    tocOpen.value = false
    await nextTick()
    await displayReaderAnchor({ href })
    currentCfi = getCurrentLocationCfi()
  } catch (err) {
    console.warn('[books] 目录跳转失败:', err)
  } finally {
    isReaderBusy.value = false
  }
}

function decreaseFontSize() {
  fontScale.value = Math.max(85, fontScale.value - 5)
  saveReaderPreferences()
  applyReaderTheme()
}

function increaseFontSize() {
  fontScale.value = Math.min(130, fontScale.value + 5)
  saveReaderPreferences()
  applyReaderTheme()
}

async function loadReader(anchor?: ReaderAnchor) {
  const runId = loadRunId + 1
  loadRunId = runId
  isReaderBusy.value = true
  loading.value = true
  error.value = ''

  const slug = String(route.params.slug || '')
  const currentBook = getBook(slug)
  if (!currentBook) {
    error.value = '图书不存在'
    loading.value = false
    isReaderBusy.value = false
    return
  }

  book.value = currentBook
  await nextTick()
  if (!viewerRef.value || !isCurrentRun(runId)) return

  try {
    cleanupReader()
    viewerKey.value += 1
    await nextTick()
    await waitForNextPaint()
    if (!viewerRef.value || !isCurrentRun(runId)) return

    const { default: ePub } = await import('epubjs')
    if (!isCurrentRun(runId)) return

    epubBook = ePub(currentBook.file)
    const navigation = await epubBook.loaded.navigation
    tocItems.value = flattenToc(navigation.toc)
    rendition.value = epubBook.renderTo(viewerRef.value, getRenditionOptions())
    applyReaderTheme()

    rendition.value.on('relocated', (location: ReaderLocation) => {
      if (location.start?.cfi) currentCfi = location.start.cfi
      if (location.start?.href) currentHref = location.start.href
      if (location.start?.href) activeTocHref.value = location.start.href
    })

    await displayReaderAnchor(anchor)
    if (!isCurrentRun(runId)) return
    loading.value = false
    isReaderBusy.value = false
  } catch (err) {
    if (!isCurrentRun(runId)) return
    console.warn('[books] EPUB 阅读器加载失败:', err)
    error.value = `无法打开 ${currentBook.file}`
    loading.value = false
    isReaderBusy.value = false
  }
}

onMounted(() => {
  restoreReaderPreferences()
  ui.showNavbar = false
  void loadReader()
})

onUnmounted(() => {
  isUnmounted = true
  loadRunId += 1
  ui.showNavbar = true
  cleanupReader()
})
</script>

<style scoped>
.reader-page {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  background: #d9e6ef;
  color: #2d2a24;
}

.reader-page--night {
  background: #202832;
  color: #efe4cf;
}

.reader-bg {
  position: fixed;
  inset: 0;
  background:
    radial-gradient(circle at 12% 12%, rgba(255, 255, 255, 0.72), transparent 28%),
    radial-gradient(circle at 88% 18%, rgba(159, 202, 228, 0.52), transparent 32%),
    linear-gradient(
      135deg,
      rgba(228, 241, 247, 0.96),
      rgba(241, 232, 211, 0.92) 54%,
      rgba(205, 226, 238, 0.94)
    );
}

.reader-page--night .reader-bg {
  background:
    radial-gradient(circle at 14% 12%, rgba(98, 125, 144, 0.46), transparent 30%),
    radial-gradient(circle at 88% 20%, rgba(172, 145, 112, 0.22), transparent 32%),
    linear-gradient(
      135deg,
      rgba(29, 38, 48, 0.98),
      rgba(42, 45, 47, 0.96) 55%,
      rgba(24, 34, 43, 0.98)
    );
}

.reader-ambient {
  position: fixed;
  border-radius: 999px;
  filter: blur(6px);
  opacity: 0.42;
  pointer-events: none;
}

.reader-ambient-one {
  top: 8rem;
  left: 7vw;
  width: 18rem;
  height: 18rem;
  background: rgba(255, 255, 255, 0.45);
}

.reader-ambient-two {
  right: 8vw;
  bottom: 8vh;
  width: 22rem;
  height: 22rem;
  background: rgba(146, 190, 216, 0.34);
}

.reader-page--night .reader-ambient-one {
  background: rgba(118, 144, 162, 0.22);
}

.reader-page--night .reader-ambient-two {
  background: rgba(172, 145, 112, 0.2);
}

.reader-toolbar {
  position: fixed;
  top: 1rem;
  left: 1rem;
  right: 1rem;
  z-index: 30;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 1rem;
  align-items: center;
  border: 1px solid rgba(255, 255, 255, 0.62);
  border-radius: 1.35rem;
  background: rgba(255, 255, 255, 0.42);
  backdrop-filter: blur(22px) saturate(1.18);
  -webkit-backdrop-filter: blur(22px) saturate(1.18);
  padding: 0.72rem 0.85rem;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.66),
    0 18px 44px rgba(85, 109, 124, 0.2);
}

.reader-page--night .reader-toolbar,
.reader-page--night .toc-panel {
  border-color: rgba(255, 244, 221, 0.14);
  background: rgba(34, 42, 49, 0.62);
  box-shadow:
    inset 0 1px 0 rgba(255, 244, 221, 0.1),
    0 18px 44px rgba(0, 0, 0, 0.28);
}

.reader-back,
.reader-btn,
.reader-icon-btn,
.mode-btn {
  border: 1px solid rgba(92, 108, 116, 0.16);
  color: rgba(45, 42, 36, 0.82);
  cursor: pointer;
  font-size: 0.82rem;
  transition:
    background 0.2s ease,
    border-color 0.2s ease,
    color 0.2s ease,
    transform 0.2s ease;
}

.reader-back,
.reader-btn,
.reader-icon-btn {
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.45);
  padding: 0.52rem 0.86rem;
}

.reader-page--night .reader-back,
.reader-page--night .reader-btn,
.reader-page--night .reader-icon-btn,
.reader-page--night .mode-btn {
  border-color: rgba(255, 244, 221, 0.14);
  color: rgba(239, 228, 207, 0.82);
}

.reader-page--night .reader-back,
.reader-page--night .reader-btn,
.reader-page--night .reader-icon-btn,
.reader-page--night .mode-switch,
.reader-page--night .font-control {
  background: rgba(255, 244, 221, 0.08);
}

.reader-back:hover,
.reader-btn:hover:not(:disabled),
.reader-icon-btn:hover:not(:disabled),
.mode-btn:hover:not(:disabled) {
  border-color: rgba(76, 106, 126, 0.24);
  background: rgba(255, 255, 255, 0.68);
  color: rgba(28, 29, 27, 0.96);
}

.reader-page--night .reader-back:hover,
.reader-page--night .reader-btn:hover:not(:disabled),
.reader-page--night .reader-icon-btn:hover:not(:disabled),
.reader-page--night .mode-btn:hover:not(:disabled) {
  border-color: rgba(255, 244, 221, 0.24);
  background: rgba(255, 244, 221, 0.14);
  color: rgba(255, 246, 228, 0.96);
}

.reader-title-wrap {
  min-width: 0;
  text-align: center;
}

.reader-kicker {
  color: rgba(68, 92, 108, 0.54);
  font-size: 0.66rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.reader-page--night .reader-kicker,
.reader-page--night .font-scale,
.reader-page--night .toc-head p {
  color: rgba(239, 228, 207, 0.58);
}

.reader-title {
  overflow: hidden;
  margin-top: 0.08rem;
  color: rgba(37, 35, 30, 0.92);
  font-size: 1rem;
  font-weight: 700;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.reader-page--night .reader-title {
  color: rgba(247, 236, 216, 0.94);
}

.reader-author {
  margin-top: 0.08rem;
  overflow: hidden;
  color: rgba(48, 52, 51, 0.52);
  font-size: 0.74rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.reader-page--night .reader-author {
  color: rgba(239, 228, 207, 0.52);
}

.reader-controls {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 0.55rem;
}

.mode-switch,
.font-control {
  display: flex;
  align-items: center;
  border: 1px solid rgba(92, 108, 116, 0.14);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.34);
  padding: 0.18rem;
}

.mode-btn {
  border-radius: 999px;
  background: transparent;
  padding: 0.4rem 0.72rem;
}

.mode-btn-active {
  background: rgba(255, 255, 255, 0.78);
  color: rgba(32, 32, 28, 0.95);
  box-shadow: 0 6px 16px rgba(91, 111, 124, 0.14);
}

.reader-page--night .mode-btn-active {
  background: rgba(239, 228, 207, 0.18);
  color: rgba(255, 246, 228, 0.96);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.18);
}

.font-control {
  gap: 0.28rem;
}

.reader-icon-btn {
  min-width: 2.4rem;
  padding: 0.38rem 0.58rem;
}

.font-scale {
  min-width: 3.4rem;
  color: rgba(45, 42, 36, 0.68);
  font-size: 0.78rem;
  text-align: center;
}

.reader-main {
  position: relative;
  z-index: 10;
  width: 100vw;
  height: 100vh;
  padding: 6.25rem clamp(1rem, 3vw, 3rem) 4.4rem;
}

.toc-panel {
  position: absolute;
  top: 6.25rem;
  left: clamp(1rem, 3vw, 3rem);
  bottom: 4.4rem;
  z-index: 34;
  display: none;
  width: min(18.5rem, calc(100vw - 2rem));
  min-height: 0;
  overflow: auto;
  border: 1px solid rgba(255, 255, 255, 0.62);
  border-radius: 1.35rem;
  background: rgba(255, 255, 255, 0.32);
  backdrop-filter: blur(22px) saturate(1.14);
  -webkit-backdrop-filter: blur(22px) saturate(1.14);
  padding: 0.8rem;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.56),
    0 18px 44px rgba(85, 109, 124, 0.16);
}

.toc-panel-open {
  display: block;
}

.toc-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.toc-head p {
  color: rgba(68, 92, 108, 0.62);
  font-size: 0.68rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.toc-close {
  padding: 0.34rem 0.64rem;
}

.toc-empty {
  padding: 1.2rem 0.4rem;
  color: rgba(48, 52, 51, 0.46);
  font-size: 0.84rem;
}

.toc-item {
  display: block;
  width: 100%;
  border: 0;
  border-radius: 0.78rem;
  background: transparent;
  color: rgba(45, 42, 36, 0.72);
  cursor: pointer;
  font-size: 0.86rem;
  line-height: 1.45;
  margin-bottom: 0.2rem;
  padding: 0.56rem 0.62rem 0.56rem calc(0.62rem + var(--toc-depth) * 0.85rem);
  text-align: left;
  transition:
    background 0.2s ease,
    color 0.2s ease;
}

.toc-item:hover,
.toc-item-active {
  background: rgba(255, 255, 255, 0.45);
  color: rgba(32, 32, 28, 0.94);
}

.reader-page--night .toc-empty,
.reader-page--night .toc-item {
  color: rgba(239, 228, 207, 0.7);
}

.reader-page--night .toc-item:hover,
.reader-page--night .toc-item-active {
  background: rgba(239, 228, 207, 0.12);
  color: rgba(255, 246, 228, 0.94);
}

.book-stage {
  position: relative;
  display: grid;
  align-items: stretch;
  width: min(100%, 74rem);
  height: 100%;
  margin: 0 auto;
}

.reader-page--scrolled .book-stage {
  width: min(100%, 52rem);
}

.paper-shell {
  position: relative;
  min-height: 0;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.72);
  border-radius: 1.65rem;
  background:
    linear-gradient(
      90deg,
      rgba(215, 197, 162, 0.26),
      transparent 7%,
      transparent 93%,
      rgba(214, 197, 162, 0.2)
    ),
    linear-gradient(180deg, #f8f1e2, #f1e6d1);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.9),
    inset 18px 0 34px rgba(120, 93, 52, 0.08),
    inset -18px 0 34px rgba(120, 93, 52, 0.06),
    0 26px 70px rgba(88, 102, 112, 0.28);
}

.reader-page--night .paper-shell {
  border-color: rgba(255, 244, 221, 0.16);
  background:
    linear-gradient(
      90deg,
      rgba(20, 18, 15, 0.24),
      transparent 7%,
      transparent 93%,
      rgba(20, 18, 15, 0.2)
    ),
    linear-gradient(180deg, #3a342c, #2f2b26);
  box-shadow:
    inset 0 1px 0 rgba(255, 244, 221, 0.1),
    inset 18px 0 34px rgba(0, 0, 0, 0.16),
    inset -18px 0 34px rgba(0, 0, 0, 0.12),
    0 26px 70px rgba(0, 0, 0, 0.34);
}

.paper-shell::before {
  content: '';
  position: absolute;
  top: 1.2rem;
  bottom: 1.2rem;
  left: 50%;
  z-index: 2;
  width: 1px;
  background: linear-gradient(180deg, transparent, rgba(125, 100, 64, 0.16), transparent);
  opacity: 0.5;
  pointer-events: none;
}

.reader-page--night .paper-shell::before {
  background: linear-gradient(180deg, transparent, rgba(255, 244, 221, 0.12), transparent);
}

.reader-page--scrolled .paper-shell::before {
  display: none;
}

.reader-viewer {
  position: relative;
  z-index: 1;
  width: 100%;
  height: 100%;
  overflow: hidden;
  padding: clamp(1.1rem, 2.4vw, 2rem);
}

.reader-page--scrolled .reader-viewer {
  overflow: hidden;
}

.reader-viewer-hidden {
  visibility: hidden;
}

.reader-state {
  position: absolute;
  inset: 0;
  z-index: 4;
  display: grid;
  place-items: center;
  padding: 2rem;
  color: rgba(59, 52, 42, 0.68);
  text-align: center;
}

.reader-page--night .reader-state {
  color: rgba(239, 228, 207, 0.7);
}

.reader-state-error {
  color: rgba(130, 54, 45, 0.86);
}

.reader-page--night .reader-state-error {
  color: rgba(255, 187, 166, 0.88);
}

.reader-hint {
  margin-top: 0.55rem;
  color: rgba(64, 58, 48, 0.48);
  font-size: 0.82rem;
}

.reader-page--night .reader-hint {
  color: rgba(239, 228, 207, 0.46);
}

.page-turn {
  position: absolute;
  top: 0;
  bottom: 0;
  z-index: 12;
  width: min(8vw, 5.5rem);
  border: 0;
  background: transparent;
  color: rgba(74, 64, 50, 0.24);
  cursor: pointer;
  font-size: clamp(2rem, 6vw, 5rem);
  transition:
    color 0.2s ease,
    background 0.2s ease;
}

.reader-page--night .page-turn {
  color: rgba(239, 228, 207, 0.24);
}

.page-turn span {
  display: inline-block;
  transform: translateY(-0.06em);
}

.page-turn-prev {
  left: 0;
}

.page-turn-next {
  right: 0;
}

.page-turn:hover {
  background: linear-gradient(90deg, rgba(255, 255, 255, 0.24), transparent);
  color: rgba(74, 64, 50, 0.48);
}

.reader-page--night .page-turn:hover {
  background: linear-gradient(90deg, rgba(239, 228, 207, 0.1), transparent);
  color: rgba(239, 228, 207, 0.5);
}

.page-turn-next:hover {
  background: linear-gradient(270deg, rgba(255, 255, 255, 0.24), transparent);
}

.reader-page--night .page-turn-next:hover {
  background: linear-gradient(270deg, rgba(239, 228, 207, 0.1), transparent);
}

.reader-footer {
  position: fixed;
  left: 50%;
  bottom: 1rem;
  z-index: 24;
  display: none;
  gap: 0.65rem;
  transform: translateX(-50%);
}

.reader-btn:disabled,
.reader-icon-btn:disabled,
.mode-btn:disabled {
  cursor: not-allowed;
  opacity: 0.48;
}

@media (max-width: 860px) {
  .reader-page--toc-open .reader-main {
    display: block;
  }

  .toc-panel {
    position: fixed;
    top: 10.7rem;
    left: 0.75rem;
    right: 0.75rem;
    width: auto;
    bottom: 4.6rem;
  }

  .reader-toolbar {
    grid-template-columns: 1fr;
    gap: 0.62rem;
    align-items: stretch;
  }

  .reader-back {
    justify-self: start;
  }

  .reader-title-wrap {
    text-align: left;
  }

  .reader-controls {
    justify-content: flex-start;
  }

  .reader-main {
    padding-top: 11.5rem;
  }
}

@media (max-width: 640px) {
  .reader-toolbar {
    left: 0.75rem;
    right: 0.75rem;
    border-radius: 1.1rem;
  }

  .reader-main {
    padding: 12rem 0.75rem 4.7rem;
  }

  .toc-panel {
    top: 11.2rem;
  }

  .paper-shell {
    border-radius: 1.15rem;
  }

  .paper-shell::before,
  .page-turn {
    display: none;
  }

  .reader-footer {
    display: flex;
  }

  .reader-viewer {
    padding: 0.85rem;
  }
}
</style>
