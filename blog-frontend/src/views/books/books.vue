<template>
  <PageBackground>
    <div class="books-page">
      <div class="books-header">
        <p class="books-kicker">{{ siteText.books.kicker }}</p>
        <h1 class="books-title">{{ siteText.books.title }}</h1>
        <p class="books-desc">{{ siteText.books.subtitle }}</p>
      </div>

      <!-- 搜索栏（UI 占位，未来接后端搜索） -->
      <div class="books-search">
        <span class="books-search-icon">
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.3-4.3" />
          </svg>
        </span>
        <input
          v-model="searchQuery"
          class="books-search-input"
          type="text"
          placeholder="搜索书名或作者..."
        />
      </div>

      <div class="books-grid">
        <RouterLink
          v-for="book in visibleBooks"
          :key="book.slug"
          :to="`/books/read/${book.slug}`"
          class="book-link"
        >
          <LiquidGlass
            v-if="ui.liquidGlassEnabled"
            :cornerRadius="18"
            :theme="ui.theme"
            :blur-radius="ui.liquidGlassBlur"
            :ripple-trail="true"
            class="book-glass"
          >
            <article class="book-card book-card--liquid">
              <div class="book-cover" :style="getCoverStyle(book)">
                <span v-if="!book.cover" class="book-cover-placeholder">{{
                  getPlaceholderLabel(book.title)
                }}</span>
              </div>
              <div class="book-info">
                <h2 class="book-name">{{ book.title }}</h2>
                <p class="book-author">{{ book.author || '作者信息待补充' }}</p>
              </div>
            </article>
          </LiquidGlass>

          <PanelFallbackGlass v-else tag="article" class="book-card book-card-fallback">
            <div class="book-cover" :style="getCoverStyle(book)">
              <span v-if="!book.cover" class="book-cover-placeholder">{{
                getPlaceholderLabel(book.title)
              }}</span>
            </div>
            <div class="book-info">
              <h2 class="book-name">{{ book.title }}</h2>
              <p class="book-author">{{ book.author || '作者信息待补充' }}</p>
            </div>
          </PanelFallbackGlass>
        </RouterLink>
      </div>

      <div v-if="totalPages > 1" class="books-pagination">
        <button class="page-btn" type="button" :disabled="currentPage === 1" @click="goPrevPage">
          上一页
        </button>
        <button
          v-for="page in pageNumbers"
          :key="page"
          class="page-btn"
          :class="{ 'page-btn-active': page === currentPage }"
          type="button"
          @click="currentPage = page"
        >
          {{ page }}
        </button>
        <button
          class="page-btn"
          type="button"
          :disabled="currentPage === totalPages"
          @click="goNextPage"
        >
          下一页
        </button>
      </div>
    </div>
  </PageBackground>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import PageBackground from '@/components/PageBackground.vue'
import PanelFallbackGlass from '@/components/panels/PanelFallbackGlass.vue'
import LiquidGlass from '@/components/liquid-glass/LiquidGlass.vue'
import { getBooks } from '@/data/books'
import { fetchBooks } from '@/api/books'
import { siteText } from '@/data/site-text'
import { useUIStore } from '@/stores/ui'
import type { Book } from '@/types'

const ui = useUIStore()
const PAGE_SIZE = 16
const books = ref<Book[]>([])
const totalBooks = ref(0)
const currentPage = ref(1)
const searchQuery = ref('')
const loading = ref(false)

// 后端分页：从 API 获取当前页数据
async function loadBooks() {
  loading.value = true
  try {
    const resp = await fetchBooks(currentPage.value, PAGE_SIZE, searchQuery.value)
    books.value = resp.items
    totalBooks.value = resp.total
  } catch {
    // API 失败时 fallback 到本地数据（前端过滤+分页）
    const allBooks = getBooks()
    const q = searchQuery.value.trim().toLowerCase()
    const filtered = q
      ? allBooks.filter(
          (b) => b.title.toLowerCase().includes(q) || b.author.toLowerCase().includes(q),
        )
      : allBooks
    totalBooks.value = filtered.length
    const start = (currentPage.value - 1) * PAGE_SIZE
    books.value = filtered.slice(start, start + PAGE_SIZE)
  } finally {
    loading.value = false
  }
}

const totalPages = computed(() => Math.max(1, Math.ceil(totalBooks.value / PAGE_SIZE)))

const visibleBooks = computed(() => books.value)

const pageNumbers = computed(() =>
  Array.from({ length: totalPages.value }, (_, index) => index + 1),
)

function getCoverStyle(book: Book) {
  if (!book.cover) return {}
  return { backgroundImage: `url(${book.cover})` }
}

function getPlaceholderLabel(title: string): string {
  return title.slice(0, 2)
}

function goPrevPage() {
  if (currentPage.value <= 1) return
  currentPage.value -= 1
}

function goNextPage() {
  if (currentPage.value >= totalPages.value) return
  currentPage.value += 1
}

// 页码变化时重新加载
watch(currentPage, () => {
  loadBooks()
})

// 搜索关键词变化时 debounce 300ms 后加载
let searchTimer: ReturnType<typeof setTimeout> | null = null
watch(searchQuery, () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    currentPage.value = 1
    loadBooks()
  }, 300)
})

// 首次加载
onMounted(() => {
  loadBooks()
})
</script>

<style scoped>
.books-page {
  position: relative;
  z-index: 10;
  width: min(100%, 78rem);
  margin: 0 auto;
  padding: 7rem 1rem 4rem;
}

.books-header {
  margin-bottom: 1.8rem;
}

/* ===== 搜索栏 ===== */
.books-search {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  max-width: 22rem;
  margin-bottom: 1.4rem;
  padding: 0.55rem 1rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  transition:
    border-color 0.2s ease,
    background 0.2s ease;
}

.books-search:focus-within {
  border-color: rgba(145, 196, 255, 0.42);
  background: rgba(255, 255, 255, 0.1);
}

.books-search-icon {
  display: flex;
  align-items: center;
  color: var(--text-muted);
  flex-shrink: 0;
}

.books-search-input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  color: var(--text-primary);
  font-size: 0.85rem;
  line-height: 1.4;
}

.books-search-input::placeholder {
  color: var(--text-muted);
}

.books-kicker {
  margin-bottom: 0.3rem;
  color: rgba(170, 215, 255, 0.74);
  font-size: 0.72rem;
  letter-spacing: 0.2em;
  text-transform: uppercase;
}

.books-title {
  color: var(--text-primary);
  font-size: clamp(1.7rem, 3vw, 2.6rem);
  font-weight: 700;
  letter-spacing: 0.08em;
}

.books-desc {
  margin-top: 0.5rem;
  color: var(--text-secondary);
  font-size: 0.9rem;
  line-height: 1.7;
}

.books-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1rem;
}

.books-pagination {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.65rem;
  margin-top: 1.6rem;
}

.page-btn {
  min-width: 2.7rem;
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  color: var(--text-primary);
  cursor: pointer;
  font-size: 0.82rem;
  padding: 0.52rem 0.9rem;
  transition:
    background 0.2s ease,
    color 0.2s ease,
    border-color 0.2s ease;
}

.page-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.14);
  color: var(--text-primary);
}

.page-btn:disabled {
  cursor: not-allowed;
  opacity: 0.38;
}

.page-btn-active {
  border-color: rgba(145, 196, 255, 0.42);
  background: rgba(110, 165, 255, 0.22);
  color: #fff;
}

.book-link {
  display: block;
  aspect-ratio: 1 / 1.8;
  color: inherit;
  text-decoration: none;
}

.book-glass {
  width: 100%;
  height: 100%;
  transition:
    transform 0.24s ease,
    filter 0.24s ease;
}

.book-card {
  display: flex;
  height: 100%;
  flex-direction: column;
  border-radius: 1.15rem;
  padding: 0.45rem;
}

.book-card--liquid {
  border: none;
  background: transparent;
  backdrop-filter: none;
  -webkit-backdrop-filter: none;
  box-shadow: none;
}

.book-card-fallback {
  transition:
    transform 0.24s ease,
    box-shadow 0.24s ease,
    border-color 0.24s ease;
}

.book-link:hover .book-glass {
  transform: translateY(-5px);
  filter: drop-shadow(0 16px 34px rgba(80, 140, 255, 0.18));
}

.book-link:hover .book-card {
  transform: translateY(-5px);
}

.book-link:hover .book-card-fallback {
  border-color: rgba(140, 185, 255, 0.24);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.16),
    0 16px 34px rgba(80, 140, 255, 0.18);
}

.book-cover {
  position: relative;
  width: 100%;
  aspect-ratio: 1 / 1.6;
  overflow: hidden;
  border-radius: 0.9rem;
  box-sizing: border-box;
  padding: 0 0.3rem;
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
  background-origin: content-box;
  background-clip: content-box;
}

.book-cover::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.book-cover-placeholder {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  color: var(--text-primary);
  font-size: 2rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-shadow: 0 8px 26px rgba(0, 0, 0, 0.42);
}

.book-info {
  display: flex;
  min-width: 0;
  flex-direction: column;
  justify-content: flex-start;
  flex: 1;
  padding: 0.42rem 0.18rem 0.12rem 0.3rem;
}

.book-name {
  overflow: hidden;
  color: var(--text-primary);
  font-size: 1rem;
  font-weight: 700;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
}

.book-author {
  margin-top: 0.16rem;
  overflow: hidden;
  color: var(--text-secondary);
  font-size: 0.86rem;
  line-height: 1.5;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 1023px) {
  .books-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 767px) {
  .books-page {
    padding-top: 6rem;
  }

  .books-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 0.6rem;
  }

  .book-card {
    min-height: auto;
    padding: 0.3rem;
  }

  .book-glass {
    aspect-ratio: auto;
  }

  .book-link {
    aspect-ratio: 1 / 1.6;
  }

  .book-cover {
    aspect-ratio: 1 / 1.3;
    border-radius: 0.6rem;
  }

  .book-name {
    font-size: 0.82rem;
    -webkit-line-clamp: 2;
  }

  .book-author {
    font-size: 0.72rem;
  }

  .book-info {
    padding: 0.3rem 0.1rem 0.1rem 0.2rem;
  }
}
</style>
