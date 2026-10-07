import { computed, ref, type Ref } from 'vue'
import type { BackgroundItem } from '@/data/backgrounds'

/** 为一个背景分组维护稳定身份；旧版下标只在首次成功加载时迁移。 */
export function createBackgroundSelection(items: Ref<BackgroundItem[]>, legacyKey: string) {
  const storage = typeof localStorage === 'undefined' ? undefined : localStorage
  const idKey = `${legacyKey}-id`
  const srcKey = `${legacyKey}-src`
  const savedId = Number(storage?.getItem(idKey))
  const selectedId = ref<number | null>(Number.isInteger(savedId) && savedId > 0 ? savedId : null)
  const selectedSrc = ref(storage?.getItem(srcKey) ?? '')
  const legacyIndex = Number(storage?.getItem(legacyKey))
  let loaded = false

  const index = computed({
    get() {
      const found = items.value.findIndex((item) =>
        item.id !== undefined ? item.id === selectedId.value : item.src === selectedSrc.value,
      )
      if (found >= 0) return found
      if (
        !loaded &&
        Number.isInteger(legacyIndex) &&
        legacyIndex >= 0 &&
        legacyIndex < items.value.length
      ) {
        return legacyIndex
      }
      return 0
    },
    set(value: number) {
      const item = items.value[value]
      if (!Number.isInteger(value) || !item) return
      if (item.id !== undefined) {
        selectedId.value = item.id
        storage?.setItem(idKey, String(item.id))
      } else {
        selectedSrc.value = item.src
        storage?.setItem(srcKey, item.src)
      }
    },
  })

  /** 原子替换分组并保留所选 ID；不存在时回退第一张。 */
  function replace(next: BackgroundItem[]) {
    const existing = next.find((item) => item.id === selectedId.value)
    const migrated =
      !loaded && selectedId.value === null && Number.isInteger(legacyIndex)
        ? next[legacyIndex]
        : undefined
    const selected = existing ?? migrated ?? next[0]
    items.value = next
    loaded = true
    selectedId.value = selected?.id ?? null
    if (selectedId.value !== null) storage?.setItem(idKey, String(selectedId.value))
    else storage?.removeItem(idKey)
    // 已完成迁移，避免空分组以后再次把旧下标当成用户选择。
    storage?.removeItem(legacyKey)
  }

  return { index, replace }
}
