const API_BASE = import.meta.env.VITE_API_BASE ?? ""

interface RequestOptions extends RequestInit {
  skipAuth?: boolean
}

async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { skipAuth = false, headers: extraHeaders, ...rest } = options

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((extraHeaders as Record<string, string>) ?? {}),
  }

  if (!skipAuth) {
    const token = localStorage.getItem("access_token")
    if (token) {
      headers["Authorization"] = `Bearer ${token}`
    }
  }

  const res = await fetch(`${API_BASE}${endpoint}`, { headers, ...rest })

  if (res.status === 401) {
    localStorage.removeItem("access_token")
    window.location.href = "/login"
    throw new Error("Unauthorized")
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.message ?? `Request failed: ${res.status}`)
  }

  return res.json() as Promise<T>
}

export const api = {
  get: <T>(url: string, opts?: RequestOptions) => request<T>(url, { method: "GET", ...opts }),
  post: <T>(url: string, body?: unknown, opts?: RequestOptions) =>
    request<T>(url, { method: "POST", body: JSON.stringify(body), ...opts }),
  put: <T>(url: string, body?: unknown, opts?: RequestOptions) =>
    request<T>(url, { method: "PUT", body: JSON.stringify(body), ...opts }),
  delete: <T>(url: string, opts?: RequestOptions) =>
    request<T>(url, { method: "DELETE", ...opts }),
}
