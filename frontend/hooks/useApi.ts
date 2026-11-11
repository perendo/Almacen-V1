import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api"
import type {
  StockExitCreate,
  StockMovementOut,
  InternalTransferCreate,
  StockOperationResult,
} from "@/types/stock"
import type { Company, Center, Warehouse, Zone, Aisle, Shelf, Bin } from "@/types/organization"
import type { Role, Permission } from "@/types/rbac"
import type { UserOut as User } from "@/types/auth"
import type {
  ArticleFamily,
  ArticleBrand,
  Uom,
  Lot,
  SerialNumber,
  InventoryCount,
  Adjustment,
  Alert,
  AuditLog,
} from "@/types/master-data"
import { stockKeys, articleKeys } from "./useArticles"

// ============================================
// COMPANIES
// ============================================
export const companyKeys = {
  all: ["companies"] as const,
  list: (params?: Record<string, string>) => [...companyKeys.all, "list", params] as const,
}

export function useCompanies(params?: Record<string, string>) {
  return useQuery({
    queryKey: companyKeys.list(params),
    queryFn: () => api.get<Company[]>("/companies", params),
  })
}

// ============================================
// CENTERS
// ============================================
export const centerKeys = {
  all: ["centers"] as const,
  list: (params?: Record<string, string>) => [...centerKeys.all, "list", params] as const,
}

export function useCenters(params?: Record<string, string>) {
  return useQuery({
    queryKey: centerKeys.list(params),
    queryFn: () => api.get<Center[]>("/centers", params),
  })
}

// ============================================
// WAREHOUSES
// ============================================
export const warehouseKeys = {
  all: ["warehouses"] as const,
  list: (params?: Record<string, string>) => [...warehouseKeys.all, "list", params] as const,
}

export function useWarehouses(params?: Record<string, string>) {
  return useQuery({
    queryKey: warehouseKeys.list(params),
    queryFn: () => api.get<Warehouse[]>("/warehouses", params),
  })
}

// ============================================
// ZONES
// ============================================
export const zoneKeys = {
  all: ["zones"] as const,
  list: (params?: Record<string, string>) => [...zoneKeys.all, "list", params] as const,
}

export function useZones(params?: Record<string, string>) {
  return useQuery({
    queryKey: zoneKeys.list(params),
    queryFn: () => api.get<Zone[]>("/zones", params),
  })
}

// ============================================
// AISLES / SHELVES / BINS
// ============================================
export const aisleKeys = {
  all: ["aisles"] as const,
  list: (params?: Record<string, string>) => [...aisleKeys.all, "list", params] as const,
}

export function useAisles(params?: Record<string, string>) {
  return useQuery({
    queryKey: aisleKeys.list(params),
    queryFn: () => api.get<Aisle[]>("/aisles", params),
  })
}

export const shelfKeys = {
  all: ["shelves"] as const,
  list: (params?: Record<string, string>) => [...shelfKeys.all, "list", params] as const,
}

export function useShelves(params?: Record<string, string>) {
  return useQuery({
    queryKey: shelfKeys.list(params),
    queryFn: () => api.get<Shelf[]>("/shelves", params),
  })
}

export const binKeys = {
  all: ["bins"] as const,
  list: (params?: Record<string, string>) => [...binKeys.all, "list", params] as const,
}

export function useBins(params?: Record<string, string>) {
  return useQuery({
    queryKey: binKeys.list(params),
    queryFn: () => api.get<Bin[]>("/bins", params),
  })
}

// ============================================
// ROLES & PERMISSIONS
// ============================================
export const roleKeys = {
  all: ["roles"] as const,
  list: () => roleKeys.all,
}

export function useRoles() {
  return useQuery({
    queryKey: roleKeys.list(),
    queryFn: () => api.get<Role[]>("/roles"),
  })
}

export const permissionKeys = {
  all: ["permissions"] as const,
  list: () => permissionKeys.all,
}

export function usePermissions() {
  return useQuery({
    queryKey: permissionKeys.list(),
    queryFn: () => api.get<Permission[]>("/permissions"),
  })
}

// ============================================
// USERS
// ============================================
export const userKeys = {
  all: ["users"] as const,
  list: (params?: Record<string, string>) => [...userKeys.all, "list", params] as const,
}

export function useUsers(params?: Record<string, string>) {
  return useQuery({
    queryKey: userKeys.list(params),
    queryFn: () => api.get<User[]>("/users", params),
  })
}

// ============================================
// ARTICLE FAMILIES
// ============================================
export const articleFamilyKeys = {
  all: ["articleFamilies"] as const,
  list: (params?: Record<string, string>) => [...articleFamilyKeys.all, "list", params] as const,
}

export function useArticleFamilies(params?: Record<string, string>) {
  return useQuery({
    queryKey: articleFamilyKeys.list(params),
    queryFn: () => api.get<ArticleFamily[]>("/article-families", params),
  })
}

// ============================================
// ARTICLE BRANDS
// ============================================
export const articleBrandKeys = {
  all: ["articleBrands"] as const,
  list: (params?: Record<string, string>) => [...articleBrandKeys.all, "list", params] as const,
}

export function useArticleBrands(params?: Record<string, string>) {
  return useQuery({
    queryKey: articleBrandKeys.list(params),
    queryFn: () => api.get<ArticleBrand[]>("/article-brands", params),
  })
}

// ============================================
// UOMS
// ============================================
export const uomKeys = {
  all: ["uoms"] as const,
  list: (params?: Record<string, string>) => [...uomKeys.all, "list", params] as const,
}

export function useUoms(params?: Record<string, string>) {
  return useQuery({
    queryKey: uomKeys.list(params),
    queryFn: () => api.get<Uom[]>("/uoms", params),
  })
}

// ============================================
// LOTS
// ============================================
export const lotKeys = {
  all: ["lots"] as const,
  list: (params?: Record<string, string>) => [...lotKeys.all, "list", params] as const,
  detail: (id: number) => [...lotKeys.all, "detail", id] as const,
}

export function useLots(
  params?: Record<string, string>,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: lotKeys.list(params),
    queryFn: () => api.get<Lot[]>("/lots", params),
    enabled: options?.enabled ?? true,
  })
}

export function useLot(id: number) {
  return useQuery({
    queryKey: lotKeys.detail(id),
    queryFn: () => api.get<Lot>(`/lots/${id}`),
    enabled: Number.isFinite(id) && id > 0,
  })
}

// ============================================
// SERIAL NUMBERS
// ============================================
export const serialKeys = {
  all: ["serials"] as const,
  list: (params?: Record<string, string>) => [...serialKeys.all, "list", params] as const,
  detail: (serialNumber: string) => [...serialKeys.all, "detail", serialNumber] as const,
}

export function useSerials(params?: Record<string, string>) {
  return useQuery({
    queryKey: serialKeys.list(params),
    queryFn: () => api.get<SerialNumber[]>("/serials", params),
  })
}

export function useSerial(serialNumber: string) {
  return useQuery({
    queryKey: serialKeys.detail(serialNumber),
    queryFn: () => api.get<SerialNumber>(`/serials/${encodeURIComponent(serialNumber)}`),
    enabled: serialNumber.length > 0,
  })
}

// ============================================
// INVENTORY COUNTS
// ============================================
export const inventoryCountKeys = {
  all: ["inventoryCounts"] as const,
  list: (params?: Record<string, string>) => [...inventoryCountKeys.all, "list", params] as const,
}

export function useInventoryCounts(params?: Record<string, string>) {
  return useQuery({
    queryKey: inventoryCountKeys.list(params),
    queryFn: () => api.get<InventoryCount[]>("/inventory-counts", params),
  })
}

// ============================================
// ADJUSTMENTS
// ============================================
export const adjustmentKeys = {
  all: ["adjustments"] as const,
  list: (params?: Record<string, string>) => [...adjustmentKeys.all, "list", params] as const,
}

export function useAdjustments(params?: Record<string, string>) {
  return useQuery({
    queryKey: adjustmentKeys.list(params),
    queryFn: () => api.get<Adjustment[]>("/adjustments", params),
  })
}

// ============================================
// ALERTS
// ============================================
export const alertKeys = {
  all: ["alerts"] as const,
  list: (params?: Record<string, string>) => [...alertKeys.all, "list", params] as const,
}

export function useAlerts(
  params?: Record<string, string>,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: alertKeys.list(params),
    queryFn: () => api.get<Alert[]>("/alerts", params),
    enabled: options?.enabled ?? true,
  })
}

export function useResolveAlert() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, resolutionNote }: { id: number; resolutionNote?: string }) =>
      api.put<Alert>(`/alerts/${id}/resolve`, {
        resolution_note: resolutionNote ?? null,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: alertKeys.all })
    },
  })
}

export function useAcknowledgeAlert() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => api.put<Alert>(`/alerts/${id}/acknowledge`, {}),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: alertKeys.all })
    },
  })
}

// ============================================
// AUDIT LOGS (solo lectura)
// ============================================
export const auditLogKeys = {
  all: ["auditLogs"] as const,
  list: (params?: Record<string, string>) => [...auditLogKeys.all, "list", params] as const,
}

export function useAuditLogs(
  params?: Record<string, string>,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: auditLogKeys.list(params),
    queryFn: () => api.get<AuditLog[]>("/audit-logs", params),
    enabled: options?.enabled ?? true,
  })
}

// ============================================
// STOCK MOVEMENTS (list + entry/exit/transfer)
// ============================================
export const stockMovementKeys = {
  all: ["stockMovements"] as const,
  list: (params?: Record<string, string>) => [...stockMovementKeys.all, "list", params] as const,
}

export function useStockMovements(params?: Record<string, string>) {
  return useQuery({
    queryKey: stockMovementKeys.list(params),
    queryFn: () => api.get<StockMovementOut[]>("/stock/movements", params),
  })
}

export function useCreateStockExit() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: StockExitCreate) =>
      api.post<StockOperationResult>("/stock/exit", body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: stockKeys.all })
      qc.invalidateQueries({ queryKey: stockMovementKeys.all })
    },
  })
}

export function useCreateInternalTransfer() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: InternalTransferCreate) =>
      api.post<StockOperationResult>("/stock/internal-transfer", body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: stockKeys.all })
      qc.invalidateQueries({ queryKey: stockMovementKeys.all })
    },
  })
}

export function useCreateAdjustment() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: Record<string, unknown>) =>
      api.post<Adjustment>("/adjustments/", body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: adjustmentKeys.all })
      qc.invalidateQueries({ queryKey: stockKeys.all })
    },
  })
}

// ============================================
// STOCK (re-export de los hooks de useArticles)
// ============================================
export { useStock, useArticles, useArticle } from "./useArticles"
