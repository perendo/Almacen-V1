export const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"

export class ApiError extends Error {
  constructor(public status: number, message: string, public data?: any) {
    super(message)
    this.name = "ApiError"
  }
}

let isRefreshing = false
let refreshSubscribers: ((token: string) => void)[] = []

function onRefreshed(token: string) {
  refreshSubscribers.forEach((cb) => cb(token))
  refreshSubscribers = []
}

function addRefreshSubscriber(cb: (token: string) => void) {
  refreshSubscribers.push(cb)
}

async function request<T>(
  input: RequestInfo | URL,
  init?: RequestInit
): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(init?.headers ?? {}),
  }

  const res = await fetch(`${API_BASE}${input instanceof Request ? input.url : input}`, {
    ...init,
    headers,
    cache: "no-store",
  })

  // Si 401 y no estamos ya refrescando, intentar renovar el access token
  if (res.status === 401 && token && typeof window !== "undefined") {
    if (!isRefreshing) {
      isRefreshing = true
      try {
        const refreshToken = localStorage.getItem("refresh_token")
        if (refreshToken) {
          const refreshRes = await fetch(`${API_BASE}/auth/refresh`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ refresh_token: refreshToken }),
          })
          if (refreshRes.ok) {
            const data = await refreshRes.json()
            localStorage.setItem("access_token", data.access_token)
            localStorage.setItem("refresh_token", data.refresh_token)
            isRefreshing = false
            onRefreshed(data.access_token)
            // Reintentar la petición original con el nuevo token
            const newHeaders: HeadersInit = {
              "Content-Type": "application/json",
              Authorization: `Bearer ${data.access_token}`,
              ...(init?.headers ?? {}),
            }
            const retryRes = await fetch(`${API_BASE}${input instanceof Request ? input.url : input}`, {
              ...init,
              headers: newHeaders,
              cache: "no-store",
            })
            if (!retryRes.ok) {
              const body = await retryRes.json().catch(() => null)
              throw new ApiError(retryRes.status, body?.detail ?? retryRes.statusText, body)
            }
            if (retryRes.status === 204) return undefined as T
            return retryRes.json()
          } else {
            // Refresh falló, limpiar sesión
            isRefreshing = false
            localStorage.removeItem("access_token")
            localStorage.removeItem("refresh_token")
            window.location.href = "/login"
            throw new ApiError(401, "Sesión expirada", null)
          }
        } else {
          isRefreshing = false
          throw new ApiError(401, "No hay token de refresco", null)
        }
      } catch (err) {
        isRefreshing = false
        throw err
      }
    } else {
      // Esperar a que se complete el refresh y reintentar
      return new Promise((resolve, reject) => {
        addRefreshSubscriber((newToken) => {
          const newHeaders: HeadersInit = {
            "Content-Type": "application/json",
            Authorization: `Bearer ${newToken}`,
            ...(init?.headers ?? {}),
          }
          fetch(`${API_BASE}${input instanceof Request ? input.url : input}`, {
            ...init,
            headers: newHeaders,
            cache: "no-store",
          })
            .then((retryRes) => {
              if (!retryRes.ok) {
                return retryRes.json().catch(() => null).then((body) => {
                  throw new ApiError(retryRes.status, body?.detail ?? retryRes.statusText, body)
                })
              }
              if (retryRes.status === 204) return undefined as T
              return retryRes.json()
            })
            .then(resolve)
            .catch(reject)
        })
      })
    }
  }

  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new ApiError(res.status, body?.detail ?? res.statusText, body)
  }

  if (res.status === 204) return undefined as T
  return res.json()
}

export const api = {
  get: <T>(path: string, params?: Record<string, string>) => {
    const url = params
      ? `${path}?${new URLSearchParams(params).toString()}`
      : path
    return request<T>(url)
  },
  post: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body) }),
  put: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "PUT", body: JSON.stringify(body) }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
}
