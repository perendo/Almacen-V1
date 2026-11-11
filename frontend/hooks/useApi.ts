import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api"
import type { StockOut, StockEntryCreate, StockExitCreate, StockMovementOut } from "@/types/stock"
import type { Company, Center, Warehouse, Zone, Aisle, Shelf, Bin } from "@/types/organization"
import type { Role, Permission, UserRole } from "@/types/rbac"
import type { UserOut as User } from "@/types/auth"
import type { Article, ArticleFamily, ArticleBrand, Uom, Lot, InventoryCount, Adjustment, Alert } from "@/types/master-data"
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
}

export function useLots(params?: Record<string, string>) {
  return useQuery({
    queryKey: lotKeys.list(params),
    queryFn: () => api.get<Lot[]>("/lots", params),
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

export function useAlerts(params?: Record<string, string>) {
  return useQuery({
    queryKey: alertKeys.list(params),
    queryFn: () => api.get<Alert[]>("/alerts", params),
  })
}

// ============================================
// STOCK MOVEMENTS (entry/exit/transfer)
// ============================================
export function useCreateStockEntry() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: StockEntryCreate) =>
      api.post<StockMovementOut>("/stock/entry", body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: stockKeys.all })
      qc.invalidateQueries({ queryKey: articleKeys.all })
    },
  })
}

export function useCreateStockExit() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: StockExitCreate) => api.post("/stock/exit", body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: stockKeys.all })
    },
  })
}

export function useCreateInternalTransfer() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: any) => api.post("/stock/internal-transfer", body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: stockKeys.all })
    },
  })
}

export function useCreateAdjustment() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: any) => api.post("/adjustments/", body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: adjustmentKeys.all })
      qc.invalidateQueries({ queryKey: stockKeys.all })
    },
  })
}