<template>
  <!-- 存储后端选择器：本地磁盘 / Cloudflare R2 -->
  <div class="storage-select" v-if="configLoaded">
    <span class="storage-select__label">存储：</span>
    <el-radio-group
      :model-value="storageBackend"
      size="small"
      @update:model-value="handleChange"
    >
      <el-radio-button value="local">本地</el-radio-button>
      <el-radio-button value="r2" :disabled="!r2Enabled">R2</el-radio-button>
    </el-radio-group>
  </div>
</template>

<script setup lang="ts">
/** 上传存储后端选择器：与 useStorageBackend 全局状态联动的轻量单选组件。 */
import { onMounted } from 'vue'
import { useStorageBackend } from '@/admin/composables/useStorageBackend'

const { storageBackend, r2Enabled, configLoaded, loadStorageConfig, setStorageBackend } =
  useStorageBackend()

onMounted(() => {
  loadStorageConfig()
})

/** 选择变化时同步全局状态（R2 未启用时该选项已被禁用，不会触发） */
function handleChange(value: string | number | boolean | undefined) {
  setStorageBackend(value === 'r2' ? 'r2' : 'local')
}
</script>

<style scoped>
.storage-select {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.storage-select__label {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}
</style>
