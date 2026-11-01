/**
 * Typed API Client for SchemaSense AI
 */

const DEFAULT_API_BASE_URL =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) || 'http://127.0.0.1:8001'

export function getApiBaseUrl(): string {
  try {
    const customUrl = localStorage.getItem('schemasense_api_base_url')
    if (customUrl && customUrl.trim() !== '') {
      return customUrl.trim().replace(/\/$/, '')
    }
  } catch {
    // Fall back to environment default
  }
  return DEFAULT_API_BASE_URL.replace(/\/$/, '')
}

export function setApiBaseUrl(url: string | null): void {
  try {
    if (!url || url.trim() === '') {
      localStorage.removeItem('schemasense_api_base_url')
    } else {
      localStorage.setItem('schemasense_api_base_url', url.trim())
    }
  } catch {
    // Ignore storage errors
  }
}

export class ApiError extends Error {
  code?: string
  status?: number
  details?: unknown

  constructor(message: string, status?: number, code?: string, details?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.details = details
  }
}

export async function request<T>(
  path: string,
  options: RequestInit = {},
  timeoutMs = 6000
): Promise<T> {
  const baseUrl = getApiBaseUrl()
  const cleanPath = path.startsWith('/') ? path : `/${path}`
  const url = `${baseUrl}${cleanPath}`

  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)

  try {
    const isFormData = options.body instanceof FormData
    const headers: Record<string, string> = {
      Accept: 'application/json',
      ...(!isFormData ? { 'Content-Type': 'application/json' } : {}),
      ...(options.headers as Record<string, string> || {}),
    }

    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers,
    })

    if (!response.ok) {
      let errorData: { error?: { message?: string; code?: string; details?: unknown } } = {}
      try {
        errorData = await response.json()
      } catch {
        // Not JSON
      }
      throw new ApiError(
        errorData?.error?.message || `HTTP ${response.status}: ${response.statusText}`,
        response.status,
        errorData?.error?.code,
        errorData?.error?.details
      )
    }

    return (await response.json()) as T
  } catch (err: unknown) {
    if (err instanceof ApiError) {
      throw err
    }
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new ApiError('Request timed out after 6 seconds. Is the backend running?', 408, 'TIMEOUT')
    }
    const message = err instanceof Error ? err.message : 'Network error connecting to backend'
    throw new ApiError(message, 0, 'NETWORK_ERROR')
  } finally {
    clearTimeout(timer)
  }
}
