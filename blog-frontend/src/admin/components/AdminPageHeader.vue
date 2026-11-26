<script setup lang="ts">
/**
 * 后台统一编辑部风格页头
 * 统一展示眉标、主标题、数量徽标、副标题与右侧操作区。
 */
defineProps<{
  /** 可选大写眉标（如 OVERVIEW / CONTENT） */
  eyebrow?: string
  /** 页面主标题 */
  title: string
  /** 简短说明文案 */
  subtitle?: string
  /** 可选计数徽标文本（如 "24 篇"） */
  count?: string | number
}>()
</script>

<template>
  <header class="admin-page-head">
    <div class="admin-page-head__copy">
      <span v-if="eyebrow" class="admin-page-head__eyebrow">{{ eyebrow }}</span>
      <div class="admin-page-head__title-row">
        <h1 class="admin-page-head__title">{{ title }}</h1>
        <span v-if="count !== undefined && count !== ''" class="admin-count-badge">{{ count }}</span>
      </div>
      <p v-if="subtitle" class="admin-page-head__subtitle">{{ subtitle }}</p>
    </div>
    <div v-if="$slots.actions" class="admin-page-head__actions">
      <slot name="actions" />
    </div>
  </header>
</template>

<style scoped>
.admin-page-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.admin-page-head__copy {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.admin-page-head__eyebrow {
  color: var(--admin-primary-color);
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.admin-page-head__title-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.admin-page-head__title {
  margin: 0;
  color: var(--admin-text-color);
  font-size: clamp(22px, 2.4vw, 27px);
  font-weight: 700;
  letter-spacing: -0.025em;
  line-height: 1.2;
}

.admin-page-head__subtitle {
  margin: 0;
  color: var(--admin-text-secondary);
  font-size: 13px;
  line-height: 1.45;
}

.admin-page-head__actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

@media (max-width: 640px) {
  .admin-page-head {
    align-items: stretch;
    flex-direction: column;
    gap: 12px;
  }

  .admin-page-head__actions {
    width: 100%;
  }
}
</style>
