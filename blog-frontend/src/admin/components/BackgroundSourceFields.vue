<script setup lang="ts">
import type { BackgroundSource } from '@/utils/backgroundSource'

const model = defineModel<BackgroundSource>({ required: true })
defineProps<{ disabled?: boolean; error?: string; batch?: boolean }>()
</script>

<template>
  <el-form-item label="背景来源（可选）">
    <el-input
      v-model="model.source_text"
      type="textarea"
      :rows="3"
      maxlength="120"
      show-word-limit
      :disabled="disabled"
      placeholder="例如：画师名字 · 作品名称"
    />
    <span class="source-hint">留空时隐藏来源牌{{ batch ? '；批量添加的图片共用此来源' : '' }}</span>
  </el-form-item>
  <el-form-item label="来源外链（可选）" :error="error">
    <el-input
      v-model="model.source_url"
      maxlength="2048"
      :disabled="disabled"
      placeholder="https://…（点击来源牌后打开）"
    />
  </el-form-item>
</template>

<style scoped>
.source-hint {
  font-size: 12px;
  color: var(--admin-text-secondary, #909399);
  line-height: 1.6;
}
</style>
