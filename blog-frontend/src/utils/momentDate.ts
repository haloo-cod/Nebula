/** 说说时间按 UTC 解析，并固定使用北京时间展示。 */
const SHANGHAI_TIME_ZONE = 'Asia/Shanghai'

const formatter = new Intl.DateTimeFormat('zh-CN', {
  timeZone: SHANGHAI_TIME_ZONE,
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit',
  hourCycle: 'h23',
})

/** 兼容迁移前无时区的说说时间，按 UTC 解释。 */
export function parseMomentDate(value: string): Date | null {
  const normalized = /(?:[zZ]|[+-]\d{2}:\d{2})$/.test(value) ? value : `${value}Z`
  const date = new Date(normalized)
  return Number.isNaN(date.getTime()) ? null : date
}

/** 格式化为上海墙上时间，避免受访客设备时区影响。 */
export function formatMomentDate(value: string): string {
  const date = parseMomentDate(value)
  if (!date) return value.replace('T', ' ').slice(0, 19)
  const parts = Object.fromEntries(formatter.formatToParts(date).map(({ type, value }) => [type, value]))
  return `${parts.year}-${parts.month}-${parts.day} ${parts.hour}:${parts.minute}:${parts.second}`
}

/** 为说说卡片和首页轮播格式化相对时间。 */
export function formatMomentRelativeTime(value: string, now = Date.now()): string {
  const date = parseMomentDate(value)
  if (!date) return value
  const diff = now - date.getTime()
  if (diff < 60_000) return '刚刚'
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}分钟前`
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}小时前`
  if (diff < 3 * 86_400_000) return `${Math.floor(diff / 86_400_000)}天前`
  return formatMomentDate(value).slice(0, 16)
}
