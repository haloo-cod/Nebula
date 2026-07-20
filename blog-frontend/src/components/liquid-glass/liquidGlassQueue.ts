/**
 * 液态玻璃纹理上传协调模块
 *
 * 在新架构中,纹理由共享渲染器统一管理,此模块仅保留
 * waitForNextTextureUploadSettled / waitForTextureUploadQueueIdle 接口
 * 供 UI store 的 toggleTheme 使用。
 *
 * 实现方式：监听渲染器的纹理就绪事件。
 */

import { waitForTexture, hasTexture } from '@/components/liquid-glass/liquidGlassRenderer'
import darkBgUrl from '@/assets/img/test3.jpg'
import lightBgUrl from '@/assets/img/test6.PNG'

/** 等待下次纹理上传完成（主题切换时调用,等待新主题纹理就绪） */
export function waitForNextTextureUploadSettled(timeoutMs = 1200): Promise<void> {
  // 在新架构中,等待当前主题对应的两个纹理 URL 就绪即可
  // toggleTheme 在调用此函数前已经切换了 theme,此时需要等待的是新 theme 的纹理
  // 由于调用方无法传入具体 URL,我们等待两个纹理都就绪（它们通常已经预加载好了）
  return Promise.race([
    Promise.all([
      hasTexture(darkBgUrl) ? Promise.resolve() : waitForTexture(darkBgUrl, timeoutMs),
      hasTexture(lightBgUrl) ? Promise.resolve() : waitForTexture(lightBgUrl, timeoutMs),
    ]).then(() => {}),
    new Promise<void>((resolve) => setTimeout(resolve, timeoutMs)),
  ])
}

/** 等待纹理上传队列空闲（在新架构中纹理上传是同步的,直接 resolve） */
export function waitForTextureUploadQueueIdle(): Promise<void> {
  return Promise.resolve()
}

/** 兼容旧接口：等待首个纹理就绪 */
export function waitForFirstTextureUploadSettled(): Promise<void> {
  if (hasTexture(darkBgUrl) || hasTexture(lightBgUrl)) {
    return Promise.resolve()
  }
  return Promise.race([waitForTexture(darkBgUrl, 1200), waitForTexture(lightBgUrl, 1200)])
}
