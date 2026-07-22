<template>
  <span class="svg-icon" :style="{ '--icon-url': maskUrl }" aria-hidden="true"></span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

// 分开加载通用界面图标与社交平台图标，避免图标目录混杂。
const iconUrls = import.meta.glob<string>('../assets/icons/{ui,social}/*.svg', {
  query: '?url',
  import: 'default',
  eager: true,
})

// 短名到图标文件名前缀的映射。
const nameMap: Record<string, string> = {
  home: 'home',
  book: 'book',
  arrow_back_ios: 'arrow_back_ios',
  arrow_forward_ios: 'arrow_forward_ios',
  archive: 'box',
  friends: 'group',
  gift: 'featured_seasonal_and_gifts',
  about: 'info',
  gallery: 'account_circle',
  international: 'globe_asia',
  menu: 'menu',
  arrow_up: 'arrow_upward',
  settings: 'settings',
  sun: 'brightness_7',
  moon: 'brightness_4',
  article: 'article',
  photo: 'photo',
  download: 'download',
  tooltip: 'tooltip',
  local_library: 'local_library',
  folder: 'folder',
  keep: 'keep',
  github: 'github',
  bilibili: 'bilibili',
}

const props = defineProps<{ name: string }>()

const maskUrl = computed(() => {
  const prefix = nameMap[props.name] ?? props.name
  const entry = Object.entries(iconUrls).find(([path]) => {
    const file = path
      .split('/')
      .pop()!
      .replace(/\.svg$/i, '')
    return file === prefix || file.startsWith(prefix + '_')
  })
  return entry ? `url("${entry[1]}")` : 'none'
})
</script>

<style scoped>
.svg-icon {
  display: inline-block;
  width: 1em;
  height: 1em;
  flex-shrink: 0;
  background-color: currentColor;
  -webkit-mask-image: var(--icon-url);
  mask-image: var(--icon-url);
  -webkit-mask-repeat: no-repeat;
  mask-repeat: no-repeat;
  -webkit-mask-position: center;
  mask-position: center;
  -webkit-mask-size: contain;
  mask-size: contain;
}
</style>
