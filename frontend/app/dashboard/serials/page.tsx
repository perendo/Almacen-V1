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
import { useLots, useSerials } from "@/hooks/useApi"
import { useArticles } from "@/hooks/useArticles"
import { formatDateTime } from "@/lib/utils"
import type { SerialNumber } from "@/types/master-data"

const PAGE_SIZE = 25

export default function SerialsPage() {
  const [page, setPage] = useState(1)
  const params = useMemo(
    () => ({ skip: String((page - 1) * PAGE_SIZE), limit: String(PAGE_SIZE) }),
    [page]
  )

  const { data: serials, isLoading, error, refetch, isFetching } = useSerials(params)
  const { data: articles } = useArticles({ limit: "1000" })
  const { data: lots } = useLots({ limit: "1000" })

  const articleCodes = useMemo(() => {
    const map = new Map<number, string>()
    articles?.forEach((article) => map.set(article.id, article.internal_code))
    return map
  }, [articles])

  const lotNumbers = useMemo(() => {
    const map = new Map<number, string>()
    lots?.forEach((lot) => map.set(lot.id, lot.lot_number))
    return map
  }, [lots])

  const rows: SerialNumber[] = serials ?? []

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Números de Serie</h1>
          <p className="text-muted-foreground">Seguimiento unitario de productos electrónicos y maquinaria</p>
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
          message={error instanceof Error ? error.message : "Error cargando los números de serie"}
          onRetry={() => void refetch()}
        />
      ) : null}

      {!isLoading && !error ? (
        rows.length === 0 ? (
          <EmptyState
            title="No hay números de serie registrados"
            description="Los números de serie se registran al recepcionar artículos serializados."
          />
        ) : (
          <>
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Número de Serie</TableHead>
                    <TableHead>Artículo</TableHead>
                    <TableHead>Lote</TableHead>
                    <TableHead>Ubicación (Bin)</TableHead>
                    <TableHead>Estado</TableHead>
                    <TableHead>Alta</TableHead>
                    <TableHead className="text-right">Acciones</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {rows.map((serial) => (
                    <TableRow key={serial.id}>
                      <TableCell className="font-medium">{serial.serial_number}</TableCell>
                      <TableCell>
                        {articleCodes.get(serial.article_id) ?? `Artículo #${serial.article_id}`}
                      </TableCell>
                      <TableCell>
                        {serial.lot_id ? lotNumbers.get(serial.lot_id) ?? `Lote #${serial.lot_id}` : "—"}
                      </TableCell>
                      <TableCell>
                        {serial.current_bin_id ? `Bin #${serial.current_bin_id}` : "—"}
                      </TableCell>
                      <TableCell>
                        <Badge variant={serial.status === "in_stock" ? "default" : "secondary"}>
                          {serial.status}
                        </Badge>
                      </TableCell>
                      <TableCell>{formatDateTime(serial.created_at)}</TableCell>
                      <TableCell className="text-right">
                        <Link
                          href={`/dashboard/serials/${encodeURIComponent(serial.serial_number)}`}
                          className="text-sm font-medium text-primary underline-offset-4 hover:underline"
                        >
                          Ver trazabilidad
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
