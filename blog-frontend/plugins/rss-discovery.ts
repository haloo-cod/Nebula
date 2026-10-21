import type { Plugin } from 'vite'
import { resolveRssUrl } from '../src/utils/rss'

/** 将本站 RSS 链接写进静态 HTML，使不执行 JavaScript 的阅读器也能发现订阅。 */
export function rssDiscovery(): Plugin {
  let feedUrl = resolveRssUrl()
  return {
    name: 'rss-discovery',
    configResolved(config) {
      feedUrl = resolveRssUrl('', String(config.env.VITE_API_BASE_URL ?? ''))
    },
    transformIndexHtml() {
      return [
        {
          tag: 'link',
          attrs: {
            rel: 'alternate',
            type: 'application/rss+xml',
            title: "Starlitn'blog RSS",
            href: feedUrl,
          },
          injectTo: 'head',
        },
      ]
    },
  }
}
