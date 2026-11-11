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
import { RoleGuard } from "@/components/role-guard"
import { useBins, useStockMovements, useUoms, useWarehouses } from "@/hooks/useApi"
import { useArticles } from "@/hooks/useArticles"
import { formatDateTime } from "@/lib/utils"
import type { StockMovementOut } from "@/types/stock"

const PAGE_SIZE = 25
const MOVEMENT_ROLES = ["SuperAdmin", "Gerente de Almacén", "Operario de Almacén"]

function movementLabel(type: string): string {
  switch (type) {
    case "entry":
      return "Entrada"
    case "exit":
      return "Salida"
    case "internal_transfer":
      return "Traspaso"
    case "adjustment":
      return "Ajuste"
    default:
      return type
  }
}

function movementVariant(type: string): "default" | "secondary" | "destructive" | "outline" {
  if (type === "entry") return "default"
  if (type === "exit") return "destructive"
  if (type === "internal_transfer") return "secondary"
  return "outline"
}

export default function MovementsPage() {
  const [page, setPage] = useState(1)
  const [typeFilter, setTypeFilter] = useState("")

  const params = useMemo(() => {
    const query: Record<string, string> = {
      skip: String((page - 1) * PAGE_SIZE),
      limit: String(PAGE_SIZE),
    }
    if (typeFilter) query.movement_type = typeFilter
    return query
  }, [page, typeFilter])

  const { data: movements, isLoading, error, refetch, isFetching } = useStockMovements(params)
  const { data: articles } = useArticles({ limit: "1000" })
  const { data: warehouses } = useWarehouses({ limit: "1000" })
  const { data: bins } = useBins({ limit: "1000" })
  const { data: uoms } = useUoms({ limit: "1000" })

  const articleCodes = useMemo(() => {
    const map = new Map<number, string>()
    articles?.forEach((article) => map.set(article.id, article.internal_code))
    return map
  }, [articles])

  const warehouseCodes = useMemo(() => {
    const map = new Map<number, string>()
    warehouses?.forEach((warehouse) => map.set(warehouse.id, warehouse.code))
    return map
  }, [warehouses])

  const binCodes = useMemo(() => {
    const map = new Map<number, string>()
    bins?.forEach((bin) => map.set(bin.id, bin.code))
    return map
  }, [bins])

  const uomCodes = useMemo(() => {
    const map = new Map<number, string>()
    uoms?.forEach((uom) => map.set(uom.id, uom.code))
    return map
  }, [uoms])

  const rows: StockMovementOut[] = movements ?? []

  function location(warehouseId: number | null, binId: number | null): string {
    const warehouse = warehouseId ? warehouseCodes.get(warehouseId) ?? `WH#${warehouseId}` : null
    const bin = binId ? binCodes.get(binId) ?? `Bin#${binId}` : null
    if (!warehouse && !bin) return "—"
    return [warehouse, bin].filter(Boolean).join(" / ")
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Movimientos de Stock</h1>
          <p className="text-muted-foreground">Entradas, salidas, traslados internos y ajustes</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <RoleGuard roles={MOVEMENT_ROLES}>
            <Link
              href="/dashboard/movements/entry"
              className="inline-flex h-10 items-center justify-center rounded-md border border-input bg-background px-4 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground"
            >
              Nueva entrada
            </Link>
            <Link
              href="/dashboard/movements/exit"
              className="inline-flex h-10 items-center justify-center rounded-md border border-input bg-background px-4 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground"
            >
              Nueva salida
            </Link>
            <Link
              href="/dashboard/movements/transfer"
              className="inline-flex h-10 items-center justify-center rounded-md border border-input bg-background px-4 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground"
            >
              Traspaso interno
            </Link>
          </RoleGuard>
          <Button variant="outline" onClick={() => void refetch()} disabled={isFetching}>
            {isFetching ? "Actualizando…" : "Actualizar"}
          </Button>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <label htmlFor="movement-type" className="text-sm text-muted-foreground">
          Tipo
        </label>
        <select
          id="movement-type"
          className="h-10 rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          value={typeFilter}
          onChange={(event) => {
            setTypeFilter(event.target.value)
            setPage(1)
          }}
        >
          <option value="">Todos</option>
          <option value="entry">Entrada</option>
          <option value="exit">Salida</option>
          <option value="internal_transfer">Traspaso interno</option>
          <option value="adjustment">Ajuste</option>
        </select>
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
          message={error instanceof Error ? error.message : "Error cargando los movimientos"}
          onRetry={() => void refetch()}
        />
      ) : null}

      {!isLoading && !error ? (
        rows.length === 0 ? (
          <EmptyState
            title="No hay movimientos registrados"
            description="Las entradas, salidas y traspasos de stock aparecerán aquí en cuanto se registren."
            actionHref="/dashboard/movements/exit"
            actionLabel="Registrar una salida"
          />
        ) : (
          <>
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Fecha</TableHead>
                    <TableHead>Tipo</TableHead>
                    <TableHead>Artículo</TableHead>
                    <TableHead>Cantidad</TableHead>
                    <TableHead>Origen</TableHead>
                    <TableHead>Destino</TableHead>
                    <TableHead>Usuario</TableHead>
                    <TableHead>Notas</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {rows.map((movement) => (
                    <TableRow key={movement.id}>
                      <TableCell className="font-medium">{formatDateTime(movement.timestamp)}</TableCell>
                      <TableCell>
                        <Badge variant={movementVariant(movement.movement_type)}>
                          {movementLabel(movement.movement_type)}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {articleCodes.get(movement.article_id) ?? `Artículo #${movement.article_id}`}
                      </TableCell>
                      <TableCell>
                        {movement.quantity} {uomCodes.get(movement.uom_id) ?? ""}
                      </TableCell>
                      <TableCell>
                        {location(movement.from_warehouse_id, movement.from_bin_id)}
                      </TableCell>
                      <TableCell>{location(movement.to_warehouse_id, movement.to_bin_id)}</TableCell>
                      <TableCell>Usuario #{movement.user_id}</TableCell>
                      <TableCell className="max-w-xs truncate" title={movement.notes ?? undefined}>
                        {movement.notes || "—"}
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
