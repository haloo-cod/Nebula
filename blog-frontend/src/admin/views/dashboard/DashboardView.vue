<script setup lang="ts">
/**
 * 管理后台仪表盘（占位页）
 * Phase 4 再填充真实统计数据
 */
import { Document, ChatDotRound, Reading, Connection, EditPen, Upload, Picture } from '@element-plus/icons-vue'
</script>

<template>
  <div class="dashboard-page">
    <!-- 统计卡片 -->
    <div class="stat-cards">
      <el-card shadow="hover" class="stat-card">
        <div class="stat-content">
          <el-icon :size="32" color="#409eff"><Document /></el-icon>
          <div class="stat-info">
            <span class="stat-value">--</span>
            <span class="stat-label">文章数</span>
          </div>
        </div>
      </el-card>

      <el-card shadow="hover" class="stat-card">
        <div class="stat-content">
          <el-icon :size="32" color="#67c23a"><ChatDotRound /></el-icon>
          <div class="stat-info">
            <span class="stat-value">--</span>
            <span class="stat-label">评论数</span>
          </div>
        </div>
      </el-card>

      <el-card shadow="hover" class="stat-card">
        <div class="stat-content">
          <el-icon :size="32" color="#e6a23c"><Reading /></el-icon>
          <div class="stat-info">
            <span class="stat-value">--</span>
            <span class="stat-label">图书数</span>
          </div>
        </div>
      </el-card>

      <el-card shadow="hover" class="stat-card">
        <div class="stat-content">
          <el-icon :size="32" color="#f56c6c"><Connection /></el-icon>
          <div class="stat-info">
            <span class="stat-value">--</span>
            <span class="stat-label">友链数</span>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 快捷操作 -->
    <el-card shadow="never" class="quick-actions">
      <template #header>
        <span>快捷操作</span>
      </template>
      <div class="action-btns">
        <el-button type="primary">
          <el-icon><EditPen /></el-icon>写文章
        </el-button>
        <el-button>
          <el-icon><ChatDotRound /></el-icon>发说说
        </el-button>
        <el-button>
          <el-icon><Upload /></el-icon>上传图书
        </el-button>
        <el-button>
          <el-icon><Picture /></el-icon>上传图片
        </el-button>
      </div>
    </el-card>

    <!-- 欢迎信息 -->
    <el-card shadow="never" class="welcome-card">
      <div class="welcome-content">
        <h2>欢迎使用博客管理后台</h2>
        <p>在这里你可以管理博客的所有内容：文章、说说、图书、相册、友链等。</p>
        <p class="tip">统计数据将在后续版本中接入。</p>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.dashboard-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.stat-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}

.stat-card {
  border-radius: 12px;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--admin-text-color, #303133);
}

.stat-label {
  font-size: 13px;
  color: var(--admin-text-secondary, #909399);
  margin-top: 2px;
}

.quick-actions {
  border-radius: 12px;
}

.action-btns {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.welcome-card {
  border-radius: 12px;
}

.welcome-content h2 {
  margin: 0 0 8px;
  font-size: 18px;
  color: var(--admin-text-color, #303133);
}

.welcome-content p {
  margin: 0 0 4px;
  color: var(--admin-text-secondary, #909399);
  font-size: 14px;
}

.welcome-content .tip {
  font-style: italic;
  opacity: 0.7;
}
</style>
