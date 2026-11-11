"use client"

import { useMemo, useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { EmptyState } from "@/components/ui/empty-state"
import { ErrorState } from "@/components/ui/error-state"
import { DataPagination } from "@/components/ui/pagination"
import { useLots } from "@/hooks/useApi"
import { useArticles } from "@/hooks/useArticles"
import { formatDate } from "@/lib/utils"
import type { Lot } from "@/types/master-data"

const PAGE_SIZE = 25

export default function LotsPage() {
  const [page, setPage] = useState(1)
  const params = useMemo(
    () => ({ skip: String((page - 1) * PAGE_SIZE), limit: String(PAGE_SIZE) }),
    [page]
  )

  const { data: lots, isLoading, error, refetch, isFetching } = useLots(params)
  const { data: articles } = useArticles({ limit: "1000" })

  const articleCodes = useMemo(() => {
    const map = new Map<number, string>()
    articles?.forEach((article) => map.set(article.id, article.internal_code))
    return map
  }, [articles])

  const rows: Lot[] = lots ?? []

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Lotes</h1>
          <p className="text-muted-foreground">Gestión de lotes y trazabilidad</p>
        </div>
        <Button variant="outline" onClick={() => void refetch()} disabled={isFetching}>
          {isFetching ? "Actualizando…" : "Actualizar"}
        </Button>
      </div>

      {isLoading ? (
        <div className="space-y-2 rounded-md border p-4">
          {[1, 2, 3, 4, 5].map((i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      ) : null}

      {error && !isLoading ? (
        <ErrorState
          message={error instanceof Error ? error.message : "Error cargando los lotes"}
          onRetry={() => void refetch()}
        />
      ) : null}

      {!isLoading && !error ? (
        rows.length === 0 ? (
          <EmptyState
            title="No hay lotes registrados"
            description="Los lotes se crean al recepcionar artículos que requieren trazabilidad por lote."
            actionHref="/dashboard/articles"
            actionLabel="Ir a artículos"
          />
        ) : (
          <>
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Número de Lote</TableHead>
                    <TableHead>Artículo</TableHead>
                    <TableHead>Fabricación</TableHead>
                    <TableHead>Caducidad</TableHead>
                    <TableHead>Estado</TableHead>
                    <TableHead>Creado</TableHead>
                    <TableHead className="text-right">Acciones</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {rows.map((lot) => (
                    <TableRow key={lot.id}>
                      <TableCell className="font-medium">{lot.lot_number}</TableCell>
                      <TableCell>
                        {articleCodes.get(lot.article_id) ?? `Artículo #${lot.article_id}`}
                      </TableCell>
                      <TableCell>
                        {lot.manufacturing_date ? formatDate(lot.manufacturing_date) : "—"}
                      </TableCell>
                      <TableCell>{lot.expiration_date ? formatDate(lot.expiration_date) : "—"}</TableCell>
                      <TableCell>
                        <Badge variant={lot.status === "active" ? "default" : "secondary"}>
                          {lot.status}
                        </Badge>
                      </TableCell>
                      <TableCell>{formatDate(lot.created_at)}</TableCell>
                      <TableCell className="text-right">
                        <Link
                          href={`/dashboard/articles/${lot.article_id}`}
                          className="text-sm font-medium text-primary underline-offset-4 hover:underline"
                        >
                          Ver artículo
                        </Link>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            <DataPagination
              page={page}
              pageSize={PAGE_SIZE}
              itemCount={rows.length}
              hasNext={rows.length === PAGE_SIZE}
              onPrevious={() => setPage((current) => Math.max(1, current - 1))}
              onNext={() => setPage((current) => current + 1)}
              disabled={isFetching}
            />
          </>
        )
      ) : null}
    </div>
  )
}
