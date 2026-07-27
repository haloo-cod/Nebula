// ---------------------------------------------------------------------------
// 藏宝阁数据源
// 当前为静态数据，未来接入后端 API 后替换为异步获取。
// ---------------------------------------------------------------------------

import type { Treasure, TreasureCategory } from '@/types'

/** 全部藏宝条目（静态占位示例，可按需替换为真实数据） */
const treasures: Treasure[] = []

/** 获取所有藏宝条目 */
export function getTreasures(): Treasure[] {
  return treasures
}

/** 获取所有分类列表（去重） */
export function getTreasureCategories(): TreasureCategory[] {
  const categories = [...new Set(treasures.map((t) => t.category))]
  return categories
}
