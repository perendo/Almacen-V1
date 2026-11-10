export interface User {
  id: number
  email: string
  full_name: string
  is_active: boolean
  company_id: number | null
  roles: string[]
}

export interface Company {
  id: number
  name: string
  tax_id: string | null
  currency: string
  fiscal_year_start_month: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Center {
  id: number
  company_id: number
  name: string
  code: string
  address: string | null
  city: string | null
  postal_code: string | null
  country: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Warehouse {
  id: number
  center_id: number
  name: string
  code: string
  type: string
  capacity_volume: number | null
  capacity_weight: number | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Zone {
  id: number
  warehouse_id: number
  name: string
  code: string
  type: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Aisle {
  id: number
  zone_id: number
  name: string
  code: string
}

export interface Shelf {
  id: number
  aisle_id: number
  name: string
  code: string
  level: number
}

export interface Bin {
  id: number
  shelf_id: number
  code: string
  capacity_volume: number | null
  capacity_weight: number | null
  is_active: boolean
  created_at: string
  updated_at: string
}