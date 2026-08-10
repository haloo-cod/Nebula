<template>
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

      <div class="books-sort" role="group" aria-label="图书排序">
        <span class="books-sort-label">排序</span>
        <button
          v-for="option in [
            { value: 'newest' as BookSort, label: '最新上传' },
            { value: 'oldest' as BookSort, label: '最早上传' },
            { value: 'custom' as BookSort, label: '自定义排序' },
          ]"
          :key="option.value"
          type="button"
          class="books-sort-option"
          :class="{ active: sortMode === option.value }"
          @click="sortMode = option.value"
        >
          {{ option.label }}
        </button>
      </div>

      <div class="books-grid">
        <RouterLink
          v-for="book in books"
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
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="PAGE_SIZE"
          :total="totalBooks"
          :pager-count="5"
          background
          layout="prev, pager, next"
        />
      </div>
    </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import PanelFallbackGlass from '@/components/panels/PanelFallbackGlass.vue'
import LiquidGlass from '@/components/liquid-glass/LiquidGlass.vue'
import { getBooks } from '@/data/books'
import { fetchBooks, type BookSort } from '@/api/books'
import { siteText } from '@/data/site-text'
import { useUIStore } from '@/stores/ui'
import type { Book } from '@/types'

const ui = useUIStore()
const PAGE_SIZE = 16
const books = ref<Book[]>([])
const totalBooks = ref(0)
const currentPage = ref(1)
const searchQuery = ref('')
const sortMode = ref<BookSort>('newest')
const loading = ref(false)

// 后端分页：从 API 获取当前页数据
async function loadBooks() {
  loading.value = true
  try {
    const resp = await fetchBooks(currentPage.value, PAGE_SIZE, searchQuery.value, sortMode.value)
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
    if (sortMode.value === 'newest') {
      filtered.sort((a, b) => b.slug.localeCompare(a.slug))
    } else if (sortMode.value === 'oldest') {
      filtered.sort((a, b) => a.slug.localeCompare(b.slug))
    }
    totalBooks.value = filtered.length
    const start = (currentPage.value - 1) * PAGE_SIZE
    books.value = filtered.slice(start, start + PAGE_SIZE)
  } finally {
    loading.value = false
  }
}

const totalPages = computed(() => Math.max(1, Math.ceil(totalBooks.value / PAGE_SIZE)))

function getCoverStyle(book: Book) {
  if (!book.cover) return {}
  return { backgroundImage: `url(${book.cover})` }
}

function getPlaceholderLabel(title: string): string {
  return title.slice(0, 2)
}

// 页码变化时重新加载
watch(currentPage, () => {
  loadBooks()
})

watch(sortMode, () => {
  currentPage.value = 1
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

.books-sort {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.45rem;
  margin: -0.7rem 0 1.4rem;
}

.books-sort-label {
  color: var(--text-muted);
  font-size: 0.78rem;
}

.books-sort-option {
  padding: 0.35rem 0.72rem;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 0.75rem;
}

.books-sort-option.active {
  border-color: rgba(145, 196, 255, 0.42);
  background: rgba(110, 165, 255, 0.2);
  color: var(--text-primary);
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
  justify-content: center;
  margin-top: 2rem;
}

.books-pagination :deep(.el-pagination) {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.books-pagination :deep(.el-pager) {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.books-pagination :deep(.el-pagination button),
.books-pagination :deep(.el-pager li) {
  min-width: 2.4rem !important;
  height: auto !important;
  min-height: unset !important;
  border: 1px solid rgba(255, 255, 255, 0.14) !important;
  border-radius: 999px !important;
  background: rgba(255, 255, 255, 0.08) !important;
  color: var(--text-primary) !important;
  font-size: 0.82rem !important;
  font-weight: 400 !important;
  padding: 0.4rem 0.75rem !important;
  box-shadow: none !important;
  line-height: 1 !important;
  margin: 0 !important;
}

.books-pagination :deep(.el-pagination button:hover:not(:disabled)),
.books-pagination :deep(.el-pager li:hover:not(.is-active)) {
  background: rgba(255, 255, 255, 0.14) !important;
  color: var(--text-primary) !important;
}

.books-pagination :deep(.el-pagination button:disabled) {
  opacity: 0.38 !important;
  cursor: not-allowed !important;
  background: rgba(255, 255, 255, 0.05) !important;
}

.books-pagination :deep(.el-pager li.is-active) {
  border-color: rgba(145, 196, 255, 0.42) !important;
  background: rgba(110, 165, 255, 0.22) !important;
  color: #fff !important;
}

.books-pagination :deep(.el-pagination button.is-active) {
  background: transparent !important;
  color: var(--text-primary) !important;
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
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow:
    0 8px 28px rgba(0, 0, 0, 0.18),
    inset 0 1px 0 rgba(255, 255, 255, 0.24),
    inset 0 0 20px rgba(255, 255, 255, 0.06);
  transition:
    transform 0.24s ease,
    box-shadow 0.24s ease,
    border-color 0.24s ease;
}

@media (hover: hover) and (pointer: fine) {
  .book-link:hover .book-glass,
  .book-link:hover .book-card {
    transform: translateY(-3px);
    filter: drop-shadow(0 8px 24px rgba(80, 140, 255, 0.14));
  }
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
