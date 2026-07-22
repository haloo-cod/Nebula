/**
 * 背景图 API
 * 对应后端 /api/v1/backgrounds 路由
 */

import { api, resolveUrl } from './client'

/** 后端返回的背景图条目 */
export interface ApiBgItem {
  id: number
  url: string
  theme: string
  device: string
  sort_order: number
  created_at: string
}

/** 背景图列表响应 */
interface BgListResponse {
  items: ApiBgItem[]
  total: number
}

/**
 * 获取背景图列表（按 theme + device 筛选）
 * 返回已排序的背景图数组，url 已补全为完整可访问地址
 */
export async function fetchBackgrounds(theme: string, device: string): Promise<ApiBgItem[]> {
  const resp = await api.get<BgListResponse>(`/api/v1/backgrounds?theme=${theme}&device=${device}`)
  // 补全 url 为完整路径
  return resp.items.map((item) => ({
    ...item,
    url: resolveUrl(item.url),
  }))
}
