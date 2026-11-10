// Browser HTTP transport adapter; feature APIs do not call fetch directly.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, options)
  if (response.status === 204) return undefined as T

  const result: unknown = await response.json().catch(() => null)
  if (!response.ok) {
    const detail = typeof result === 'object' && result !== null && 'detail' in result
      ? result.detail
      : undefined
    throw new Error(
      typeof detail === 'string' ? detail : `Request failed (${response.status})`,
    )
  }
  return result as T
}
