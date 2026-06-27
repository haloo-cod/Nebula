<template>
  <div class="diary-card">
    <div class="diary-header">
      <span class="diary-tag">{{ tag }}</span>
      <span class="diary-time">{{ time }}</span>
    </div>
    <p class="diary-content">{{ content }}</p>
    <div class="diary-footer">
      <span class="diary-readmore">点击查看全文</span>
    </div>
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    tag: string
    time: string
    content: string
  }>(),
  {},
)
</script>

<style scoped>
.diary-card {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  padding: 1.25rem 1.5rem;
  height: 100%;
  box-sizing: border-box;
  min-height: 0;
}

.diary-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.diary-tag {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.85);
  background: rgba(255, 150, 180, 0.15);
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
}

.diary-time {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.45);
}

.diary-content {
  font-size: 0.88rem;
  color: rgba(255, 255, 255, 0.85);
  line-height: 1.75;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 6;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.diary-footer {
  margin-top: auto;
  text-align: right;
}

.diary-readmore {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.4);
  cursor: pointer;
  transition: color 0.2s ease;
}

.diary-readmore:hover {
  color: rgba(255, 255, 255, 0.8);
}
</style>