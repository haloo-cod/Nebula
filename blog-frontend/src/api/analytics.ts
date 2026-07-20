/** 访问统计上报 API。 */
import { api } from './client'

/** 单日访问趋势。 */
export interface AnalyticsTrendItem {
  date: string
  pv: number
  uv: number
}

/** 前台可展示的访问统计聚合数据。 */
export interface AnalyticsPublicSummary {
  today_pv: number
  today_uv: number
  total_pv: number
  total_uv: number
  trend: AnalyticsTrendItem[]
}

/** 上报一次公开访问行为。 */
export function recordAnalyticsEvent(data: {
  event_type: string
  path: string
  title?: string
  referrer?: string
  visitor_id?: string
}): Promise<void> {
  return api.post<void>('/api/v1/analytics/events', data)
}

/** 获取前台访问统计聚合数据。 */
export function fetchPublicAnalyticsSummary(): Promise<AnalyticsPublicSummary> {
  return api.get<AnalyticsPublicSummary>('/api/v1/analytics/public-summary')
}
