<script setup lang="ts">
/** 两套玻璃布局共用的本站信息，每个按钮只复制所在行的字段值。 */
import { computed, ref, watch } from 'vue'
import type { FriendExchangeInfo } from '@/api/friends'
import '@/assets/styles/exchange-site-info.css'

/** 交换信息的单行展示与复制内容。 */
interface ExchangeInfoLine {
  key: string
  label: string
  copyLabel: string
  value: string
  className: string
  link?: boolean
}

const props = defineProps<{ info: FriendExchangeInfo; rssUrl: string }>()
const copied = ref('')
/** 复制期间只锁定重复调用，按钮外观保持稳定，避免整列明暗闪烁。 */
const copying = ref(false)
const error = ref('')
const announcement = ref('')
const lines = computed<ExchangeInfoLine[]>(() =>
  [
    {
      key: 'name',
      label: '',
      copyLabel: '站点名称',
      value: props.info.name,
      className: 'exchange-site-name',
    },
    {
      key: 'url',
      label: '站点',
      copyLabel: '站点地址',
      value: props.info.url,
      className: 'exchange-site-url',
    },
    {
      key: 'bio',
      label: '简介',
      copyLabel: '简介',
      value: props.info.bio,
      className: 'exchange-site-bio',
    },
    {
      key: 'avatar',
      label: '头像',
      copyLabel: '头像地址',
      value: props.info.avatar,
      className: 'exchange-site-avatar-url',
    },
    {
      key: 'rss',
      label: 'RSS',
      copyLabel: 'RSS 地址',
      value: props.rssUrl,
      className: 'exchange-site-rss',
      link: true,
    },
  ].filter((line) => line.key !== 'rss' || Boolean(line.value)),
)

/** 剪贴板只写入当前字段值，不包含标签或其他行。 */
async function copyLine(line: ExchangeInfoLine) {
  if (!line.value || copying.value) return
  copying.value = true
  error.value = ''
  try {
    await navigator.clipboard.writeText(line.value)
    copied.value = line.key
    announcement.value = `${line.copyLabel}已复制`
  } catch {
    copied.value = ''
    announcement.value = ''
    error.value = '复制失败，请手动选择这一行文字复制。'
  } finally {
    copying.value = false
  }
}

watch([() => props.info, () => props.rssUrl], () => {
  copied.value = ''
  announcement.value = ''
  error.value = ''
})
</script>

<template>
  <div class="exchange-site-info">
    <component
      :is="line.key === 'name' ? 'h3' : 'p'"
      v-for="line in lines"
      :key="line.key"
      :class="['exchange-info-row', line.className]"
    >
      <span class="exchange-info-value">
        <span v-if="line.label">{{ line.label }}：</span
        ><a v-if="line.link" :href="line.value" target="_blank" rel="noopener noreferrer">{{
          line.value
        }}</a
        ><span v-else>{{ line.value }}</span>
      </span>
      <button
        type="button"
        class="exchange-copy-button"
        :aria-label="`复制${line.copyLabel}`"
        :title="copied === line.key ? '已复制' : `复制${line.copyLabel}`"
        :disabled="!line.value"
        @click="copyLine(line)"
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.7"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        >
          <path v-if="copied === line.key" d="m5 12 4 4L19 6" />
          <template v-else>
            <rect x="9" y="9" width="11" height="11" rx="2" />
            <path d="M15 5V4a1 1 0 0 0-1-1H4a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h1" />
          </template>
        </svg>
      </button>
    </component>
    <span class="sr-only" role="status" aria-live="polite">{{ announcement }}</span>
    <p v-if="error" class="exchange-copy-error" role="alert">{{ error }}</p>
  </div>
</template>
