export type StockMovementType = "entry" | "exit" | "internal_transfer" | "adjustment"
export type StockStatus = "available" | "quarantined" | "blocked"

export interface StockOut {
  id: number
  warehouse_id: number
  bin_id: number | null
  article_id: number
  lot_id: number | null
  serial_id: number | null
  quantity: number
  uom_id: number
  reserved_quantity: number
  available_quantity: number
  status: StockStatus
  updated_at: string
}

export interface StockEntryCreate {
  warehouse_id: number
  bin_id: number | null
  article_id: number
  lot_id: number | null
  serial_id: number | null
  quantity: number
  uom_id: number
  reference_type?: string
  reference_id?: number
  notes?: string
  quality_control_blocked: boolean
}

export interface StockMovementOut {
  id: number
  movement_type: StockMovementType
  article_id: number
  quantity: number
  uom_id: number
  user_id: number
  timestamp: string
  notes: string | null
}