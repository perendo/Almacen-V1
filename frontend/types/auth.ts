export interface Token {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface UserLogin {
  email: string
  password: string
}

export interface UserCreate {
  email: string
  password: string
  full_name: string
  company_id?: number
  role_ids: number[]
}

export interface UserUpdate {
  email?: string
  password?: string
  full_name?: string
  is_active?: boolean
  company_id?: number
}

export interface UserOut {
  id: number
  email: string
  full_name: string
  is_active: boolean
  company_id: number | null
  roles: string[]
}

export interface ChangePassword {
  current_password: string
  new_password: string
}