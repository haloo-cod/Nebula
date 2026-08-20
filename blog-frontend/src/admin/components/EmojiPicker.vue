<script setup lang="ts">
/** 可复用 Emoji 选择器，保存 Unicode Emoji 字符串。 */
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import 'emoji-picker-element'

const props = defineProps<{ modelValue: string }>()
const emit = defineEmits<{ (event: 'update:modelValue', value: string): void }>()

const open = ref(false)
const root = ref<HTMLElement | null>(null)
const picker = ref<HTMLElement | null>(null)

function toggle() {
  open.value = !open.value
}

function clear() {
  emit('update:modelValue', '')
  open.value = false
}

function handleEmojiClick(event: Event) {
  // emoji-picker-element 的事件 detail 提供所选 Emoji 的 unicode 字符串。
  const detail = (event as CustomEvent<{ unicode?: string }>).detail
  if (detail?.unicode) {
    emit('update:modelValue', detail.unicode)
    open.value = false
  }
}

function handleDocumentClick(event: MouseEvent) {
  if (root.value && !root.value.contains(event.target as Node)) {
    open.value = false
  }
}

watch(open, async (visible) => {
  if (!visible) return
  await nextTick()
  picker.value?.addEventListener('emoji-click', handleEmojiClick)
})

onMounted(() => document.addEventListener('click', handleDocumentClick))
onUnmounted(() => {
  picker.value?.removeEventListener('emoji-click', handleEmojiClick)
  document.removeEventListener('click', handleDocumentClick)
})
</script>

<template>
  <div ref="root" class="emoji-picker-field">
    <button type="button" class="emoji-trigger" @click.stop="toggle">
      <span v-if="modelValue" class="emoji-value">{{ props.modelValue }}</span>
      <span v-else class="emoji-placeholder">选择 Emoji</span>
    </button>
    <button v-if="modelValue" type="button" class="emoji-clear" aria-label="清除心情" @click="clear">
      清除
    </button>
    <div v-if="open" class="emoji-popover" @click.stop>
      <component :is="'emoji-picker'" ref="picker" class="emoji-picker-element" />
    </div>
  </div>
</template>

<style scoped>
.emoji-picker-field { position: relative; display: flex; align-items: center; gap: 8px; }
.emoji-trigger { min-width: 120px; height: 34px; padding: 0 12px; border: 1px solid var(--el-border-color); border-radius: 4px; background: var(--el-fill-color-blank); cursor: pointer; text-align: left; }
.emoji-value { font-size: 22px; line-height: 1; }
.emoji-placeholder, .emoji-clear { color: var(--el-text-color-placeholder); font-size: 13px; }
.emoji-clear { border: 0; background: transparent; cursor: pointer; }
.emoji-popover { position: absolute; z-index: 20; top: calc(100% + 8px); left: 0; box-shadow: var(--el-box-shadow-light); }
.emoji-picker-element { width: min(352px, calc(100vw - 48px)); height: 420px; }
</style>
