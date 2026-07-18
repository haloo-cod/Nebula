<template>
  <div class="about-tabs">
    <button
      class="tab-btn"
      :class="{ 'tab-btn--active': activeTab === 'intro' }"
      type="button"
      @click="$emit('change', 'intro')"
    >
      自我介绍
    </button>
    <button
      class="tab-btn"
      :class="{ 'tab-btn--active': activeTab === 'activity' }"
      type="button"
      @click="$emit('change', 'activity')"
    >
      研究动态
    </button>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  activeTab: 'intro' | 'activity'
}>()

defineEmits<{
  change: [tab: 'intro' | 'activity']
}>()
</script>

<style scoped>
.about-tabs {
  display: flex;
  gap: 0.35rem;
  padding: 0.3rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 0.85rem;
  width: fit-content;
}

.tab-btn {
  padding: 0.5rem 1.2rem;
  border: none;
  border-radius: 0.65rem;
  background: transparent;
  color: var(--text-muted);
  font-size: 0.82rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.25s ease;
}

.tab-btn:hover:not(.tab-btn--active) {
  color: var(--text-secondary);
}

.tab-btn--active {
  background: rgba(100, 150, 255, 0.2);
  color: rgba(180, 210, 255, 0.95);
  box-shadow: 0 2px 8px rgba(100, 150, 255, 0.15);
}
</style>

<!-- Light 主题适配 -->
<style>
[data-theme='light'] .about-tabs {
  background: rgba(0, 0, 0, 0.03);
  border-color: rgba(0, 0, 0, 0.08);
}

[data-theme='light'] .about-tabs .tab-btn--active {
  background: rgba(50, 100, 220, 0.12);
  color: rgba(30, 70, 180, 1);
  box-shadow: 0 2px 8px rgba(50, 100, 220, 0.1);
}
</style>
