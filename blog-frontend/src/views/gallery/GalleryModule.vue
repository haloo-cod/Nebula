<template>
  <GlassPanel class="module-panel">
    <RouterLink to="/gallery" class="back-link">← 返回展览</RouterLink>
    <h1 class="module-title">{{ moduleTitle }}</h1>
    <!-- 内容待补充 -->
  </GlassPanel>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import GlassPanel from '@/components/panels/GlassPanel.vue'

const route = useRoute()

// 模块 slug → 中文标题映射
const titles: Record<string, string> = {
  projects: '项目',
  skills: '技能',
  timeline: '人生时间线',
  essays: '随笔',
  animation: '动画',
  images: '图片',
}

const moduleTitle = computed(() => {
  // 路由参数可能是字符串或数组,统一取字符串
  const module = String(route.params.module ?? '')
  return titles[module] || '展览'
})
</script>

<style scoped>
.module-panel {
  min-height: 60vh;
}

.back-link {
  display: inline-block;
  margin-bottom: 1.5rem;
  font-size: 0.82rem;
  color: rgba(160, 200, 255, 0.85);
  text-decoration: none;
  transition: color 0.2s ease;
}

.back-link:hover {
  color: rgba(200, 225, 255, 1);
}

.module-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.85);
  letter-spacing: 0.05em;
}
</style>
