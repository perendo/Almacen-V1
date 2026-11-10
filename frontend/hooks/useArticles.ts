import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api"
import type { Article } from "@/types/master-data"
import type { StockOut, StockEntryCreate, StockMovementOut } from "@/types/stock"

export const articleKeys = {
  all: ["articles"] as const,
  list: (params?: Record<string, string>) => [...articleKeys.all, "list", params] as const,
  detail: (id: number) => [...articleKeys.all, "detail", id] as const,
}

export function useArticles(params?: Record<string, string>) {
  return useQuery({
    queryKey: articleKeys.list(params),
    queryFn: () => api.get<Article[]>("/articles", params),
  })
}

export function useArticle(id: number) {
  return useQuery({
    queryKey: articleKeys.detail(id),
    queryFn: () => api.get<Article>(`/articles/${id}`),
  })
}

export const stockKeys = {
  all: ["stock"] as const,
  list: (params?: Record<string, string>) => [...stockKeys.all, "list", params] as const,
}

export function useStock(params?: Record<string, string>) {
  return useQuery({
    queryKey: stockKeys.list(params),
    queryFn: () => api.get<StockOut[]>("/stock", params),
  })
}

export function useCreateStockEntry() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: StockEntryCreate) =>
      api.post<StockMovementOut>("/stock-movements/entry", body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: stockKeys.all })
      qc.invalidateQueries({ queryKey: articleKeys.all })
    },
  })
}