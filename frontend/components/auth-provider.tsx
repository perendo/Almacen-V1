"use client"

import { createContext, useCallback, useContext, useEffect, useState, ReactNode } from "react"
import { api } from "@/lib/api"
import type { UserOut } from "@/types/auth"

const ROLES_CACHE_KEY = "wms_user_roles"

interface AuthContextType {
  token: string | null
  user: UserOut | null
  roles: string[]
  isAuthenticated: boolean
  loading: boolean
  login: (token: string) => void
  logout: () => void
  refreshUser: () => Promise<void>
  hasRole: (role: string | string[]) => boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

function readTokenRoles(token: string): string[] {
  try {
    const payload = JSON.parse(atob(token.split(".")[1]))
    return Array.isArray(payload?.roles) ? payload.roles : []
  } catch {
    return []
  }
}

function cacheRoles(roles: string[]) {
  if (typeof window === "undefined") return
  try {
    localStorage.setItem(ROLES_CACHE_KEY, JSON.stringify(roles))
  } catch {
    // el almacenamiento puede no estar disponible (modo privado, cuota)
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setTokenState] = useState<string | null>(null)
  const [user, setUser] = useState<UserOut | null>(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [loading, setLoading] = useState(true)

  const applyUser = useCallback((profile: UserOut) => {
    setUser(profile)
    cacheRoles(profile.roles ?? [])
  }, [])

  const refreshUser = useCallback(async () => {
    try {
      const me = await api.get<UserOut>("/auth/me")
      applyUser(me)
    } catch {
      // Si /auth/me falla se mantienen los datos del token como respaldo.
    }
  }, [applyUser])

  useEffect(() => {
    const storedToken = localStorage.getItem("access_token")
    if (storedToken) {
      setTokenState(storedToken)
      setIsAuthenticated(true)
      try {
        const payload = JSON.parse(atob(storedToken.split(".")[1]))
        setUser({
          id: payload.user_id,
          email: payload.email ?? payload.sub,
          full_name: payload.full_name ?? "",
          is_active: true,
          company_id: payload.company_id ?? null,
          roles: Array.isArray(payload.roles) ? payload.roles : [],
        } as UserOut)
      } catch {
        setUser(null)
      }
      // El perfil real (con los roles vigentes) manda sobre el JWT.
      void refreshUser()
    }
    setLoading(false)
  }, [refreshUser])

  const login = (newToken: string) => {
    localStorage.setItem("access_token", newToken)
    setTokenState(newToken)
    setIsAuthenticated(true)
    try {
      const payload = JSON.parse(atob(newToken.split(".")[1]))
      setUser({
        id: payload.user_id,
        email: payload.email ?? payload.sub,
        full_name: payload.full_name ?? "",
        is_active: true,
        company_id: payload.company_id ?? null,
        roles: Array.isArray(payload.roles) ? payload.roles : [],
      } as UserOut)
    } catch {
      setUser(null)
    }
    void refreshUser()
  }

  const logout = () => {
    // Revocar el refresh token en el servidor (best-effort) antes de limpiar
    // el almacenamiento local. Si la red falla, la sesión local se cierra igual.
    const refreshToken = localStorage.getItem("refresh_token")
    void api
      .post("/auth/logout", refreshToken ? { refresh_token: refreshToken } : {})
      .catch(() => undefined)

    localStorage.removeItem("access_token")
    localStorage.removeItem("refresh_token")
    localStorage.removeItem(ROLES_CACHE_KEY)
    document.cookie = "access_token=; path=/; max-age=0; samesite=lax"
    setTokenState(null)
    setUser(null)
    setIsAuthenticated(false)
  }

  const roles = user?.roles ?? (token ? readTokenRoles(token) : [])

  const hasRole = (role: string | string[]) => {
    const required = Array.isArray(role) ? role : [role]
    return required.some((name) => roles.includes(name))
  }

  return (
    <AuthContext.Provider
      value={{ token, user, roles, isAuthenticated, loading, login, logout, refreshUser, hasRole }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider")
  return ctx
}
