<template>
  <div class="note-card">
    <div class="note-header">
      <h2 class="note-title">{{ title }}</h2>
      <span class="note-subtitle">{{ subtitle }}</span>
    </div>
    <p class="note-content">{{ content }}</p>
    <p class="note-features">{{ features }}</p>
    <div class="note-footer">
      <span class="note-date">{{ date }}</span>
      <div class="note-stats">
        <span v-for="stat in stats" :key="stat.label" class="note-stat">
          <span class="note-stat-value">{{ stat.value }}</span>
          <span class="note-stat-label">{{ stat.label }}</span>
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface NoteStat {
  value: string
  label: string
}

withDefaults(
  defineProps<{
    title: string
    subtitle: string
    content: string
    features: string
    date: string
    stats?: NoteStat[]
  }>(),
  {
    stats: () => [],
  },
)
</script>

<style scoped>
.note-card {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  padding: 1.5rem 1.75rem;
  height: 100%;
  box-sizing: border-box;
  min-height: 0;
}

.note-header {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.note-title {
  font-size: 1.4rem;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
  margin: 0;
  letter-spacing: 0.02em;
}

.note-subtitle {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.55);
  margin: 0;
}

.note-content {
  font-size: 1rem;
  color: rgba(255, 255, 255, 0.85);
  line-height: 1.6;
  margin: 0;
}

.note-features {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.6);
  line-height: 1.6;
  margin: 0;
}

.note-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: auto;
  padding-top: 0.5rem;
}

.note-date {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.5);
}

.note-stats {
  display: flex;
  gap: 1.2rem;
}

.note-stat {
  display: flex;
  align-items: baseline;
  gap: 0.3rem;
}

.note-stat-value {
  font-size: 0.95rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
}

.note-stat-label {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.45);
}
</style>
