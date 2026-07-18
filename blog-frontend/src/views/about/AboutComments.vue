<template>
  <div class="about-comments">
    <h3 class="comments-title">评论</h3>

    <!-- 输入区 -->
    <div class="comments-input-wrap">
      <input
        class="comments-input"
        type="text"
        placeholder="评论功能即将上线..."
        disabled
      />
      <button class="comments-submit" type="button" disabled>发送</button>
    </div>

    <!-- 测试评论列表 -->
    <div class="comments-list">
      <div v-for="comment in comments" :key="comment.id" class="comment-item">
        <div class="comment-avatar" :style="{ background: comment.avatarColor }">
          {{ comment.author.charAt(0) }}
        </div>
        <div class="comment-body">
          <div class="comment-head">
            <span class="comment-author">{{ comment.author }}</span>
            <span class="comment-date">{{ comment.date }}</span>
          </div>
          <p class="comment-content">{{ comment.content }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface CommentItem {
  id: number
  author: string
  date: string
  content: string
  avatarColor: string
}

const comments: CommentItem[] = [
  {
    id: 1,
    author: '访客A',
    date: '2026-07-15 14:22',
    content: '博客很漂亮，液态玻璃效果惊艳！一直在找这种风格的博客参考，学到很多。',
    avatarColor: '#6366f1',
  },
  {
    id: 2,
    author: 'Starlit',
    date: '2026-07-15 16:05',
    content: '谢谢喜欢！还在不断完善中，后续会加入更多有趣的功能~',
    avatarColor: '#ec4899',
  },
  {
    id: 3,
    author: '访客B',
    date: '2026-07-17 09:30',
    content: '请问自习室的番茄钟数据是存在本地的吗？还是会在后端上线后同步？',
    avatarColor: '#14b8a6',
  },
  {
    id: 4,
    author: 'Starlit',
    date: '2026-07-17 10:15',
    content: '目前是 localStorage 本地存储，后续后端上线后会支持云端同步，数据不会丢的。',
    avatarColor: '#ec4899',
  },
]
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

.comments-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 1.25rem;
}

.comment-item {
  display: flex;
  gap: 0.75rem;
}

.comment-avatar {
  flex-shrink: 0;
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 0.8rem;
  font-weight: 700;
}

.comment-body {
  flex: 1;
  min-width: 0;
}

.comment-head {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
}

.comment-author {
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--text-primary);
}

.comment-date {
  font-size: 0.68rem;
  color: var(--text-muted);
}

.comment-content {
  margin: 0;
  font-size: 0.85rem;
  line-height: 1.6;
  color: var(--text-secondary);
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
