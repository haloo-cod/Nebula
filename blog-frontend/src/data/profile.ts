import avatarImage from '@/assets/img/test2.jpg'
import type { Profile, SocialLink } from '@/types'

// 头像图片(由 Vite 处理为最终 URL)
export const avatar: string = avatarImage

// 站点作者资料
export const profile: Profile = {
  name: 'Starlit',
  bio: '分享技术、生活和思考的个人博客',
}

// 社交链接列表
export const socialLinks: SocialLink[] = [
  { label: 'GitHub', icon: '🐙', url: 'https://github.com' },
  { label: 'Twitter', icon: '🐦', url: 'https://twitter.com' },
  { label: 'Email', icon: '✉️', url: 'mailto:example@example.com' },
  { label: 'RSS', icon: '📡', url: '/rss' },
]
