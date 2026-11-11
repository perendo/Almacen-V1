import type { ReactNode } from "react"
import { useAuth } from "@/hooks/useAuth"

interface RoleGuardProps {
  /** Rol o lista de roles que pueden ver el contenido (basta con uno). */
  role?: string | string[]
  roles?: string[]
  fallback?: ReactNode
  children: ReactNode
}

/**
 * Muestra `children` solo si el usuario autenticado tiene alguno de los roles
 * indicados. Los roles se leen del perfil devuelto por `GET /auth/me`
 * (cargado por AuthProvider), no exclusivamente del JWT.
 */
export function RoleGuard({ role, roles, fallback = null, children }: RoleGuardProps) {
  const { isAuthenticated, hasRole } = useAuth()

  if (!isAuthenticated) return <>{fallback}</>

  const required = roles ?? (role ? (Array.isArray(role) ? role : [role]) : [])
  if (required.length === 0 || !hasRole(required)) return <>{fallback}</>

  return <>{children}</>
}

export function RoleRedirect({ role, roles, children }: Omit<RoleGuardProps, "fallback">) {
  const { isAuthenticated, hasRole } = useAuth()

  if (!isAuthenticated) return null

  const required = roles ?? (role ? (Array.isArray(role) ? role : [role]) : [])
  if (required.length === 0 || hasRole(required)) return <>{children}</>

  return null
}
