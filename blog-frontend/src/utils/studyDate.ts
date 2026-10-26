/** 获取自习室逻辑日期：按本地时间计算，凌晨 4:00 前归入前一天。 */
export function getLogicalDate(now: Date = new Date()): string {
  const day = new Date(now.getTime())
  if (day.getHours() < 4) day.setDate(day.getDate() - 1)
  const year = String(day.getFullYear()).padStart(4, '0')
  const month = String(day.getMonth() + 1).padStart(2, '0')
  const date = String(day.getDate()).padStart(2, '0')
  return `${year}-${month}-${date}`
}
