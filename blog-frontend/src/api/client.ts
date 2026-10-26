/**
 * HTTP 客户端封装
 * 统一处理 baseURL、认证 token、错误响应
 */

const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL

/**
 * API 根地址。
 *
 * - 开发期默认直连 localhost:8000；如启用上面的 Vite 代理，可将
 *   VITE_API_BASE_URL 设为空字符串，让请求走同源代理，方便局域网预览。
 * - 生产或直连部署：在 .env 中填写完整的后端地址（如 https://api.example.com）。
 */
export const BASE_URL =
  configuredBaseUrl !== undefined && configuredBaseUrl !== ''
    ? configuredBaseUrl.replace(/\/+$/, '')
    : ''
const TOKEN_KEY = 'blog_admin_token'

/** 令牌变更订阅；刷新只轮换令牌，登录和登出会替换整个会话。 */
type TokenListener = (token: string | null, sessionChanged: boolean) => void
const tokenListeners = new Set<TokenListener>()
let sessionVersion = 0

/** 刷新接口的令牌响应。 */
interface RefreshResponse {
  access_token: string
  token_type: string
}

let refreshFlight: { version: number; promise: Promise<RefreshResponse> } | null = null

/**
 * API 开关：通过环境变量 VITE_USE_API 控制
 * 设为 'false' 时所有 API 请求自动失败，触发各页面的 fallback 逻辑
 * 默认为 true（启用 API）
 */
export const USE_API = import.meta.env.VITE_USE_API !== 'false'

/** 将后端相对路径补全为完整 URL（图片/文件等静态资源） */
export function resolveUrl(url: string): string {
  if (!url) return ''
  if (url.startsWith('http')) return url
  const path = url.startsWith('/') ? url : `/${url}`
  return encodeURI(`${BASE_URL}${path}`)
}

/** 从 localStorage 获取 JWT */
export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

function updateToken(token: string | null, sessionChanged: boolean): void {
  if (sessionChanged) sessionVersion += 1
  if (token) localStorage.setItem(TOKEN_KEY, token)
  else localStorage.removeItem(TOKEN_KEY)
  tokenListeners.forEach((listener) => listener(token, sessionChanged))
}

/** 存储新登录会话的 JWT，并同步登录界面。 */
export function setToken(token: string): void {
  updateToken(token, true)
}

/** 清除 JWT 和订阅方的用户信息。 */
export function clearToken(): void {
  updateToken(null, true)
}

/** 订阅令牌轮换或会话失效，返回取消订阅函数。 */
export function subscribeToken(listener: TokenListener): () => void {
  tokenListeners.add(listener)
  return () => tokenListeners.delete(listener)
}

/** API 错误类 */
export class ApiError extends Error {
  status: number
  detail: string

  constructor(status: number, detail: string) {
    super(detail)
    this.status = status
    this.detail = detail
  }
}

function responseError(status: number, text: string): ApiError {
  let detail = `请求失败 (${status})`
  try {
    const body: unknown = JSON.parse(text)
    if (body && typeof body === 'object' && 'detail' in body && body.detail) {
      detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)
    }
  } catch {
    // 非 JSON 错误页保留状态码。
  }
  return new ApiError(status, detail)
}

/** 仅信任配置的 API 源和本站的相对 API 路径。 */
function isApiUrl(url: string): boolean {
  try {
    const target = new URL(url, window.location.href)
    const base = new URL(BASE_URL || '/', window.location.href)
    return (
      (target.protocol === 'http:' || target.protocol === 'https:') &&
      (target.origin === base.origin ||
        (target.origin === window.location.origin && target.pathname.startsWith('/api/')))
    )
  } catch {
    return false
  }
}

/** 所有请求共享同一次 Cookie 刷新；过期响应不能覆盖后续登录。 */
export async function refreshAccessToken(): Promise<RefreshResponse> {
  const version = sessionVersion
  const token = getToken()
  if (refreshFlight) {
    if (refreshFlight.version === version) return refreshFlight.promise
    // 新登录须等旧刷新结束，避免同时轮换 Refresh Cookie。
    try {
      await refreshFlight.promise
    } catch {
      // 旧会话的刷新结果不决定当前会话。
    }
    if (version !== sessionVersion || token !== getToken()) {
      throw new ApiError(401, '登录状态已更改，请重试')
    }
    return refreshAccessToken()
  }

  const promise = (async () => {
    if (!USE_API) throw new ApiError(0, 'API 已禁用（VITE_USE_API=false）')
    const response = await fetch(`${BASE_URL}/api/v1/auth/refresh`, {
      method: 'POST',
      credentials: 'include',
    })
    if (!response.ok) {
      if (
        (response.status === 401 || response.status === 403) &&
        version === sessionVersion &&
        token === getToken()
      ) {
        clearToken()
      }
      throw responseError(response.status, await response.text())
    }
    const refreshed = (await response.json()) as RefreshResponse
    if (version !== sessionVersion || token !== getToken()) {
      throw new ApiError(401, '登录状态已更改，请重试')
    }
    updateToken(refreshed.access_token, false)
    return refreshed
  })()
  refreshFlight = { version, promise }
  try {
    return await promise
  } finally {
    if (refreshFlight?.promise === promise) refreshFlight = null
  }
}

async function withAuthentication<T extends { status: number }>(
  send: (token: string | null) => Promise<T>,
  auth: boolean,
): Promise<T> {
  const version = sessionVersion
  const token = auth ? getToken() : null
  const response = await send(token)
  if (!auth || response.status !== 401 || version !== sessionVersion) return response

  // 迟到的旧 token 响应直接使用已轮换的 token，不再刷新 Cookie。
  if (token === getToken()) await refreshAccessToken()
  if (version !== sessionVersion || !getToken()) return response
  // 重试在刷新之外执行，其 403、网络错误等直接交给调用方。
  return send(getToken())
}

/** 使用共享 401 恢复发送 API 请求，返回原始响应供调用方读取。 */
async function apiFetch(
  path: string,
  options: RequestInit = {},
  auth = false,
): Promise<Response> {
  if (!USE_API) throw new ApiError(0, 'API 已禁用（VITE_USE_API=false）')
  const response = await withAuthentication((token) => {
    const headers = new Headers(options.headers)
    if (auth) {
      headers.delete('Authorization')
      if (token) headers.set('Authorization', `Bearer ${token}`)
    }
    return fetch(`${BASE_URL}${path}`, { ...options, headers, credentials: 'include' })
  }, auth)
  if (!response.ok) throw responseError(response.status, await response.text())
  return response
}

/** XHR 请求参数，供上传和下载保留浏览器进度事件。 */
interface ApiXhrOptions {
  method?: string
  body?: Document | XMLHttpRequestBodyInit | null
  headers?: Record<string, string>
  auth?: boolean
  responseType?: XMLHttpRequestResponseType
  onUploadProgress?: (percent: number) => void
  onDownloadProgress?: (percent: number) => void
}

/** 使用与 fetch 相同的刷新流程发送 XHR；第三方地址不携带认证。 */
export async function apiXhr(url: string, options: ApiXhrOptions = {}): Promise<XMLHttpRequest> {
  const trusted = isApiUrl(url)
  if (trusted && !USE_API) throw new ApiError(0, 'API 已禁用（VITE_USE_API=false）')
  const auth = trusted && (options.auth ?? false)
  const xhr = await withAuthentication((token) => {
    const { promise, resolve, reject } = Promise.withResolvers<XMLHttpRequest>()
    const request = new XMLHttpRequest()
    request.open(options.method ?? 'GET', url)
    request.withCredentials = auth
    request.responseType = options.responseType ?? ''
    Object.entries(options.headers ?? {}).forEach(([key, value]) => {
      if (key.toLowerCase() === 'cookie') return
      if (key.toLowerCase() === 'authorization' && (!trusted || auth)) return
      request.setRequestHeader(key, value)
    })
    if (auth && token) request.setRequestHeader('Authorization', `Bearer ${token}`)
    request.upload.addEventListener('progress', (event) => {
      if (event.lengthComputable) {
        options.onUploadProgress?.(Math.round((event.loaded / event.total) * 100))
      }
    })
    request.addEventListener('progress', (event) => {
      if (event.lengthComputable) {
        options.onDownloadProgress?.(Math.round((event.loaded / event.total) * 100))
      }
    })
    request.addEventListener('load', () => resolve(request))
    request.addEventListener('error', () => reject(new Error('网络错误，请稍后重试')))
    request.addEventListener('abort', () => reject(new Error('请求已取消')))
    request.send(options.body ?? null)
    return promise
  }, auth)
  if (xhr.status < 200 || xhr.status >= 300) {
    const text = xhr.response instanceof Blob ? await xhr.response.text() : xhr.responseText
    throw responseError(xhr.status, text)
  }
  return xhr
}

/** 通用 JSON 请求函数。 */
async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  options?: { auth?: boolean },
): Promise<T> {
  const headers: Record<string, string> = {}
  if (body && !(body instanceof FormData)) headers['Content-Type'] = 'application/json'
  const response = await apiFetch(
    path,
    {
      method,
      headers,
      body: body instanceof FormData ? body : body ? JSON.stringify(body) : undefined,
    },
    options?.auth ?? false,
  )
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

/** 公开的 API 方法 */
export const api = {
  get<T>(path: string, auth = false): Promise<T> {
    return request<T>('GET', path, undefined, { auth })
  },
  post<T>(path: string, body?: unknown, auth = false): Promise<T> {
    return request<T>('POST', path, body, { auth })
  },
  put<T>(path: string, body?: unknown, auth = false): Promise<T> {
    return request<T>('PUT', path, body, { auth })
  },
  patch<T>(path: string, body?: unknown, auth = false): Promise<T> {
    return request<T>('PATCH', path, body, { auth })
  },
  delete<T>(path: string, auth = true): Promise<T> {
    return request<T>('DELETE', path, undefined, { auth })
  },
}
