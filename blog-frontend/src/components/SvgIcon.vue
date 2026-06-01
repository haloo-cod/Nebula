<template>
  <span class="svg-icon" :style="{ '--icon-url': maskUrl }" aria-hidden="true"></span>
</template>

<script setup>
import { computed } from 'vue'

// 一次性收集 iconfont 下所有 svg 的最终 URL
// 注意：import.meta.glob 的模式必须是相对路径，不支持 @ 别名
const iconUrls = import.meta.glob('../assets/iconfont/*.svg', {
  query: '?url',
  import: 'default',
  eager: true,
})

const props = defineProps({
  name: { type: String, required: true },
})

const maskUrl = computed(() => {
  const entry = Object.entries(iconUrls).find(([path]) => path.endsWith(`/${props.name}.svg`))
  return entry ? `url("${entry[1]}")` : 'none'
})
</script>

<style scoped>
/* 用 mask 渲染单色图标，颜色跟随 currentColor，可随选中态变化
   通过 CSS 变量注入 url，避免 Vue 内联样式无法正确输出 -webkit- 前缀的问题 */
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
