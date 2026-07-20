<script setup lang="ts">
/**
 * 站点配置页
 * 未来扩展：站点名称、描述、SEO、公告等全局配置
 * 当前为占位页，待后端 SiteConfig API 完善后对接
 */
import { Setting } from '@element-plus/icons-vue'
</script>

<template>
  <div class="site-config-page">
    <el-card shadow="never" class="section-card">
      <template #header>
        <span>站点配置</span>
      </template>
      <div class="placeholder-content">
        <el-icon :size="48" color="#c0c4cc"><Setting /></el-icon>
        <h3>站点配置功能开发中</h3>
        <p>后续将支持以下配置项：</p>
        <ul>
          <li>站点名称 / 副标题</li>
          <li>SEO 描述 / 关键词</li>
          <li>公告信息</li>
          <li>评论开关</li>
          <li>注册开关（未来用户系统）</li>
        </ul>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.site-config-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.section-card {
  border-radius: 12px;
}
.placeholder-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 0;
  text-align: center;
}
.placeholder-content h3 {
  margin: 16px 0 8px;
  color: var(--admin-text-color, #303133);
}
.placeholder-content p {
  color: var(--admin-text-secondary, #909399);
  margin-bottom: 12px;
}
.placeholder-content ul {
  list-style: none;
  padding: 0;
  color: var(--admin-text-secondary, #909399);
  font-size: 14px;
}
.placeholder-content li::before {
  content: '• ';
  color: #409eff;
}
</style>
