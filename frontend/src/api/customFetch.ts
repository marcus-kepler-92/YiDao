/**
 * Custom fetch for Orval-generated API client.
 * Injects VITE_API_BASE and Bearer token; handles 401 by clearing token and redirecting to login.
 */

const API_BASE = import.meta.env.VITE_API_BASE ?? ""

export const customFetch = async <T>(url: string, options: RequestInit = {}): Promise<T> => {
  const token = localStorage.getItem("access_token")
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  }
  if (!headers["Content-Type"] && options.body instanceof FormData === false && options.body instanceof URLSearchParams === false) {
    headers["Content-Type"] = "application/json"
  }
  if (token) {
    headers["Authorization"] = `Bearer ${token}`
  }

  const fullUrl = API_BASE ? `${API_BASE.replace(/\/$/, "")}${url}` : url
  const res = await fetch(fullUrl, { ...options, headers })

  if (res.status === 401) {
    localStorage.removeItem("access_token")
    window.location.href = "/login"
    throw new Error("Unauthorized")
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error((body as { message?: string }).message ?? `Request failed: ${res.status}`)
  }

  const data = await res.json()
  return { status: res.status, data } as T
}
