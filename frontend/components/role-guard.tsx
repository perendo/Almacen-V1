import { useAuth } from "@/hooks/useAuth"

export function RoleGuard({ role, children }: { role: string; children: React.ReactNode }) {
  const { isAuthenticated, user } = useAuth()

  if (!isAuthenticated) return null

  const roles = user?.roles ?? []
  if (!roles.includes(role)) return null

  return <>{children}</>
}

export function RoleRedirect({ role, children }: { role: string; children: React.ReactNode }) {
  const { isAuthenticated, user } = useAuth()

  if (!isAuthenticated) return null

  const roles = user?.roles ?? []
  if (roles.includes(role)) return <>{children}</>

  return null
}