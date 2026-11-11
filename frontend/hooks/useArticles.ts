import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api"
import type { Article, ArticleTranslation, ArticleUpdate } from "@/types/master-data"
import type { StockOut, StockEntryCreate, StockOperationResult } from "@/types/stock"

export const articleKeys = {
  all: ["articles"] as const,
  list: (params?: Record<string, string>) => [...articleKeys.all, "list", params] as const,
  detail: (id: number) => [...articleKeys.all, "detail", id] as const,
  translations: (id: number) => [...articleKeys.all, "translations", id] as const,
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
    enabled: Number.isFinite(id) && id > 0,
  })
}

export function useArticleTranslations(id: number) {
  return useQuery({
    queryKey: articleKeys.translations(id),
    queryFn: () => api.get<ArticleTranslation[]>(`/articles/${id}/translations`),
    enabled: Number.isFinite(id) && id > 0,
  })
}

export function useUpdateArticle(id: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: ArticleUpdate) => api.put<Article>(`/articles/${id}`, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: articleKeys.all })
    },
  })
}

export const stockKeys = {
  all: ["stock"] as const,
  list: (params?: Record<string, string>) => [...stockKeys.all, "list", params] as const,
}

export function useStock(
  params?: Record<string, string>,
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: stockKeys.list(params),
    queryFn: () => api.get<StockOut[]>("/stock", params),
    enabled: options?.enabled ?? true,
  })
}

export function useCreateStockEntry() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: StockEntryCreate) =>
      api.post<StockOperationResult>("/stock/entry", body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: stockKeys.all })
      qc.invalidateQueries({ queryKey: articleKeys.all })
    },
  })
}
