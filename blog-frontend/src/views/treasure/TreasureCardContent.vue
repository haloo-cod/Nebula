<template>
  <article class="treasure-card">
    <!-- 图标 -->
    <div class="treasure-icon">{{ item.icon }}</div>

    <!-- 信息区 -->
    <div class="treasure-info">
      <h3 class="treasure-name">{{ item.title }}</h3>
      <p class="treasure-description">{{ item.description }}</p>
    </div>

    <!-- 底部：标签 + 下载标记 -->
    <div class="treasure-footer">
      <div class="treasure-tags">
        <span v-for="tag in item.tags" :key="tag" class="treasure-tag">{{ tag }}</span>
      </div>
      <span v-if="item.downloadUrl" class="treasure-download-badge" title="可下载">↓</span>
    </div>
  </article>
</template>

<script setup lang="ts">
import type { Treasure } from '@/types'

defineProps<{
  item: Treasure
}>()
</script>

<style scoped>
.treasure-card {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 1.4rem 1.2rem 1rem;
  border-radius: 1.15rem;
}

.treasure-icon {
  font-size: 2rem;
  line-height: 1;
  margin-bottom: 0.8rem;
}

.treasure-info {
  flex: 1;
  min-width: 0;
}

.treasure-name {
  color: var(--text-primary);
  font-size: 1.05rem;
  font-weight: 700;
  line-height: 1.4;
  margin-bottom: 0.4rem;
}

.treasure-description {
  color: var(--text-secondary);
  font-size: 0.82rem;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
  overflow: hidden;
}

.treasure-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 0.9rem;
  gap: 0.5rem;
}

.treasure-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.treasure-tag {
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: var(--text-secondary);
  font-size: 0.68rem;
  white-space: nowrap;
}

.treasure-download-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 1.6rem;
  height: 1.6rem;
  border-radius: 50%;
  background: rgba(255, 200, 100, 0.18);
  border: 1px solid rgba(255, 200, 100, 0.3);
  color: rgba(255, 220, 140, 0.9);
  font-size: 0.8rem;
  font-weight: 700;
  flex-shrink: 0;
}
</style>
