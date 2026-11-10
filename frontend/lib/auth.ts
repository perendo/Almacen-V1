export function getToken(): string | null {
  if (typeof window === "undefined") return null
  return localStorage.getItem("access_token")
}

export function setToken(token: string) {
  if (typeof window === "undefined") return
  localStorage.setItem("access_token", token)
  // Cookie accesible por el middleware (que se ejecuta en el servidor y no
  // puede leer localStorage). Sin ella, recargar /dashboard redirige a /login.
  document.cookie = `access_token=${token}; path=/; max-age=${7 * 24 * 60 * 60}; samesite=lax`
}

export function setRefreshToken(token: string) {
  if (typeof window === "undefined") return
  localStorage.setItem("refresh_token", token)
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null
  return localStorage.getItem("refresh_token")
}

export function logout() {
  if (typeof window === "undefined") return
  localStorage.removeItem("access_token")
  localStorage.removeItem("refresh_token")
  document.cookie = "access_token=; path=/; max-age=0; samesite=lax"
  window.location.href = "/login"
}

export function decodeJWT(token: string): any {
  try {
    const payload = token.split(".")[1]
    if (!payload) return null
    return JSON.parse(atob(payload))
  } catch {
    return null
  }
}

export function getUserRoles(): string[] {
  const token = getToken()
  if (!token) return []
  const payload = decodeJWT(token)
  return payload?.roles ?? []
}

export function hasRole(role: string): boolean {
  return getUserRoles().includes(role)
}

export function isSuperAdmin(): boolean {
  return hasRole("SuperAdmin")
}

export function isWarehouseManager(): boolean {
  return hasRole("Gerente de Almacén")
}

export function isWarehouseOperator(): boolean {
  return hasRole("Operario de Almacén")
}

export function isAuditor(): boolean {
  return hasRole("Auditor")
}