<template>
  <GlassPanel :compact="compact" :flat="flat" class="flex flex-col items-center text-center">
    <img
      :src="avatar"
      alt="avatar"
      class="avatar"
      :class="{ 'avatar-sm': compact, 'avatar-square': square }"
      translate="no"
    />
    <h2 class="name" :class="{ 'name-sm': compact }">{{ name }}</h2>
    <p class="bio" :class="{ 'bio-sm': compact }">{{ bio }}</p>
    <div class="social-links" translate="no">
      <a
        v-for="link in links"
        :key="link.label"
        :href="link.url"
        :title="link.label"
        target="_blank"
        rel="noopener"
        class="social-icon"
        >{{ link.icon }}</a
      >
    </div>
  </GlassPanel>
</template>

<script setup>
import GlassPanel from './GlassPanel.vue'
// 定义组件属性 约束父组件传入的数据类型和默认值
defineProps({
  avatar: { type: String, required: true },
  name: { type: String, default: 'Starlit' },
  bio: { type: String, default: '分享技术、生活和思考的个人博客' },
  links: { type: Array, default: () => [] },
  compact: { type: Boolean, default: false },
  flat: { type: Boolean, default: false },
  // square: 头像使用方形（圆角矩形）而非圆形
  square: { type: Boolean, default: false },
})
</script>

<style scoped>
.avatar {
  width: 100px; /* 头像尺寸 */
  height: 100px;
  border-radius: 50%; /* 50% = 圆形，0 = 方形 */
  object-fit: cover;
  border: 2px solid rgba(255, 255, 255, 0.2);
  margin-bottom: 1rem; /* 头像与名字的间距 */
}

.name {
  font-size: 1.25rem; /* 名字字号 */
  font-weight: 700;
  color: #fff;
  margin-bottom: 0.25rem; /* 名字与简介的间距 */
}

.bio {
  font-size: 0.8rem; /* 简介字号 */
  color: rgba(255, 255, 255, 0.55); /* 简介颜色透明度 */
  margin-bottom: 1rem; /* 简介与图标的间距 */
  line-height: 1.5;
}

.social-links {
  display: flex;
  gap: 0.75rem; /* 图标之间的间距 */
  justify-content: center;
  margin-top: auto;
}

.social-icon {
  font-size: 1.25rem; /* 图标大小 */
  color: rgba(255, 255, 255, 0.5); /* 图标颜色透明度 */
  transition:
    color 0.3s ease,
    transform 0.3s ease;
}

.social-icon:hover {
  color: rgba(255, 255, 255, 0.9); /* hover 时的图标颜色 */
  transform: translateY(-2px); /* hover 时上浮距离 */
}

/* 方形头像版本：占满整个面板宽度（面板自带 1.5rem 内边距形成间隙），
   1:1 方形圆角 + 阴影 */
.avatar-square {
  width: 100%;
  height: auto;
  aspect-ratio: 1 / 1;
  border-radius: 1rem;
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow:
    0 8px 24px rgba(0, 0, 0, 0.35),
    0 2px 6px rgba(0, 0, 0, 0.25);
}

/* 紧凑版（首页左列） */
.avatar-sm {
  width: 80px;
  height: 80px;
  margin-bottom: 0.75rem;
}

.name-sm {
  font-size: 1.1rem;
}

.bio-sm {
  font-size: 0.75rem;
  margin-bottom: 0.75rem;
}
</style>
