import type { Friend } from '@/types'

/**
 * 友链静态数据层。
 * 当前为演示数据,后续可替换为后端 API 或 CMS 读取。
 */
const friends: Friend[] = [
  {
    name: '暮色工坊',
    bio: '记录前端、设计和一些慢慢变好的日常。',
    avatar: 'https://api.dicebear.com/9.x/adventurer/svg?seed=twilight',
    url: 'https://example.com',
  },
  {
    name: '星河手札',
    bio: '关于 Vue、工程化和个人知识库的碎片笔记。',
    avatar: 'https://api.dicebear.com/9.x/adventurer/svg?seed=galaxy',
    url: 'https://vuejs.org',
  },
  {
    name: '北巷代码',
    bio: '偏爱干净代码,也喜欢把复杂问题讲清楚。',
    avatar: 'https://api.dicebear.com/9.x/adventurer/svg?seed=lane',
    url: 'https://vite.dev',
  },
  {
    name: '浮光档案',
    bio: '照片、旅行和那些值得被保存的小瞬间。',
    avatar: 'https://api.dicebear.com/9.x/adventurer/svg?seed=glimmer',
    url: 'https://developer.mozilla.org',
  },
  {
    name: '青柠实验室',
    bio: '折腾工具、自动化和效率系统的个人实验田。',
    avatar: 'https://api.dicebear.com/9.x/adventurer/svg?seed=lime',
    url: 'https://github.com',
  },
  {
    name: '半夏书房',
    bio: '读书、写作和偶尔出现的技术长文。',
    avatar: 'https://api.dicebear.com/9.x/adventurer/svg?seed=summer',
    url: 'https://www.wikipedia.org',
  },
]

/** 获取全部友链 */
export function getFriends(): Friend[] {
  return friends
}
