import type { UserOut } from "./auth"

export interface Role {
  id: number
  name: string
  description: string | null
  scope: string
  is_system: boolean
}

export interface Permission {
  id: number
  resource: string
  action: string
}

export interface UserRole {
  id: number
  user_id: number
  role_id: number
  company_id: number | null
  warehouse_id: number | null
}

export interface UserWithRoles extends UserOut {
  user_roles: UserRole[]
}