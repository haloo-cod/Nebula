import type { Friend } from '@/types'

/**
 * 友链静态数据层。 以替换后端接口
 */
const friends: Friend[] = []

/** 获取全部友链 */
export function getFriends(): Friend[] {
  return friends
}
