<template>
  <span class="svg-icon" :style="{ '--icon-url': maskUrl }" aria-hidden="true"></span>
</template>

<script setup>
import { computed } from 'vue'

const iconUrls = import.meta.glob('../assets/iconfont/goole/*.svg', {
  query: '?url',
  import: 'default',
  eager: true,
})

// 短名 → Google 文件名前缀映射
const nameMap = {
  home: 'home',
  archive: 'box',
  friends: 'group',
  gift: 'featured_seasonal_and_gifts',
  about: 'info',
  gallery: 'account_circle',
  international: 'globe_asia',
  menu: 'menu',
  arrow_up: 'arrow_upward',
  settings: 'settings',
}

const props = defineProps({
  name: { type: String, required: true },
})

const maskUrl = computed(() => {
  const prefix = nameMap[props.name] ?? props.name
  const entry = Object.entries(iconUrls).find(([path]) => {
    const file = path.split('/').pop()
    return file.startsWith(prefix + '_') || file === prefix + '.svg'
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
