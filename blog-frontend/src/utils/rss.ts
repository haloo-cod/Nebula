/** 本站 RSS 接口路径，供前端入口和构建时的自动发现标签共同使用。 */
export const RSS_PATH = '/api/v1/rss.xml'

/** 优先使用自定义地址；空值沿用 API 基址，同域页面可补全站点来源。 */
export function resolveRssUrl(configuredUrl = '', apiBaseUrl = '', siteOrigin = ''): string {
  const base = (apiBaseUrl.trim() || siteOrigin.trim()).replace(/\/+$/, '')
  return configuredUrl.trim() || `${base}${RSS_PATH}`
}
