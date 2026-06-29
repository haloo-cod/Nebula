<template>
  <div class="reader-page">
    <div class="reader-bg"></div>

    <header class="reader-toolbar">
      <button class="reader-back" type="button" @click="goBack">返回书架</button>
      <div class="reader-title-wrap">
        <h1 class="reader-title">{{ book?.title || '图书阅读器' }}</h1>
        <p v-if="book?.author" class="reader-author">{{ book.author }}</p>
      </div>
      <div class="reader-actions">
        <button class="reader-btn" type="button" :disabled="loading || !rendition" @click="prevPage">上一页</button>
        <button class="reader-btn" type="button" :disabled="loading || !rendition" @click="nextPage">下一页</button>
      </div>
    </header>

    <main class="reader-main">
      <div v-if="loading" class="reader-state">正在加载 EPUB...</div>
      <div v-else-if="error" class="reader-state reader-state-error">
        <p>{{ error }}</p>
        <p class="reader-hint">请确认测试文件已放在 public/books/ 对应路径下。</p>
      </div>
      <div ref="viewerRef" class="reader-viewer" :class="{ 'reader-viewer-hidden': loading || error }"></div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ePub, { type Book as EpubBook, type Rendition } from 'epubjs'
import { getHydratedBook } from '@/data/books'
import { useUIStore } from '@/stores/ui'
import type { Book } from '@/types'

const route = useRoute()
const router = useRouter()
const ui = useUIStore()
const viewerRef = ref<HTMLElement | null>(null)
const book = ref<Book | null>(null)
const loading = ref(true)
const error = ref('')
const rendition = ref<Rendition | null>(null)
let epubBook: EpubBook | null = null

function goBack() {
  router.push('/books')
}

async function prevPage() {
  if (!rendition.value) return
  await rendition.value.prev()
}

async function nextPage() {
  if (!rendition.value) return
  await rendition.value.next()
}

async function loadReader() {
  const slug = String(route.params.slug || '')
  const currentBook = await getHydratedBook(slug)
  if (!currentBook) {
    error.value = '图书不存在'
    loading.value = false
    return
  }

  book.value = currentBook
  if (!viewerRef.value) return

  try {
    epubBook = ePub(currentBook.file)
    rendition.value = epubBook.renderTo(viewerRef.value, {
      width: '100%',
      height: '100%',
      flow: 'paginated',
      spread: 'none',
    })
    await rendition.value.display()
  } catch (err) {
    console.warn('[books] EPUB 阅读器加载失败:', err)
    error.value = `无法打开 ${currentBook.file}`
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  ui.showNavbar = false
  void loadReader()
})

onUnmounted(() => {
  ui.showNavbar = true
  if (rendition.value) rendition.value.destroy()
  if (epubBook) epubBook.destroy()
})
</script>

<style scoped>
.reader-page {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  background: #080b12;
}

.reader-bg {
  position: fixed;
  inset: 0;
  background:
    radial-gradient(circle at 18% 16%, rgba(115, 175, 255, 0.16), transparent 34%),
    radial-gradient(circle at 82% 14%, rgba(170, 125, 255, 0.12), transparent 30%),
    linear-gradient(180deg, rgba(8, 11, 18, 0.98), rgba(14, 18, 28, 0.96));
}

.reader-toolbar {
  position: fixed;
  top: 1rem;
  left: 1rem;
  right: 1rem;
  z-index: 20;
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 1rem;
  align-items: center;
  border-radius: 1.2rem;
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(15, 20, 34, 0.62);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  padding: 0.7rem 0.8rem;
  box-shadow: 0 16px 38px rgba(0, 0, 0, 0.28);
}

.reader-back,
.reader-btn {
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.86);
  cursor: pointer;
  font-size: 0.82rem;
  padding: 0.55rem 0.9rem;
  transition:
    background 0.2s ease,
    color 0.2s ease;
}

.reader-back:hover,
.reader-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.16);
  color: #fff;
}

.reader-btn:disabled {
  cursor: not-allowed;
  opacity: 0.45;
}

.reader-title-wrap {
  min-width: 0;
  text-align: center;
}

.reader-title {
  overflow: hidden;
  color: rgba(255, 255, 255, 0.94);
  font-size: 0.98rem;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.reader-author {
  margin-top: 0.15rem;
  overflow: hidden;
  color: rgba(255, 255, 255, 0.48);
  font-size: 0.74rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.reader-actions {
  display: flex;
  gap: 0.5rem;
}

.reader-main {
  position: relative;
  z-index: 10;
  width: 100vw;
  height: 100vh;
  padding: 5.4rem 1rem 1rem;
}

.reader-viewer {
  width: 100%;
  height: 100%;
  overflow: hidden;
  border-radius: 1.2rem;
  background: rgba(242, 238, 225, 0.96);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.36);
}

.reader-viewer-hidden {
  visibility: hidden;
}

.reader-state {
  position: absolute;
  inset: 5.4rem 1rem 1rem;
  display: grid;
  place-items: center;
  border-radius: 1.2rem;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.72);
  text-align: center;
}

.reader-state-error {
  color: rgba(255, 220, 220, 0.88);
}

.reader-hint {
  margin-top: 0.55rem;
  color: rgba(255, 255, 255, 0.46);
  font-size: 0.82rem;
}

@media (max-width: 767px) {
  .reader-toolbar {
    grid-template-columns: 1fr;
    gap: 0.55rem;
  }

  .reader-actions {
    justify-content: center;
  }

  .reader-main {
    padding-top: 8.2rem;
  }

  .reader-state {
    inset: 8.2rem 1rem 1rem;
  }
}
</style>
