<template>
  <PageBackground>
    <div class="books-page">
      <div class="books-header">
        <p class="books-kicker">Library</p>
        <h1 class="books-title">图书</h1>
        <p class="books-desc">一块一块的玻璃书格。点击任意图书后进入全屏 EPUB 阅读器。</p>
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
            class="book-glass"
          >
            <article class="book-card">
              <div class="book-cover" :style="getCoverStyle(book)">
                <span v-if="!book.cover" class="book-cover-placeholder">{{ book.title.slice(0, 1) }}</span>
              </div>
              <div class="book-info">
                <h2 class="book-name">{{ book.title }}</h2>
                <p class="book-author">{{ book.author }}</p>
              </div>
            </article>
          </LiquidGlass>

          <article v-else class="book-card book-card-fallback">
            <div class="book-cover" :style="getCoverStyle(book)">
              <span v-if="!book.cover" class="book-cover-placeholder">{{ book.title.slice(0, 1) }}</span>
            </div>
            <div class="book-info">
              <h2 class="book-name">{{ book.title }}</h2>
              <p class="book-author">{{ book.author }}</p>
            </div>
          </article>
        </RouterLink>
      </div>
    </div>
  </PageBackground>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import PageBackground from '@/components/PageBackground.vue'
import LiquidGlass from '@/components/LiquidGlass.vue'
import { extractBookMeta, getBooks } from '@/data/books'
import { useUIStore } from '@/stores/ui'
import type { Book } from '@/types'

const ui = useUIStore()
const books = ref<Book[]>(getBooks())

function getCoverStyle(book: Book) {
  if (!book.cover) return {}
  return { backgroundImage: `url(${book.cover})` }
}

onMounted(() => {
  void Promise.all(
    books.value.map(async (book) => {
      const extracted = await extractBookMeta(book)
      return {
        ...book,
        author: book.author || extracted.author || '',
        cover: book.cover || extracted.cover || '',
        description: book.description || extracted.description || '',
      }
    }),
  ).then((hydratedBooks) => {
    books.value = hydratedBooks
  })
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

.books-kicker {
  margin-bottom: 0.3rem;
  color: rgba(170, 215, 255, 0.74);
  font-size: 0.72rem;
  letter-spacing: 0.2em;
  text-transform: uppercase;
}

.books-title {
  color: rgba(255, 255, 255, 0.94);
  font-size: clamp(1.7rem, 3vw, 2.6rem);
  font-weight: 700;
  letter-spacing: 0.08em;
}

.books-desc {
  margin-top: 0.5rem;
  color: rgba(255, 255, 255, 0.52);
  font-size: 0.9rem;
  line-height: 1.7;
}

.books-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1rem;
}

.book-link {
  min-height: 18.5rem;
  color: inherit;
  text-decoration: none;
}

.book-glass {
  width: 100%;
  height: 100%;
  min-height: 18.5rem;
  transition:
    transform 0.24s ease,
    filter 0.24s ease;
}

.book-link:hover .book-glass {
  transform: translateY(-5px);
  filter: drop-shadow(0 16px 34px rgba(80, 140, 255, 0.18));
}

.book-card {
  display: flex;
  height: 100%;
  min-height: 18.5rem;
  flex-direction: column;
  padding: 0.9rem;
}

.book-card-fallback {
  border-radius: 18px;
  border: 1px solid rgba(255, 255, 255, 0.16);
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  transition:
    transform 0.24s ease,
    box-shadow 0.24s ease;
}

.book-link:hover .book-card-fallback {
  transform: translateY(-5px);
  box-shadow: 0 16px 34px rgba(80, 140, 255, 0.18);
}

.book-cover {
  position: relative;
  display: grid;
  min-height: 13rem;
  flex: 1;
  place-items: center;
  overflow: hidden;
  border-radius: 0.9rem;
  background:
    radial-gradient(circle at 22% 18%, rgba(162, 210, 255, 0.26), transparent 32%),
    linear-gradient(145deg, rgba(18, 31, 54, 0.92), rgba(52, 68, 106, 0.72));
  background-size: cover;
  background-position: center;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.14),
    0 12px 28px rgba(0, 0, 0, 0.2);
}

.book-cover::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.11), transparent 46%);
  pointer-events: none;
}

.book-cover-placeholder {
  color: rgba(255, 255, 255, 0.82);
  font-size: 4rem;
  font-weight: 700;
  text-shadow: 0 8px 26px rgba(0, 0, 0, 0.42);
}

.book-info {
  padding: 0.9rem 0.35rem 0.15rem;
}

.book-name {
  overflow: hidden;
  color: rgba(255, 255, 255, 0.94);
  font-size: 0.98rem;
  font-weight: 700;
  line-height: 1.45;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.book-author {
  margin-top: 0.28rem;
  overflow: hidden;
  color: rgba(255, 255, 255, 0.55);
  font-size: 0.78rem;
  line-height: 1.45;
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
    gap: 0.8rem;
  }

  .book-link,
  .book-glass,
  .book-card {
    min-height: 15.5rem;
  }

  .book-cover {
    min-height: 10.4rem;
  }
}

@media (max-width: 440px) {
  .books-grid {
    grid-template-columns: 1fr;
  }
}
</style>
