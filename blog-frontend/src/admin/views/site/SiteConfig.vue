<script setup lang="ts">
/**
 * 站点配置页
 * 规划中的全局站点参数配置入口（待后端 SiteConfig API 完整对接）。
 */
import { Setting } from '@element-plus/icons-vue'
import AdminPageHeader from '@/admin/components/AdminPageHeader.vue'

const plannedItems = [
  { title: '站点品牌与副标题', desc: '统一配置博客名称、眉标与页脚文案' },
  { title: 'SEO 与元信息', desc: '站点描述、关键词、默认社交分享图' },
  { title: '全站公告与维护开关', desc: '按需展示顶部公告条或临时维护提示' },
  { title: '评论与注册策略', desc: '集中控制评论审核、新用户注册及邮箱验证开关' },
]
</script>

<template>
  <div class="admin-page">
    <AdminPageHeader
      eyebrow="SYSTEM"
      title="站点配置"
      subtitle="全局站点开关与 SEO 参数设置入口（后端配置接口接入中）。"
    />

    <section class="admin-surface config-roadmap">
      <div class="roadmap-head">
        <span class="roadmap-icon"><el-icon :size="20"><Setting /></el-icon></span>
        <div>
          <h2>即将支持的配置项</h2>
          <p>后端 SiteConfig API 就绪后，以下配置将支持实时保存与热生效。</p>
        </div>
      </div>

      <div class="roadmap-grid">
        <div v-for="item in plannedItems" :key="item.title" class="roadmap-item">
          <span class="admin-status-dot is-primary">{{ item.title }}</span>
          <p>{{ item.desc }}</p>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.config-roadmap {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.roadmap-head {
  display: flex;
  align-items: center;
  gap: 14px;
}

.roadmap-icon {
  display: grid;
  width: 40px;
  height: 40px;
  place-items: center;
  border: 1px solid var(--admin-border-color);
  border-radius: 10px;
  background: var(--admin-fill-bg);
  color: var(--admin-primary-color);
  flex-shrink: 0;
}

.roadmap-head h2 {
  margin: 0 0 4px;
  color: var(--admin-text-color);
  font-size: 16px;
}

.roadmap-head p {
  margin: 0;
  color: var(--admin-text-secondary);
  font-size: 13px;
}

.roadmap-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.roadmap-item {
  padding: 14px 16px;
  border: 1px solid var(--admin-border-color);
  border-radius: 10px;
  background: var(--admin-panel-subtle);
}

.roadmap-item p {
  margin: 6px 0 0 13px;
  color: var(--admin-text-secondary);
  font-size: 12.5px;
}

@media (max-width: 640px) {
  .roadmap-grid {
    grid-template-columns: 1fr;
  }
}
</style>
