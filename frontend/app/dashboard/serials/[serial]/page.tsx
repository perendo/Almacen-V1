"use client"

import { useMemo } from "react"
import Link from "next/link"
import { useParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
import { EmptyState } from "@/components/ui/empty-state"
import { ErrorState } from "@/components/ui/error-state"
import {
  useAisles,
  useBins,
  useLots,
  useSerial,
  useShelves,
  useStockMovements,
  useWarehouses,
  useZones,
} from "@/hooks/useApi"
import { useArticleTranslations, useArticles } from "@/hooks/useArticles"
import { ApiError } from "@/lib/api"
import { formatDateTime } from "@/lib/utils"
import type { StockMovementOut } from "@/types/stock"

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

export default function SerialDetailPage() {
  const params = useParams<{ serial: string }>()
  // Next.js ya entrega el parámetro de ruta decodificado.
  const serialNumber = params?.serial ?? ""

  const serialQuery = useSerial(serialNumber)
  const serial = serialQuery.data
  const articleId = serial?.article_id ?? 0

  const articlesQuery = useArticles({ limit: "1000" })
  const translationsQuery = useArticleTranslations(articleId)
  const lotsQuery = useLots({ limit: "1000" })
  const movementsQuery = useStockMovements({ limit: "1000" })

  const binsQuery = useBins({ limit: "1000" })
  const shelvesQuery = useShelves({ limit: "1000" })
  const aislesQuery = useAisles({ limit: "1000" })
  const zonesQuery = useZones({ limit: "1000" })
  const warehousesQuery = useWarehouses({ limit: "1000" })

  const articleCode = useMemo(() => {
    if (!serial) return "—"
    return (
      articlesQuery.data?.find((article) => article.id === serial.article_id)?.internal_code ??
      `Artículo #${serial.article_id}`
    )
  }, [articlesQuery.data, serial])

  const articleName = useMemo(() => {
    const list = translationsQuery.data ?? []
    const translation = list.find((item) => item.language_code === "es") ?? list[0]
    return translation?.name ?? null
  }, [translationsQuery.data])

  const lotNumber = useMemo(() => {
    if (!serial?.lot_id) return "—"
    return lotsQuery.data?.find((lot) => lot.id === serial.lot_id)?.lot_number ?? `Lote #${serial.lot_id}`
  }, [lotsQuery.data, serial])

  const locationPath = useMemo(() => {
    if (!serial?.current_bin_id) return "—"
    const bin = binsQuery.data?.find((item) => item.id === serial.current_bin_id)
    if (!bin) return `Bin #${serial.current_bin_id}`
    const shelf = shelvesQuery.data?.find((item) => item.id === bin.shelf_id)
    const aisle = shelf ? aislesQuery.data?.find((item) => item.id === shelf.aisle_id) : undefined
    const zone = aisle ? zonesQuery.data?.find((item) => item.id === aisle.zone_id) : undefined
    const warehouse = zone
      ? warehousesQuery.data?.find((item) => item.id === zone.warehouse_id)
      : undefined
    return [warehouse?.code, zone?.code, aisle?.code, shelf?.code, bin.code].filter(Boolean).join(" › ")
  }, [serial, binsQuery.data, shelvesQuery.data, aislesQuery.data, zonesQuery.data, warehousesQuery.data])

  const serialMovements: StockMovementOut[] = useMemo(
    () =>
      serial
        ? (movementsQuery.data ?? []).filter((movement) => movement.serial_id === serial.id)
        : [],
    [movementsQuery.data, serial]
  )

  const isNotFound = serialQuery.error instanceof ApiError && serialQuery.error.status === 404

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Trazabilidad de Serie</h1>
          <p className="text-muted-foreground">Historial completo de ubicaciones y movimientos</p>
        </div>
        <Link href="/dashboard/serials">
          <Button variant="outline">Volver a listado</Button>
        </Link>
      </div>

      {serialQuery.isLoading ? (
        <div className="space-y-4 rounded-md border p-6">
          <Skeleton className="h-8 w-64" />
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-20 w-full" />
          </div>
        </div>
      ) : null}

      {isNotFound ? (
        <EmptyState
          title="Número de serie no encontrado"
          description={`No existe ninguna serie con el número ${serialNumber}.`}
          actionHref="/dashboard/serials"
          actionLabel="Volver al listado de series"
        />
      ) : null}

      {serialQuery.error && !isNotFound ? (
        <ErrorState
          message={
            serialQuery.error instanceof Error
              ? serialQuery.error.message
              : "Error cargando el número de serie"
          }
          onRetry={() => void serialQuery.refetch()}
        />
      ) : null}

      {serial ? (
        <div className="rounded-md border p-6">
          <div className="mb-4 flex flex-wrap items-center gap-3">
            <h2 className="text-lg font-semibold">Serie: {serial.serial_number}</h2>
            <Badge variant={serial.status === "in_stock" ? "default" : "secondary"}>{serial.status}</Badge>
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div className="rounded-lg border p-4">
              <h3 className="text-sm font-semibold text-muted-foreground">Artículo</h3>
              <p className="text-sm text-foreground">
                {articleCode}
                {articleName ? ` — ${articleName}` : ""}
              </p>
            </div>
            <div className="rounded-lg border p-4">
              <h3 className="text-sm font-semibold text-muted-foreground">Ubicación actual</h3>
              <p className="text-sm text-foreground">{locationPath}</p>
            </div>
            <div className="rounded-lg border p-4">
              <h3 className="text-sm font-semibold text-muted-foreground">Estado</h3>
              <p className="text-sm text-foreground">{serial.status}</p>
            </div>
            <div className="rounded-lg border p-4">
              <h3 className="text-sm font-semibold text-muted-foreground">Lote</h3>
              <p className="text-sm text-foreground">{lotNumber}</p>
            </div>
            <div className="rounded-lg border p-4">
              <h3 className="text-sm font-semibold text-muted-foreground">Alta</h3>
              <p className="text-sm text-foreground">{formatDateTime(serial.created_at)}</p>
            </div>
            <div className="rounded-lg border p-4">
              <h3 className="text-sm font-semibold text-muted-foreground">Última actualización</h3>
              <p className="text-sm text-foreground">
                {serial.updated_at ? formatDateTime(serial.updated_at) : "—"}
              </p>
            </div>
          </div>

          <div className="mt-6">
            <h3 className="mb-2 text-sm font-semibold text-muted-foreground">Historial de Movimientos</h3>

            {movementsQuery.isLoading ? (
              <div className="space-y-2">
                {[1, 2, 3].map((i) => (
                  <Skeleton key={i} className="h-10 w-full" />
                ))}
              </div>
            ) : movementsQuery.error ? (
              <ErrorState
                title="No se pudo cargar el historial de movimientos"
                message={
                  movementsQuery.error instanceof Error
                    ? movementsQuery.error.message
                    : "Error consultando /stock/movements"
                }
                onRetry={() => void movementsQuery.refetch()}
              />
            ) : serialMovements.length === 0 ? (
              <EmptyState
                title="Sin movimientos para esta serie"
                description="No hay movimientos de stock registrados con este número de serie."
              />
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Fecha</TableHead>
                    <TableHead>Tipo</TableHead>
                    <TableHead>Cantidad</TableHead>
                    <TableHead>Notas</TableHead>
                    <TableHead>Usuario</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {serialMovements.map((movement) => (
                    <TableRow key={movement.id}>
                      <TableCell className="font-medium">{formatDateTime(movement.timestamp)}</TableCell>
                      <TableCell>
                        <Badge variant={movementVariant(movement.movement_type)}>
                          {movementLabel(movement.movement_type)}
                        </Badge>
                      </TableCell>
                      <TableCell>{movement.quantity}</TableCell>
                      <TableCell className="max-w-xs truncate" title={movement.notes ?? undefined}>
                        {movement.notes || "—"}
                      </TableCell>
                      <TableCell>Usuario #{movement.user_id}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </div>
        </div>
      ) : null}
    </div>
  )
}
