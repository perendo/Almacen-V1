export interface Article {
  id: number
  company_id: number
  internal_code: string
  ean13: string | null
  supplier_reference: string | null
  family_id: number | null
  subfamily_id: number | null
  brand_id: number | null
  weight_kg: number | null
  volume_m3: number | null
  length_cm: number | null
  width_cm: number | null
  height_cm: number | null
  is_serialized: boolean
  lot_required: boolean
  abc_class: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ArticleFamily {
  id: number
  company_id: number
  name: string
  code: string
}

export interface ArticleSubfamily {
  id: number
  family_id: number
  name: string
  code: string
}

export interface ArticleBrand {
  id: number
  company_id: number
  name: string
}

export interface Uom {
  id: number
  company_id: number
  code: string
  name: string
  type: string
  is_base: boolean
}

export interface UomConversion {
  id: number
  company_id: number
  from_uom_id: number
  to_uom_id: number
  factor: number
}

export interface ArticlePrice {
  id: number
  article_id: number
  uom_id: number
  price_type: string
  value: number
  currency: string
  valid_from: string | null
  valid_to: string | null
  is_active: boolean
}

export interface ArticleTax {
  id: number
  article_id: number
  tax_type: string
  rate: number
  is_active: boolean
  valid_from: string | null
  valid_to: string | null
}

export interface Lot {
  id: number
  company_id: number
  article_id: number
  lot_number: string
  manufacturing_date: string | null
  expiration_date: string | null
  status: string
  created_at: string
}

export interface SerialNumber {
  id: number
  company_id: number
  article_id: number
  serial_number: string
  lot_id: number | null
  current_bin_id: number | null
  status: string
  created_at: string
  updated_at: string
}

export interface InventoryCount {
  id: number
  company_id: number
  warehouse_id: number
  zone_id: number | null
  count_type: string
  status: string
  counted_by: number | null
  approved_by: number | null
  count_date: string
  approved_at: string | null
  notes: string | null
}

export interface InventoryCountLine {
  id: number
  inventory_count_id: number
  bin_id: number | null
  article_id: number
  lot_id: number | null
  serial_id: number | null
  system_quantity: number
  counted_quantity: number
  difference: number | null
  status: string
  notes: string | null
}

export interface Adjustment {
  id: number
  company_id: number
  warehouse_id: number
  adjustment_type: string
  reason: string
  account_code: string | null
  quantity: number
  uom_id: number
  article_id: number
  lot_id: number | null
  serial_id: number | null
  user_id: number
  approved_by: number | null
  status: string
  created_at: string
  approved_at: string | null
}

export interface Alert {
  id: number
  company_id: number
  alert_type: string
  article_id: number | null
  lot_id: number | null
  bin_id: number | null
  warehouse_id: number | null
  severity: string
  status: string
  message: string | null
  created_at: string
  resolved_at: string | null
  resolved_by: number | null
}

export interface AuditLog {
  id: number
  company_id: number | null
  user_id: number | null
  timestamp: string
  ip: string | null
  action: string
  entity_type: string
  entity_id: number | null
  old_values: string | null
  new_values: string | null
  description: string | null
}