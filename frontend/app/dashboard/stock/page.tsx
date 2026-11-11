"use client"

export const dynamic = "force-dynamic"

import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { useStock } from "@/hooks/useArticles"
import type { StockOut } from "@/types/stock"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert } from "@/components/ui/alert"

export default function StockPage() {
  const { data: stock, isLoading, error } = useStock()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Stock por Ubicación</h1>
        <p className="text-muted-foreground">Inventario disponible por almacén y ubicación</p>
      </div>

      {isLoading && (
        <div className="rounded-md border p-4">
          {[1, 2, 3, 4, 5].map((i) => (
            <TableRow key={i}>
              <Skeleton className="h-10 w-32" />
              <Skeleton className="h-10 w-20" />
              <Skeleton className="h-10 w-24" />
              <Skeleton className="h-10 w-20" />
              <Skeleton className="h-10 w-16" />
              <Skeleton className="h-10 w-16" />
              <Skeleton className="h-10 w-16" />
            </TableRow>
          ))}
        </div>
      )}

      {error && (
        <Alert variant="destructive">
          Error cargando el stock. Intente nuevamente.
        </Alert>
      )}

      {!isLoading && !error && (
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Artículo</TableHead>
                <TableHead>Almacén</TableHead>
                <TableHead>Ubicación (Bin)</TableHead>
                <TableHead>Lote</TableHead>
                <TableHead>Cantidad</TableHead>
                <TableHead>Disponible</TableHead>
                <TableHead>Estado</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(stock as StockOut[] | undefined)?.map((item) => (
                <TableRow key={item.id}>
                  <TableCell className="font-medium">{String(item.article_id)}</TableCell>
                  <TableCell>{String(item.warehouse_id)}</TableCell>
                  <TableCell>{String(item.bin_id ?? "—")}</TableCell>
                  <TableCell>{String(item.lot_id ?? "—")}</TableCell>
                  <TableCell>{item.quantity}</TableCell>
                  <TableCell>{item.available_quantity}</TableCell>
                  <TableCell>
                    <Badge variant={item.status === "available" ? "default" : item.status === "quarantined" ? "secondary" : "destructive"}>
                      {item.status}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  )
}
