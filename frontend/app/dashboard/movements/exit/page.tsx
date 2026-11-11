"use client"

import { useMemo, useState } from "react"
import { z } from "zod"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { ErrorState } from "@/components/ui/error-state"
import { Skeleton } from "@/components/ui/skeleton"
import { RoleGuard } from "@/components/role-guard"
import { useAuth } from "@/hooks/useAuth"
import {
  useAisles,
  useBins,
  useCreateStockExit,
  useLots,
  useSerials,
  useShelves,
  useUoms,
  useWarehouses,
  useZones,
} from "@/hooks/useApi"
import { useArticles } from "@/hooks/useArticles"
import { ApiError } from "@/lib/api"
import { formatDate } from "@/lib/utils"
import type { StockExitCreate } from "@/types/stock"
import { Loader2, PackageMinus } from "lucide-react"

const EXIT_ROLES = ["SuperAdmin", "Gerente de Almacén", "Operario de Almacén"]

const exitSchema = z.object({
  warehouse_id: z.number().int().positive("Seleccione un almacén"),
  from_bin_id: z.number().int().positive().optional(),
  article_id: z.number().int().positive("Seleccione un artículo"),
  lot_id: z.number().int().positive().optional(),
  serial_id: z.number().int().positive().optional(),
  quantity: z.number().gt(0, "La cantidad debe ser mayor a 0"),
  uom_id: z.number().int().positive("Seleccione una unidad de medida"),
  strategy: z.enum(["FIFO", "FEFO"]),
  reference_type: z.string().max(50).optional(),
  reference_id: z.number().int().positive().optional(),
  notes: z.string().max(500).optional(),
})

type FieldErrors = Partial<Record<keyof z.infer<typeof exitSchema>, string>>

interface ExitFormState {
  warehouse_id: string
  from_bin_id: string
  article_id: string
  lot_id: string
  serial_id: string
  quantity: string
  uom_id: string
  strategy: "FIFO" | "FEFO"
  reference_type: string
  reference_id: string
  notes: string
}

const INITIAL_FORM: ExitFormState = {
  warehouse_id: "",
  from_bin_id: "",
  article_id: "",
  lot_id: "",
  serial_id: "",
  quantity: "1",
  uom_id: "",
  strategy: "FIFO",
  reference_type: "",
  reference_id: "",
  notes: "",
}

const selectClassName =
  "h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"

function toOptionalNumber(value: string): number | undefined {
  if (!value.trim()) return undefined
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : undefined
}

export default function StockExitPage() {
  const { user } = useAuth()
  const [form, setForm] = useState<ExitFormState>(INITIAL_FORM)
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({})
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const articlesQuery = useArticles({ limit: "1000" })
  const warehousesQuery = useWarehouses({ limit: "1000" })
  const binsQuery = useBins({ limit: "1000" })
  const uomsQuery = useUoms({ limit: "1000" })
  const lotsQuery = useLots({
    limit: "1000",
    ...(user?.company_id ? { company_id: String(user.company_id) } : {}),
  })
  const serialsQuery = useSerials({ limit: "1000" })
  const zonesQuery = useZones({ limit: "1000" })
  const aislesQuery = useAisles({ limit: "1000" })
  const shelvesQuery = useShelves({ limit: "1000" })

  const createStockExit = useCreateStockExit()

  const articles = articlesQuery.data ?? []
  const warehouses = warehousesQuery.data ?? []
  const uoms = uomsQuery.data ?? []
  const bins = useMemo(() => binsQuery.data ?? [], [binsQuery.data])
  const lots = useMemo(() => lotsQuery.data ?? [], [lotsQuery.data])
  const serials = useMemo(() => serialsQuery.data ?? [], [serialsQuery.data])

  const selectedArticleId = toOptionalNumber(form.article_id)
  const selectedWarehouseId = toOptionalNumber(form.warehouse_id)

  // El endpoint /bins no filtra por almacén; se resuelve la jerarquía en cliente.
  const binWarehouse = useMemo(() => {
    const zoneWarehouse = new Map<number, number>()
    zonesQuery.data?.forEach((zone) => zoneWarehouse.set(zone.id, zone.warehouse_id))
    const aisleZone = new Map<number, number>()
    aislesQuery.data?.forEach((aisle) => aisleZone.set(aisle.id, aisle.zone_id))
    const shelfAisle = new Map<number, number>()
    shelvesQuery.data?.forEach((shelf) => shelfAisle.set(shelf.id, shelf.aisle_id))
    const map = new Map<number, number>()
    bins.forEach((bin) => {
      const aisleId = shelfAisle.get(bin.shelf_id)
      const zoneId = aisleId ? aisleZone.get(aisleId) : undefined
      const warehouseId = zoneId ? zoneWarehouse.get(zoneId) : undefined
      if (warehouseId) map.set(bin.id, warehouseId)
    })
    return map
  }, [bins, zonesQuery.data, aislesQuery.data, shelvesQuery.data])

  const availableBins = useMemo(
    () =>
      selectedWarehouseId
        ? bins.filter((bin) => binWarehouse.get(bin.id) === selectedWarehouseId)
        : bins,
    [bins, binWarehouse, selectedWarehouseId]
  )

  const articleLots = useMemo(
    () => (selectedArticleId ? lots.filter((lot) => lot.article_id === selectedArticleId) : []),
    [lots, selectedArticleId]
  )

  const articleSerials = useMemo(
    () =>
      selectedArticleId ? serials.filter((serial) => serial.article_id === selectedArticleId) : [],
    [serials, selectedArticleId]
  )

  const catalogError =
    articlesQuery.error ??
    warehousesQuery.error ??
    uomsQuery.error ??
    binsQuery.error ??
    lotsQuery.error ??
    serialsQuery.error ??
    zonesQuery.error ??
    aislesQuery.error ??
    shelvesQuery.error

  const catalogsLoading =
    articlesQuery.isLoading ||
    warehousesQuery.isLoading ||
    uomsQuery.isLoading ||
    binsQuery.isLoading

  function updateField<K extends keyof ExitFormState>(key: K, value: ExitFormState[K]) {
    setForm((current) => ({ ...current, [key]: value }))
  }

  function handleArticleChange(value: string) {
    setForm((current) => ({
      ...current,
      article_id: value,
      lot_id: "",
      serial_id: "",
    }))
  }

  function handleWarehouseChange(value: string) {
    setForm((current) => ({ ...current, warehouse_id: value, from_bin_id: "" }))
  }

  async function reloadCatalogs() {
    await Promise.all([
      articlesQuery.refetch(),
      warehousesQuery.refetch(),
      binsQuery.refetch(),
      uomsQuery.refetch(),
      lotsQuery.refetch(),
      serialsQuery.refetch(),
      zonesQuery.refetch(),
      aislesQuery.refetch(),
      shelvesQuery.refetch(),
    ])
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setSuccess(null)

    const candidate = {
      warehouse_id: toOptionalNumber(form.warehouse_id),
      from_bin_id: toOptionalNumber(form.from_bin_id),
      article_id: toOptionalNumber(form.article_id),
      lot_id: toOptionalNumber(form.lot_id),
      serial_id: toOptionalNumber(form.serial_id),
      quantity: Number(form.quantity),
      uom_id: toOptionalNumber(form.uom_id),
      strategy: form.strategy,
      reference_type: form.reference_type.trim() || undefined,
      reference_id: toOptionalNumber(form.reference_id),
      notes: form.notes.trim() || undefined,
    }

    const parsed = exitSchema.safeParse(candidate)
    if (!parsed.success) {
      const nextErrors: FieldErrors = {}
      parsed.error.issues.forEach((issue) => {
        const key = issue.path[0]
        if (typeof key === "string" && !(key in nextErrors)) {
          nextErrors[key as keyof FieldErrors] = issue.message
        }
      })
      setFieldErrors(nextErrors)
      return
    }

    setFieldErrors({})
    const body: StockExitCreate = parsed.data

    try {
      const result = await createStockExit.mutateAsync(body)
      setSuccess(result.detail || "Salida de stock registrada correctamente")
      setForm(INITIAL_FORM)
    } catch (err) {
      if (err instanceof ApiError) {
        const detail = typeof err.data?.detail === "string" ? err.data.detail : err.message
        setError(
          err.status === 400
            ? `Operación rechazada por el servidor: ${detail}`
            : detail
        )
      } else {
        setError(err instanceof Error ? err.message : "Error al registrar la salida de stock")
      }
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Salida de Stock — Albarán</h1>
          <p className="text-muted-foreground">Registre una salida/expedición de mercancía del almacén</p>
        </div>
        <Button onClick={() => (window.location.href = "/dashboard/movements")} variant="outline">
          Volver a movimientos
        </Button>
      </div>

      <RoleGuard
        roles={EXIT_ROLES}
        fallback={
          <Alert>
            <AlertDescription>
              Su rol es de solo lectura. Solo SuperAdmin, Gerente de Almacén y Operario de Almacén pueden
              registrar salidas de stock.
            </AlertDescription>
          </Alert>
        }
      >
        {error ? (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        ) : null}

        {success ? (
          <Alert>
            <AlertDescription>{success}</AlertDescription>
          </Alert>
        ) : null}

        {catalogError ? (
          <ErrorState
            title="No se pudieron cargar los catálogos del formulario"
            message={
              catalogError instanceof Error
                ? catalogError.message
                : "Error cargando artículos, almacenes o unidades de medida"
            }
            onRetry={() => void reloadCatalogs()}
          />
        ) : null}

        <Card>
          <CardHeader>
            <CardTitle>Datos de la salida</CardTitle>
            <CardDescription>Complete los datos del albarán de salida de mercancía</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {catalogsLoading ? (
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
                {[1, 2, 3, 4, 5, 6].map((i) => (
                  <Skeleton key={i} className="h-16 w-full" />
                ))}
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-6" noValidate>
                <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
                  <div className="space-y-2">
                    <label htmlFor="warehouse_id" className="text-sm font-medium text-foreground">
                      Almacén de origen *
                    </label>
                    <select
                      id="warehouse_id"
                      className={selectClassName}
                      value={form.warehouse_id}
                      onChange={(event) => handleWarehouseChange(event.target.value)}
                      disabled={createStockExit.isPending}
                    >
                      <option value="">Seleccionar almacén</option>
                      {warehouses.map((warehouse) => (
                        <option key={warehouse.id} value={warehouse.id}>
                          {warehouse.name} ({warehouse.code})
                        </option>
                      ))}
                    </select>
                    {fieldErrors.warehouse_id ? (
                      <p className="text-xs text-destructive">{fieldErrors.warehouse_id}</p>
                    ) : null}
                  </div>

                  <div className="space-y-2">
                    <label htmlFor="from_bin_id" className="text-sm font-medium text-foreground">
                      Ubicación (Bin)
                    </label>
                    <select
                      id="from_bin_id"
                      className={selectClassName}
                      value={form.from_bin_id}
                      onChange={(event) => updateField("from_bin_id", event.target.value)}
                      disabled={createStockExit.isPending}
                    >
                      <option value="">Seleccionar bin</option>
                      {availableBins.map((bin) => (
                        <option key={bin.id} value={bin.id}>
                          {bin.code}
                        </option>
                      ))}
                    </select>
                    {selectedWarehouseId && availableBins.length === 0 ? (
                      <p className="text-xs text-muted-foreground">
                        No hay bins asociados a este almacén en la jerarquía disponible.
                      </p>
                    ) : null}
                    {fieldErrors.from_bin_id ? (
                      <p className="text-xs text-destructive">{fieldErrors.from_bin_id}</p>
                    ) : null}
                  </div>

                  <div className="space-y-2">
                    <label htmlFor="article_id" className="text-sm font-medium text-foreground">
                      Artículo *
                    </label>
                    <select
                      id="article_id"
                      className={selectClassName}
                      value={form.article_id}
                      onChange={(event) => handleArticleChange(event.target.value)}
                      disabled={createStockExit.isPending}
                    >
                      <option value="">Seleccionar artículo</option>
                      {articles.map((article) => (
                        <option key={article.id} value={article.id}>
                          {article.internal_code}
                          {article.ean13 ? ` — EAN ${article.ean13}` : ""}
                        </option>
                      ))}
                    </select>
                    {fieldErrors.article_id ? (
                      <p className="text-xs text-destructive">{fieldErrors.article_id}</p>
                    ) : null}
                  </div>

                  <div className="space-y-2">
                    <label htmlFor="lot_id" className="text-sm font-medium text-foreground">
                      Lote
                    </label>
                    <select
                      id="lot_id"
                      className={selectClassName}
                      value={form.lot_id}
                      onChange={(event) => updateField("lot_id", event.target.value)}
                      disabled={createStockExit.isPending || !selectedArticleId}
                    >
                      <option value="">Seleccionar lote (opcional)</option>
                      {articleLots.map((lot) => (
                        <option key={lot.id} value={lot.id}>
                          {lot.lot_number}
                          {lot.expiration_date ? ` — caduca ${formatDate(lot.expiration_date)}` : ""}
                        </option>
                      ))}
                    </select>
                    {fieldErrors.lot_id ? (
                      <p className="text-xs text-destructive">{fieldErrors.lot_id}</p>
                    ) : null}
                  </div>

                  <div className="space-y-2">
                    <label htmlFor="serial_id" className="text-sm font-medium text-foreground">
                      Número de serie
                    </label>
                    <select
                      id="serial_id"
                      className={selectClassName}
                      value={form.serial_id}
                      onChange={(event) => updateField("serial_id", event.target.value)}
                      disabled={createStockExit.isPending || !selectedArticleId}
                    >
                      <option value="">Seleccionar serie (opcional)</option>
                      {articleSerials.map((serial) => (
                        <option key={serial.id} value={serial.id}>
                          {serial.serial_number}
                        </option>
                      ))}
                    </select>
                    {fieldErrors.serial_id ? (
                      <p className="text-xs text-destructive">{fieldErrors.serial_id}</p>
                    ) : null}
                  </div>

                  <div className="space-y-2">
                    <label htmlFor="quantity" className="text-sm font-medium text-foreground">
                      Cantidad *
                    </label>
                    <Input
                      id="quantity"
                      type="number"
                      min="0.01"
                      step="0.01"
                      value={form.quantity}
                      onChange={(event) => updateField("quantity", event.target.value)}
                      disabled={createStockExit.isPending}
                      placeholder="0"
                    />
                    {fieldErrors.quantity ? (
                      <p className="text-xs text-destructive">{fieldErrors.quantity}</p>
                    ) : null}
                  </div>

                  <div className="space-y-2">
                    <label htmlFor="uom_id" className="text-sm font-medium text-foreground">
                      Unidad de medida *
                    </label>
                    <select
                      id="uom_id"
                      className={selectClassName}
                      value={form.uom_id}
                      onChange={(event) => updateField("uom_id", event.target.value)}
                      disabled={createStockExit.isPending}
                    >
                      <option value="">Seleccionar UOM</option>
                      {uoms.map((uom) => (
                        <option key={uom.id} value={uom.id}>
                          {uom.name} ({uom.code})
                        </option>
                      ))}
                    </select>
                    {fieldErrors.uom_id ? (
                      <p className="text-xs text-destructive">{fieldErrors.uom_id}</p>
                    ) : null}
                  </div>

                  <div className="space-y-2">
                    <label htmlFor="strategy" className="text-sm font-medium text-foreground">
                      Estrategia
                    </label>
                    <select
                      id="strategy"
                      className={selectClassName}
                      value={form.strategy}
                      onChange={(event) =>
                        updateField("strategy", event.target.value === "FEFO" ? "FEFO" : "FIFO")
                      }
                      disabled={createStockExit.isPending}
                    >
                      <option value="FIFO">FIFO (primero en entrar, primero en salir)</option>
                      <option value="FEFO">FEFO (primero en caducar, primero en salir)</option>
                    </select>
                  </div>

                  <div className="space-y-2">
                    <label htmlFor="reference_type" className="text-sm font-medium text-foreground">
                      Tipo de referencia
                    </label>
                    <Input
                      id="reference_type"
                      value={form.reference_type}
                      onChange={(event) => updateField("reference_type", event.target.value)}
                      disabled={createStockExit.isPending}
                      placeholder="Ej: sales_order"
                    />
                    {fieldErrors.reference_type ? (
                      <p className="text-xs text-destructive">{fieldErrors.reference_type}</p>
                    ) : null}
                  </div>

                  <div className="space-y-2">
                    <label htmlFor="reference_id" className="text-sm font-medium text-foreground">
                      ID de referencia
                    </label>
                    <Input
                      id="reference_id"
                      type="number"
                      value={form.reference_id}
                      onChange={(event) => updateField("reference_id", event.target.value)}
                      disabled={createStockExit.isPending}
                      placeholder="Ej: 12345"
                    />
                    {fieldErrors.reference_id ? (
                      <p className="text-xs text-destructive">{fieldErrors.reference_id}</p>
                    ) : null}
                  </div>

                  <div className="space-y-2">
                    <label htmlFor="notes" className="text-sm font-medium text-foreground">
                      Notas
                    </label>
                    <Input
                      id="notes"
                      value={form.notes}
                      onChange={(event) => updateField("notes", event.target.value)}
                      disabled={createStockExit.isPending}
                      placeholder="Observaciones del albarán"
                    />
                    {fieldErrors.notes ? (
                      <p className="text-xs text-destructive">{fieldErrors.notes}</p>
                    ) : null}
                  </div>
                </div>

                <CardFooter className="flex justify-end gap-2 px-0 pb-0 pt-6">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => {
                      setForm(INITIAL_FORM)
                      setFieldErrors({})
                      setError(null)
                      setSuccess(null)
                    }}
                    disabled={createStockExit.isPending}
                  >
                    Limpiar
                  </Button>
                  <Button
                    type="submit"
                    disabled={createStockExit.isPending}
                    className="flex items-center gap-2"
                  >
                    {createStockExit.isPending ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Registrando salida…
                      </>
                    ) : (
                      <>
                        <PackageMinus className="h-4 w-4" />
                        Generar albarán de salida
                      </>
                    )}
                  </Button>
                </CardFooter>
              </form>
            )}
          </CardContent>
        </Card>
      </RoleGuard>
    </div>
  )
}
