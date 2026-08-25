<script setup lang="ts">
/** 可复用 Emoji 选择器，保存 Unicode Emoji 字符串。 */
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import 'emoji-picker-element'

const props = defineProps<{
  modelValue: string
  /** 由外部按钮控制选择器打开状态。 */
  open?: boolean
  /** 编辑器工具栏已有触发按钮时隐藏组件自己的触发按钮。 */
  hideTrigger?: boolean
  /** 外部触发按钮选择器，避免打开弹窗时被文档点击监听立即关闭。 */
  externalTriggerSelector?: string
}>()
const emit = defineEmits<{
  (event: 'update:modelValue', value: string): void
  (event: 'update:open', value: boolean): void
}>()

const isOpen = ref(false)
const root = ref<HTMLElement | null>(null)
const picker = ref<HTMLElement | null>(null)
const popupStyle = ref<Record<string, string>>({})

function toggle() {
  setOpen(!isOpen.value)
}

function setOpen(value: boolean) {
  isOpen.value = value
  emit('update:open', value)
}

function clear() {
  emit('update:modelValue', '')
  setOpen(false)
}

function handleEmojiClick(event: Event) {
  // emoji-picker-element 的事件 detail 提供所选 Emoji 的 unicode 字符串。
  const detail = (event as CustomEvent<{ unicode?: string }>).detail
  if (detail?.unicode) {
    emit('update:modelValue', detail.unicode)
    setOpen(false)
  }
}

function handleDocumentClick(event: MouseEvent) {
  const target = event.target as Node
  if (root.value?.contains(target)) return
  if (
    props.externalTriggerSelector &&
    target instanceof Element &&
    target.closest(props.externalTriggerSelector)
  ) {
    return
  }
  setOpen(false)
}

/** 根据外部触发按钮位置放置选择器，避免被固定在页面角落。 */
function updatePopupPosition() {
  if (!isOpen.value || !props.externalTriggerSelector) return
  const trigger = document.querySelector<HTMLElement>(props.externalTriggerSelector)
  if (!trigger) return

  const rect = trigger.getBoundingClientRect()
  const width = Math.min(352, window.innerWidth - 32)
  const height = 420
  const gap = 8
  const left = Math.min(Math.max(16, rect.left), window.innerWidth - width - 16)
  const top =
    rect.bottom + gap + height <= window.innerHeight
      ? rect.bottom + gap
      : Math.max(16, rect.top - height - gap)

  popupStyle.value = {
    left: `${left}px`,
    top: `${top}px`,
    width: `${width}px`,
  }
}

watch(isOpen, async (visible) => {
  if (visible) {
    await nextTick()
    picker.value?.addEventListener('emoji-click', handleEmojiClick)
    updatePopupPosition()
  } else {
    picker.value?.removeEventListener('emoji-click', handleEmojiClick)
  }
})

watch(
  () => props.open,
  (value) => {
    if (typeof value === 'boolean' && value !== isOpen.value) isOpen.value = value
  },
  { immediate: true },
)

onMounted(() => {
  document.addEventListener('click', handleDocumentClick)
  window.addEventListener('resize', updatePopupPosition)
  window.addEventListener('scroll', updatePopupPosition, true)
})
onUnmounted(() => {
  picker.value?.removeEventListener('emoji-click', handleEmojiClick)
  document.removeEventListener('click', handleDocumentClick)
  window.removeEventListener('resize', updatePopupPosition)
  window.removeEventListener('scroll', updatePopupPosition, true)
})
</script>

<template>
  <div ref="root" class="emoji-picker-field">
    <button v-if="!hideTrigger" type="button" class="emoji-trigger" @click.stop="toggle">
      <span v-if="modelValue" class="emoji-value">{{ props.modelValue }}</span>
      <span v-else class="emoji-placeholder">选择 Emoji</span>
    </button>
    <button v-if="modelValue" type="button" class="emoji-clear" aria-label="清除心情" @click="clear">
      清除
    </button>
    <div
      v-if="isOpen"
      class="emoji-popover"
      :class="{ 'emoji-popover--external': externalTriggerSelector }"
      :style="popupStyle"
      @click.stop
    >
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
.emoji-popover {
  position: absolute;
  z-index: 2000;
  top: calc(100% + 8px);
  left: 0;
  box-shadow: var(--el-box-shadow-light);
}
.emoji-popover--external {
  position: fixed;
  top: auto;
  left: auto;
}
.emoji-picker-element { display: block; width: min(352px, calc(100vw - 32px)); height: 420px; }
</style>
