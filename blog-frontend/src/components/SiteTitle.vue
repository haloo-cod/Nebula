<template>
  <div class="site-title" :class="sizeClass" translate="no">
    <h1 class="font-bold text-white tracking-wider select-none">
      {{ displayed }}<span class="caret" :class="{ 'caret-blink': done }">|</span>
    </h1>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useTypewriter } from '@/composables/useTypewriter'

const props = defineProps({
  text: { type: String, default: "Starlitn'blog" },
  size: { type: String, default: 'lg' }, // 'lg' 桌面大标题 | 'sm' 移动端
  instant: { type: Boolean, default: false },
})

const { displayed, done } = useTypewriter(props.text, { instant: props.instant })

const sizeClass = computed(() => (props.size === 'sm' ? 'title-sm' : 'title-lg'))
</script>

<style scoped>
.site-title {
  text-align: center;
}

.title-lg h1 {
  font-size: 2.25rem;
}

@media (min-width: 640px) {
  .title-lg h1 {
    font-size: 3rem;
  }
}

@media (min-width: 768px) {
  .title-lg h1 {
    font-size: 4.5rem;
  }
}

.title-sm h1 {
  font-size: 1.875rem;
}

.caret {
  font-weight: 400;
}

.caret-blink {
  animation: caret-pulse 1s step-end infinite;
}

@keyframes caret-pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0;
  }
}
</style>
