import type { Friend } from '@/types'

/**
 * 友链页面的空初始值；真实列表来自数据库 API。
 */
const friends: Friend[] = []

/** 获取全部友链 */
export function getFriends(): Friend[] {
  return friends
}
