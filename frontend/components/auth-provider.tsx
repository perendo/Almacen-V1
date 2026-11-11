"use client"

import { createContext, useContext, useEffect, useState, ReactNode } from "react"
import { api } from "@/lib/api"
import type { UserOut } from "@/types/auth"

interface AuthContextType {
  token: string | null
  user: UserOut | null
  isAuthenticated: boolean
  loading: boolean
  login: (token: string) => void
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setTokenState] = useState<string | null>(null)
  const [user, setUser] = useState<UserOut | null>(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const t = localStorage.getItem("access_token")
    if (t) {
      setTokenState(t)
      setIsAuthenticated(true)
      try {
        const payload = JSON.parse(atob(t.split(".")[1]))
        setUser({
          id: payload.user_id,
          email: payload.email ?? payload.sub,
          full_name: payload.full_name ?? "",
          is_active: true,
          company_id: payload.company_id ?? null,
          roles: payload.roles ?? [],
        } as UserOut)
        // Cargar perfil completo desde el backend para tener roles y datos actualizados
        void api
          .get<UserOut>("/auth/me")
          .then((me) => setUser(me))
          .catch(() => {
            // Si /auth/me falla, mantener los datos del token
          })
      } catch {
        setUser(null)
      }
    }
    setLoading(false)
  }, [])

  const login = (token: string) => {
    localStorage.setItem("access_token", token)
    setTokenState(token)
    setIsAuthenticated(true)
    try {
      const payload = JSON.parse(atob(token.split(".")[1]))
      setUser({
        id: payload.user_id,
        email: payload.email ?? payload.sub,
        full_name: payload.full_name ?? "",
        is_active: true,
        company_id: payload.company_id ?? null,
        roles: payload.roles ?? [],
      } as UserOut)
      void api
        .get<UserOut>("/auth/me")
        .then((me) => setUser(me))
        .catch(() => {})
    } catch {
      setUser(null)
    }
  }

  const logout = () => {
    localStorage.removeItem("access_token")
    localStorage.removeItem("refresh_token")
    document.cookie = "access_token=; path=/; max-age=0; samesite=lax"
    setTokenState(null)
    setUser(null)
    setIsAuthenticated(false)
  }

  return (
    <AuthContext.Provider value={{ token, user, isAuthenticated, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider")
  return ctx
}
