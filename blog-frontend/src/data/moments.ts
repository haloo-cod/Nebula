import type { Moment, MomentPage } from '@/types'

/** 说说数据由后端 API 提供，保留空 getter 兼容旧代码。 */
export function getMoments(_page = 1, _pageSize = 10): MomentPage {
  return { items: [], total: 0 }
}

/** 获取全部说说，后端数据不可用时返回空数组。 */
export function getAllMoments(): Moment[] {
  return []
}
