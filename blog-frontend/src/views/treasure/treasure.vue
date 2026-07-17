<template>
  <PageBackground>
    <div class="treasure-page">
      <!-- 页面头部 -->
      <header class="treasure-header">
        <span class="treasure-kicker">Treasure</span>
        <h1 class="treasure-title">藏宝阁</h1>
        <p class="treasure-desc">收集有趣的开源项目和实用资源，未来会提供文件下载。</p>
      </header>

      <!-- 分类筛选标签 -->
      <nav class="treasure-tabs" aria-label="分类筛选">
        <button
          class="tab-btn"
          :class="{ 'tab-btn-active': activeCategory === null }"
          type="button"
          @click="activeCategory = null"
        >
          全部
        </button>
        <button
          v-for="cat in categories"
          :key="cat"
          class="tab-btn"
          :class="{ 'tab-btn-active': activeCategory === cat }"
          type="button"
          @click="activeCategory = cat"
        >
          {{ cat }}
        </button>
      </nav>

      <!-- 宝物网格 -->
      <TransitionGroup name="grid-item" tag="div" class="treasure-grid">
        <a
          v-for="item in pagedTreasures"
          :key="item.slug"
          :href="item.url"
          target="_blank"
          rel="noopener noreferrer"
          class="treasure-link"
        >
          <LiquidGlass
            v-if="ui.liquidGlassEnabled"
            class="treasure-glass"
            :theme="ui.theme"
            :corner-radius="22"
            :blur-radius="ui.liquidGlassBlur"
            :glass-thickness="36"
            :highlight-width="3"
            ripple-trail
          >
            <TreasureCardContent :item="item" />
          </LiquidGlass>

          <PanelFallbackGlass v-else tag="div" class="treasure-glass treasure-glass--fallback">
            <TreasureCardContent :item="item" />
          </PanelFallbackGlass>
        </a>
      </TransitionGroup>

      <!-- 空状态 -->
      <div v-if="filteredTreasures.length === 0" class="treasure-empty">
        <p>该分类暂无内容</p>
      </div>

      <!-- 分页 -->
      <div v-if="totalPages > 1" class="treasure-pagination">
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
import { computed, ref, watch } from 'vue'
import PageBackground from '@/components/PageBackground.vue'
import LiquidGlass from '@/components/liquid-glass/LiquidGlass.vue'
import PanelFallbackGlass from '@/components/panels/PanelFallbackGlass.vue'
import TreasureCardContent from './TreasureCardContent.vue'
import { getTreasures, getTreasureCategories } from '@/data/treasures'
import { useUIStore } from '@/stores/ui'
import type { TreasureCategory } from '@/types'

const ui = useUIStore()

// 数据
const treasures = getTreasures()
const categories = getTreasureCategories()

// 分页配置
const PAGE_SIZE = 12
const currentPage = ref(1)

// 当前选中的分类，null 表示全部
const activeCategory = ref<TreasureCategory | null>(null)

// 筛选后的宝物列表（全部）
const filteredTreasures = computed(() => {
  if (activeCategory.value === null) return treasures
  return treasures.filter((t) => t.category === activeCategory.value)
})

// 总页数
const totalPages = computed(() => Math.max(1, Math.ceil(filteredTreasures.value.length / PAGE_SIZE)))

// 页码列表
const pageNumbers = computed(() =>
  Array.from({ length: totalPages.value }, (_, index) => index + 1),
)

// 当前页显示的数据
const pagedTreasures = computed(() => {
  const start = (currentPage.value - 1) * PAGE_SIZE
  return filteredTreasures.value.slice(start, start + PAGE_SIZE)
})

function goPrevPage() {
  if (currentPage.value > 1) currentPage.value -= 1
}

function goNextPage() {
  if (currentPage.value < totalPages.value) currentPage.value += 1
}

// 切换分类时重置页码
watch(activeCategory, () => {
  currentPage.value = 1
})

// 如果总页数变小（比如数据减少），保证当前页不越界
watch(totalPages, (nextTotal) => {
  if (currentPage.value > nextTotal) currentPage.value = nextTotal
})
</script>

<style scoped>
.treasure-page {
  position: relative;
  z-index: 10;
  width: min(100%, 76rem);
  margin: 0 auto;
  padding: 7rem 1rem 5rem;
}

/* ===== 页面头部 ===== */
.treasure-header {
  margin-bottom: 1.8rem;
}

.treasure-kicker {
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: rgba(255, 200, 100, 0.78);
}

.treasure-title {
  margin-top: 0.4rem;
  color: var(--text-primary);
  font-size: clamp(1.7rem, 3vw, 2.6rem);
  font-weight: 700;
  letter-spacing: 0.08em;
}

.treasure-desc {
  margin-top: 0.5rem;
  max-width: 42rem;
  color: var(--text-secondary);
  font-size: 0.9rem;
  line-height: 1.7;
}

/* ===== 分类标签 ===== */
.treasure-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1.6rem;
}

.tab-btn {
  padding: 0.5rem 1.1rem;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.06);
  color: var(--text-secondary);
  font-size: 0.82rem;
  cursor: pointer;
  transition:
    background 0.2s ease,
    color 0.2s ease,
    border-color 0.2s ease;
}

.tab-btn:hover {
  background: rgba(255, 255, 255, 0.12);
  color: var(--text-primary);
}

.tab-btn-active {
  border-color: rgba(255, 200, 100, 0.5);
  background: rgba(255, 200, 100, 0.22);
  color: var(--text-primary);
}

/* ===== 宝物网格 ===== */
.treasure-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1rem;
}

.treasure-link {
  display: block;
  min-height: 12rem;
  color: inherit;
  text-decoration: none;
}

.treasure-glass {
  width: 100%;
  height: 100%;
  min-height: inherit;
  border-radius: 1.25rem;
  transition:
    transform 0.24s ease,
    filter 0.24s ease;
}

.treasure-glass--fallback {
  transition:
    transform 0.24s ease,
    border-color 0.28s ease,
    box-shadow 0.28s ease;
}

.treasure-link:hover .treasure-glass {
  transform: translateY(-4px);
  filter: drop-shadow(0 14px 32px rgba(255, 200, 100, 0.12));
}

.treasure-link:hover .treasure-glass--fallback {
  border-color: rgba(255, 200, 100, 0.32);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.16),
    0 14px 32px rgba(255, 200, 100, 0.1);
}

/* ===== 空状态 ===== */
.treasure-empty {
  text-align: center;
  padding: 4rem 1rem;
  color: var(--text-secondary);
  font-size: 0.95rem;
}

/* ===== 分页 ===== */
.treasure-pagination {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.65rem;
  margin-top: 1.8rem;
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
  border-color: rgba(255, 200, 100, 0.5);
  background: rgba(255, 200, 100, 0.18);
  color: var(--text-primary);
}

/* ===== TransitionGroup 动画 ===== */
.grid-item-enter-active {
  transition: transform 0.3s ease;
}

.grid-item-leave-active {
  transition:
    opacity 0.2s ease,
    transform 0.2s ease;
  position: absolute;
}

.grid-item-enter-from {
  transform: translateY(16px);
}

.grid-item-leave-to {
  opacity: 0;
  transform: scale(0.95);
}

.grid-item-move {
  transition: transform 0.3s ease;
}

/* ===== 响应式 ===== */
@media (max-width: 1023px) {
  .treasure-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .treasure-page {
    padding-top: 6rem;
  }

  .treasure-grid {
    grid-template-columns: 1fr;
  }
}
</style>
