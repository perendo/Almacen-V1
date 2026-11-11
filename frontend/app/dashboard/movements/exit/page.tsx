"use client"

import { useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { useCreateStockExit } from "@/hooks/useApi"
import type { StockExitCreate } from "@/types/stock"
import { Loader2, PackageMinus } from "lucide-react"

const exitSchema = z.object({
  warehouse_id: z.coerce.number(),
  from_bin_id: z.coerce.number().optional(),
  article_id: z.coerce.number(),
  lot_id: z.coerce.number().optional(),
  serial_id: z.coerce.number().optional(),
  quantity: z.coerce.number().gt(0, "La cantidad debe ser mayor a 0"),
  uom_id: z.coerce.number(),
  strategy: z.enum(["FIFO", "FEFO"]).default("FIFO"),
  reference_type: z.string().optional(),
  reference_id: z.coerce.number().optional(),
  notes: z.string().optional(),
})

type ExitFormData = z.infer<typeof exitSchema>

export default function StockExitPage() {
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const createStockExit = useCreateStockExit()

  const form = useForm<ExitFormData>({
    resolver: zodResolver(exitSchema),
    defaultValues: {
      warehouse_id: undefined,
      from_bin_id: undefined,
      article_id: undefined,
      lot_id: undefined,
      serial_id: undefined,
      quantity: 1,
      uom_id: undefined,
      strategy: "FIFO",
      reference_type: undefined,
      reference_id: undefined,
      notes: "",
    },
  })

  async function onSubmit(values: ExitFormData) {
    setError(null)
    setIsSubmitting(true)
    try {
      const body: StockExitCreate = {
        warehouse_id: values.warehouse_id,
        from_bin_id: values.from_bin_id,
        article_id: values.article_id,
        lot_id: values.lot_id,
        serial_id: values.serial_id,
        quantity: values.quantity,
        uom_id: values.uom_id,
        strategy: values.strategy,
        reference_type: values.reference_type,
        reference_id: values.reference_id,
        notes: values.notes || undefined,
      }
      await createStockExit.mutateAsync(body)
      form.reset()
      setError(null)
    } catch (err: any) {
      setError(err?.message ?? "Error al registrar la salida de stock")
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Salida de Stock — Albarán</h1>
          <p className="text-muted-foreground">
            Registre una salida/expedición de mercancía del almacén
          </p>
        </div>
        <Button onClick={() => window.location.href = "/dashboard/movements"} variant="outline">
          Volver a movimientos
        </Button>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Datos de la salida</CardTitle>
          <CardDescription>
            Complete los datos del albarán de salida de mercancía
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">Almacén de origen *</label>
                <select
                  className="h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  onChange={(e) =>
                    form.setValue(
                      "warehouse_id",
                      Number((e.target as HTMLSelectElement).value)
                    )
                  }
                  disabled={isSubmitting}
                >
                  <option value="">Seleccionar almacén</option>
                  <option value={1}>Almacén General (WH001)</option>
                  <option value={2}>Almacén de Tránsito (WH002)</option>
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">Ubicación (Bin) *</label>
                <select
                  className="h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  onChange={(e) =>
                    form.setValue(
                      "from_bin_id",
                      Number((e.target as HTMLSelectElement).value) || undefined
                    )
                  }
                  disabled={isSubmitting}
                >
                  <option value="">Seleccionar bin</option>
                  <option value={101}>A01-S01-B001</option>
                  <option value={102}>A01-S01-B002</option>
                  <option value={103}>A01-S02-B003</option>
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">Artículo *</label>
                <select
                  className="h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  onChange={(e) =>
                    form.setValue(
                      "article_id",
                      Number((e.target as HTMLSelectElement).value)
                    )
                  }
                  disabled={isSubmitting}
                >
                  <option value="">Seleccionar artículo</option>
                  <option value={1}>ELEC-001 — Componente Electrónico</option>
                  <option value={2}>ALIM-005 — Producto Alimenticio</option>
                  <option value={3}>FERR-012 — Herramienta Ferretería</option>
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">Lote</label>
                <select
                  className="h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  onChange={(e) =>
                    form.setValue(
                      "lot_id",
                      Number((e.target as HTMLSelectElement).value) || undefined
                    )
                  }
                  disabled={isSubmitting}
                >
                  <option value="">Seleccionar lote (opcional)</option>
                  <option value={201}>LOT-2024-001</option>
                  <option value={202}>LOT-2024-002</option>
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">Número de serie</label>
                <select
                  className="h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  onChange={(e) =>
                    form.setValue(
                      "serial_id",
                      Number((e.target as HTMLSelectElement).value) || undefined
                    )
                  }
                  disabled={isSubmitting}
                >
                  <option value="">Seleccionar serie (opcional)</option>
                  <option value={301}>SN-10001</option>
                  <option value={302}>SN-10002</option>
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">Cantidad *</label>
                <Input
                  type="number"
                  min="0.01"
                  step="0.01"
                  value={form.getValues("quantity") || ""}
                  onChange={(e) =>
                    form.setValue("quantity", e.target.valueAsNumber ?? 0)
                  }
                  disabled={isSubmitting}
                  placeholder="0"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">Unidad de medida *</label>
                <select
                  className="h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  onChange={(e) =>
                    form.setValue(
                      "uom_id",
                      Number((e.target as HTMLSelectElement).value)
                    )
                  }
                  disabled={isSubmitting}
                >
                  <option value="">Seleccionar UOM</option>
                  <option value={1}>Unidad (UNI)</option>
                  <option value={2}>Caja (CAJA)</option>
                  <option value={3}>Palé (PALET)</option>
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">Estrategia</label>
                <select
                  className="h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  onChange={(e) =>
                    form.setValue(
                      "strategy",
                      (e.target as HTMLSelectElement).value as "FIFO" | "FEFO"
                    )
                  }
                  disabled={isSubmitting}
                >
                  <option value="FIFO">FIFO (primero en entrar, primero en salir)</option>
                  <option value="FEFO">FEFO (primero en caducar, primero en salir)</option>
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">Tipo de referencia</label>
                <Input
                  value={form.getValues("reference_type") ?? ""}
                  onChange={(e) => form.setValue("reference_type", e.target.value)}
                  disabled={isSubmitting}
                  placeholder="Ej: sales_order"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">ID de referencia</label>
                <Input
                  type="number"
                  value={String(form.getValues("reference_id") ?? "")}
                  onChange={(e) =>
                    form.setValue("reference_id", e.target.valueAsNumber ?? undefined)
                  }
                  disabled={isSubmitting}
                  placeholder="Ej: 12345"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">Notas</label>
                <Input
                  value={form.getValues("notes") ?? ""}
                  onChange={(e) => form.setValue("notes", e.target.value)}
                  disabled={isSubmitting}
                  placeholder="Observaciones del albarán"
                />
              </div>
            </div>

            <CardFooter className="flex justify-end gap-2 pt-6">
              <Button
                type="button"
                variant="outline"
                onClick={() => form.reset()}
                disabled={isSubmitting}
              >
                Limpiar
              </Button>
              <Button
                type="submit"
                disabled={isSubmitting}
                className="flex items-center gap-2"
              >
                {isSubmitting ? (
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
        </CardContent>
      </Card>
    </div>
  )
}
