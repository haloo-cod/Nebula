import avatarImage from '@/assets/img/test2.jpg'
import coverImg from '@/assets/img/test5.PNG'
import type { Profile, SocialLink } from '@/types'

// 头像图片(由 Vite 处理为最终 URL)
export const avatar: string = avatarImage

// 关于页封面图
export const coverImage: string = coverImg

// 站点作者资料
export const profile: Profile = {
  name: 'Starlit',
  bio: '分享技术、生活和思考的个人博客',
}

// 社交链接列表(icon 对应 SvgIcon 的 name)
export const socialLinks: SocialLink[] = [
  { label: 'GitHub', icon: 'github', url: 'https://github.com' },
  { label: 'Bilibili', icon: 'bilibili', url: 'https://space.bilibili.com' },
]
