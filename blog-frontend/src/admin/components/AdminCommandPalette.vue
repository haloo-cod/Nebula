<script setup lang="ts">
/**
 * 后台全局命令跳转面板（⌘K / Ctrl+K）
 * 支持按关键字检索全部后台页面及高频创作与主题切换动作。
 */
import { computed, nextTick, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Search } from '@element-plus/icons-vue'
import { adminMenuGroups } from '@/admin/layout/AdminMenu'

/** 单条可执行命令 */
interface CommandEntry {
  id: string
  group: string
  title: string
  hint: string
  keywords: string
  run: () => void
}

const props = defineProps<{
  /** 是否打开命令面板 */
  modelValue: boolean
  /** 当前是否为暗色模式 */
  isDark: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  toggleDark: []
}>()

const router = useRouter()
const query = ref('')
const activeIndex = ref(0)
const inputRef = ref<HTMLInputElement | null>(null)

function close() {
  emit('update:modelValue', false)
}

function go(path: string) {
  close()
  void router.push(path)
}

const allEntries = computed<CommandEntry[]>(() => {
  const actions: CommandEntry[] = [
    {
      id: 'action-new-post',
      group: '快捷操作',
      title: '写新文章',
      hint: '/admin/posts/new',
      keywords: '写文章 新建文章 post create markdown',
      run: () => go('/admin/posts/new'),
    },
    {
      id: 'action-toggle-theme',
      group: '快捷操作',
      title: props.isDark ? '切换为亮色模式（纸墨刊物）' : '切换为暗色模式（星夜曜石）',
      hint: '主题切换',
      keywords: '暗色 亮色 主题 theme dark light',
      run: () => {
        emit('toggleDark')
        close()
      },
    },
    {
      id: 'action-visit-site',
      group: '快捷操作',
      title: '返回博客前台',
      hint: '/',
      keywords: '前台 首页 home site blog',
      run: () => go('/'),
    },
  ]

  const pages: CommandEntry[] = adminMenuGroups.flatMap((group) =>
    group.items.map((item) => ({
      id: `route-${item.path}`,
      group: group.title,
      title: item.title,
      hint: item.path,
      keywords: `${group.title} ${item.title} ${item.path} ${item.keywords ?? ''}`,
      run: () => go(item.path),
    })),
  )

  return [...actions, ...pages]
})

const filteredEntries = computed(() => {
  const term = query.value.trim().toLowerCase()
  if (!term) return allEntries.value
  return allEntries.value.filter(
    (entry) =>
      entry.title.toLowerCase().includes(term) ||
      entry.group.toLowerCase().includes(term) ||
      entry.keywords.toLowerCase().includes(term),
  )
})

watch(
  () => props.modelValue,
  async (open) => {
    if (!open) return
    query.value = ''
    activeIndex.value = 0
    await nextTick()
    inputRef.value?.focus()
  },
)

watch(filteredEntries, () => {
  activeIndex.value = 0
})

function handleKeydown(event: KeyboardEvent) {
  const list = filteredEntries.value
  if (event.key === 'Escape') {
    event.preventDefault()
    close()
    return
  }
  if (!list.length) return
  if (event.key === 'ArrowDown') {
    event.preventDefault()
    activeIndex.value = (activeIndex.value + 1) % list.length
  } else if (event.key === 'ArrowUp') {
    event.preventDefault()
    activeIndex.value = (activeIndex.value - 1 + list.length) % list.length
  } else if (event.key === 'Enter') {
    event.preventDefault()
    list[activeIndex.value]?.run()
  }
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="modelValue"
      class="cmd-backdrop"
      role="dialog"
      aria-modal="true"
      aria-label="快捷命令搜索"
      @click.self="close"
    >
      <div class="cmd-panel" @keydown="handleKeydown">
        <div class="cmd-input-row">
          <el-icon class="cmd-search-icon"><Search /></el-icon>
          <input
            ref="inputRef"
            v-model="query"
            type="text"
            class="cmd-input"
            placeholder="搜索后台模块、页面路径或快捷操作..."
          />
          <kbd class="cmd-kbd">ESC</kbd>
        </div>

        <div class="cmd-list">
          <template v-if="filteredEntries.length">
            <button
              v-for="(entry, index) in filteredEntries"
              :key="entry.id"
              type="button"
              class="cmd-item"
              :class="{ 'is-active': index === activeIndex }"
              @mouseenter="activeIndex = index"
              @click="entry.run()"
            >
              <span class="cmd-item-main">
                <span class="cmd-item-group">{{ entry.group }}</span>
                <span class="cmd-item-title">{{ entry.title }}</span>
              </span>
              <span class="cmd-item-hint">{{ entry.hint }}</span>
            </button>
          </template>
          <div v-else class="cmd-empty">未找到匹配的模块或操作</div>
        </div>

        <footer class="cmd-footer">
          <span>↑↓ 选择</span>
          <span>↵ 打开</span>
          <span>ESC 关闭</span>
        </footer>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.cmd-backdrop {
  position: fixed;
  inset: 0;
  z-index: 2600;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: min(14vh, 110px) 16px 24px;
  background: rgba(11, 12, 14, 0.42);
  backdrop-filter: blur(4px);
}

.cmd-panel {
  width: min(560px, 100%);
  overflow: hidden;
  border: 1px solid var(--admin-border-color);
  border-radius: 14px;
  background: var(--admin-panel-bg);
  box-shadow: var(--admin-shadow-overlay);
}

.cmd-input-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--admin-border-color);
}

.cmd-search-icon {
  color: var(--admin-text-muted);
  font-size: 16px;
  flex-shrink: 0;
}

.cmd-input {
  flex: 1;
  min-width: 0;
  border: 0;
  outline: none;
  background: transparent;
  color: var(--admin-text-color);
  font-size: 14px;
}

.cmd-input::placeholder {
  color: var(--admin-text-muted);
}

.cmd-kbd {
  padding: 2px 6px;
  border: 1px solid var(--admin-border-color);
  border-radius: 5px;
  background: var(--admin-fill-bg);
  color: var(--admin-text-muted);
  font-family: var(--admin-font-mono);
  font-size: 10px;
}

.cmd-list {
  max-height: min(52vh, 380px);
  overflow-y: auto;
  padding: 8px;
}

.cmd-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  width: 100%;
  padding: 9px 12px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: var(--admin-text-color);
  text-align: left;
  cursor: pointer;
}

.cmd-item.is-active {
  background: var(--admin-menu-active-bg);
}

.cmd-item-main {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.cmd-item-group {
  padding: 1px 6px;
  border-radius: 4px;
  background: var(--admin-fill-bg);
  color: var(--admin-text-secondary);
  font-size: 11px;
  flex-shrink: 0;
}

.cmd-item-title {
  font-size: 13.5px;
  font-weight: 550;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cmd-item-hint {
  color: var(--admin-text-muted);
  font-family: var(--admin-font-mono);
  font-size: 11px;
  flex-shrink: 0;
}

.cmd-empty {
  padding: 28px 16px;
  color: var(--admin-text-muted);
  font-size: 13px;
  text-align: center;
}

.cmd-footer {
  display: flex;
  gap: 16px;
  padding: 9px 16px;
  border-top: 1px solid var(--admin-border-color);
  background: var(--admin-panel-subtle);
  color: var(--admin-text-muted);
  font-size: 11px;
}
</style>
