// 日历数据：节假日（timor.tech 在线 API）+ 24 节气（lunar-typescript 本地计算）
import { Solar } from 'lunar-typescript'

// ---------- 节气（离线计算）----------
// 给定年月，返回 { '日': '节气名' } 映射，例如 { 5: '芒种', 21: '夏至' }
export function getSolarTerms(year, month) {
  const result = {}
  const daysInMonth = new Date(year, month, 0).getDate() // month 为 1-12
  for (let day = 1; day <= daysInMonth; day++) {
    const jieqi = Solar.fromYmd(year, month, day).getLunar().getJieQi()
    if (jieqi) result[day] = jieqi
  }
  return result
}

// ---------- 节假日（在线 API + 缓存）----------
// timor.tech 返回整年数据，key 为 'MM-DD'
const holidayCache = new Map()

export async function getHolidays(year) {
  if (holidayCache.has(year)) return holidayCache.get(year)
  try {
    const res = await fetch(`https://timor.tech/api/holiday/year/${year}`, {
      headers: { Accept: 'application/json' },
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const json = await res.json()
    const data = json.holiday || {}
    holidayCache.set(year, data)
    return data
  } catch (e) {
    console.warn('[calendar] 节假日加载失败，降级为无节假日显示:', e)
    holidayCache.set(year, {})
    return {}
  }
}

// 从整年节假日数据中提取指定月份的映射
// 返回 { 日: { name, isOff, isWork } }
// isOff: 放假日；isWork: 调休补班日
export function pickMonthHolidays(yearData, month) {
  const result = {}
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
