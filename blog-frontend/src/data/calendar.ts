// 日历数据:节假日(timor.tech 在线 API)+ 24 节气(lunar-typescript 本地计算)
import { Solar } from 'lunar-typescript'
import type { HolidayApiInfo, HolidayApiResponse, HolidayDay } from '@/types'

// ---------- 节气(离线计算)----------
// 给定年月,返回 { 日: '节气名' } 映射,例如 { 5: '芒种', 21: '夏至' }
export function getSolarTerms(year: number, month: number): Record<number, string> {
  const result: Record<number, string> = {}
  const daysInMonth = new Date(year, month, 0).getDate() // month 为 1-12
  for (let day = 1; day <= daysInMonth; day++) {
    const jieqi = Solar.fromYmd(year, month, day).getLunar().getJieQi()
    if (jieqi) result[day] = jieqi
  }
  return result
}

// ---------- 节假日(在线 API + 缓存)----------
// timor.tech 返回整年数据,key 为 'MM-DD'
const holidayCache = new Map<number, Record<string, HolidayApiInfo>>()

/**
 * 获取指定年份的整年节假日数据(带缓存,失败时降级为空)
 * @param year 年份
 * @returns key 为 'MM-DD' 的节假日映射
 */
export async function getHolidays(year: number): Promise<Record<string, HolidayApiInfo>> {
  const cached = holidayCache.get(year)
  if (cached) return cached
  try {
    const res = await fetch(`https://timor.tech/api/holiday/year/${year}`, {
      headers: { Accept: 'application/json' },
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    // 外部 API 返回值无类型,按已知外形断言(见 types/HolidayApiResponse)
    const json = (await res.json()) as HolidayApiResponse
    const data = json.holiday || {}
    holidayCache.set(year, data)
    return data
  } catch (e) {
    console.warn('[calendar] 节假日加载失败,降级为无节假日显示:', e)
    holidayCache.set(year, {})
    return {}
  }
}

// 从整年节假日数据中提取指定月份的映射
// 返回 { 日: { name, isOff, isWork } }
// isOff: 放假日;isWork: 调休补班日
export function pickMonthHolidays(
  yearData: Record<string, HolidayApiInfo>,
  month: number,
): Record<number, HolidayDay> {
  const result: Record<number, HolidayDay> = {}
  const mm = String(month).padStart(2, '0')
  for (const [key, info] of Object.entries(yearData)) {
    if (!key.startsWith(`${mm}-`)) continue
    const day = Number(key.slice(3))
    result[day] = {
      name: info.name,
      isOff: info.holiday === true,
      isWork: info.holiday === false,
    }
  }
  return result
}
