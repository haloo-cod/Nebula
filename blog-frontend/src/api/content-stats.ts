/** 主页内容统计 API。 */
import { api } from './client'

/** 公开主页展示的内容数量统计。 */
export interface ContentStats {
  posts: number
  moments: number
  gallery_projects: number
  active_days: number
}

/** 获取主页内容统计。 */
export function fetchContentStats(): Promise<ContentStats> {
  return api.get<ContentStats>('/api/v1/content-stats')
}
