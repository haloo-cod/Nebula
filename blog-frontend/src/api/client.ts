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

/** 存储 JWT */
export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

/** 清除 JWT */
export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY)
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

/** 通用请求函数 */
async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  options?: { auth?: boolean; retry?: boolean },
): Promise<T> {
  // API 开关关闭时直接抛异常，触发各页面 fallback
  if (!USE_API) {
    throw new ApiError(0, 'API 已禁用（VITE_USE_API=false）')
  }

  const headers: Record<string, string> = {}
  const auth = options?.auth ?? false

  if (auth) {
    const token = getToken()
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
  }

  if (body && !(body instanceof FormData)) {
    headers['Content-Type'] = 'application/json'
  }

  const response = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body instanceof FormData ? body : body ? JSON.stringify(body) : undefined,
    credentials: 'include',
  })

  if (!response.ok) {
    if (
      response.status === 401 &&
      auth &&
      options?.retry !== false &&
      path !== '/api/v1/auth/refresh'
    ) {
      try {
        const refreshed = await request<{ access_token: string }>(
          'POST',
          '/api/v1/auth/refresh',
          undefined,
          { retry: false },
        )
        setToken(refreshed.access_token)
        return request<T>(method, path, body, { auth, retry: false })
      } catch {
        clearToken()
      }
    }
    let detail = `请求失败 (${response.status})`
    try {
      const errBody = await response.json()
      if (errBody.detail) {
        detail =
          typeof errBody.detail === 'string' ? errBody.detail : JSON.stringify(errBody.detail)
      }
    } catch {
      // 忽略解析错误
    }
    throw new ApiError(response.status, detail)
  }

  // 204 No Content
  if (response.status === 204) {
    return undefined as T
  }

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
