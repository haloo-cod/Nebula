<template>
  <div class="about-comments">
    <h3 class="comments-title">评论</h3>
    <div class="comments-empty">暂无评论</div>
    <div class="comments-input-wrap">
      <input
        class="comments-input"
        type="text"
        placeholder="评论功能即将上线..."
        disabled
      />
      <button class="comments-submit" type="button" disabled>发送</button>
    </div>
  </div>
</template>

<script setup lang="ts">
// 评论区 UI 壳，后续对接后端
</script>

<style scoped>
.about-comments {
  padding: 1.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.comments-title {
  margin: 0 0 1rem;
  color: var(--text-primary);
  font-size: 1.1rem;
  font-weight: 700;
}

.comments-empty {
  text-align: center;
  padding: 2rem 0;
  color: var(--text-muted);
  font-size: 0.82rem;
}

.comments-input-wrap {
  display: flex;
  gap: 0.5rem;
}

.comments-input {
  flex: 1;
  padding: 0.6rem 1rem;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 0.75rem;
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-primary);
  font-size: 0.85rem;
  outline: none;
}

.comments-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.comments-input::placeholder {
  color: var(--text-muted);
}

.comments-submit {
  padding: 0.6rem 1.2rem;
  border: 1px solid rgba(140, 185, 255, 0.3);
  border-radius: 0.75rem;
  background: rgba(100, 150, 255, 0.12);
  color: rgba(180, 210, 255, 0.9);
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.comments-submit:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

@media (min-width: 768px) {
  .about-comments {
    padding: 2rem 2.5rem;
  }
}
</style>

<!-- Light 主题适配 -->
<style>
[data-theme='light'] .about-comments {
  border-top-color: rgba(0, 0, 0, 0.06);
}

[data-theme='light'] .about-comments .comments-input {
  background: rgba(0, 0, 0, 0.03);
  border-color: rgba(0, 0, 0, 0.1);
}

[data-theme='light'] .about-comments .comments-submit {
  background: rgba(50, 100, 220, 0.1);
  border-color: rgba(50, 100, 220, 0.3);
  color: rgba(30, 70, 180, 1);
}
</style>
