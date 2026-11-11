export type StockMovementType = "entry" | "exit" | "internal_transfer" | "adjustment"
export type StockStatus = "available" | "quarantined" | "blocked"

export interface StockOut {
  id: number
  company_id: number
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

export interface StockExitCreate {
  warehouse_id: number
  from_bin_id?: number
  article_id: number
  lot_id?: number
  serial_id?: number
  quantity: number
  uom_id: number
  strategy?: string
  reference_type?: string
  reference_id?: number
  notes?: string
}

export interface StockMovementOut {
  id: number
  company_id: number
  movement_type: StockMovementType
  reference_type: string | null
  reference_id: number | null
  article_id: number
  from_warehouse_id: number | null
  from_bin_id: number | null
  to_warehouse_id: number | null
  to_bin_id: number | null
  lot_id: number | null
  serial_id: number | null
  quantity: number
  uom_id: number
  notes: string | null
  user_id: number
  timestamp: string
}

export interface StockOperationResult {
  detail: string
}

export interface InternalTransferCreate {
  from_warehouse_id: number
  from_bin_id?: number | null
  to_warehouse_id: number
  to_bin_id?: number | null
  article_id: number
  lot_id?: number | null
  serial_id?: number | null
  quantity: number
  uom_id: number
  notes?: string
}