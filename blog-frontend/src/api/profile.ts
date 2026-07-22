/**
 * 个人资料 API
 * 对应后端 /api/v1/profile 路由
 */

import { api, resolveUrl } from './client'
import type { Profile, SocialLink } from '@/types'

/** 后端返回的社交链接 */
interface ApiSocialLink {
  id: number
  label: string
  icon: string
  url: string
  sort_order: number
}

/** 后端返回的个人资料 */
interface ApiProfileResponse {
  name: string
  bio: string
  avatar_url: string
  cover_url: string
  social_links: ApiSocialLink[]
}

/** 前端用的完整资料（含头像 URL 和社交链接） */
export interface ProfileData {
  profile: Profile
  avatarUrl: string
  coverUrl: string
  socialLinks: SocialLink[]
}

/** 获取个人资料 */
export async function fetchProfile(): Promise<ProfileData> {
  const resp = await api.get<ApiProfileResponse>('/api/v1/profile')
  return {
    profile: {
      name: resp.name,
      bio: resp.bio,
    },
    avatarUrl: resp.avatar_url ? resolveUrl(resp.avatar_url) : '',
    coverUrl: resp.cover_url ? resolveUrl(resp.cover_url) : '',
    socialLinks: resp.social_links.map((l) => ({
      label: l.label,
      icon: l.icon,
      url: l.url,
    })),
  }
}
