export const dynamic = "force-dynamic"

import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"

export default function StockPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Stock por Ubicación</h1>
        <p className="text-muted-foreground">Inventario disponible por almacén y ubicación</p>
      </div>

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
            {[1, 2, 3, 4, 5].map((i) => (
              <TableRow key={i}>
                <TableCell className="font-medium">ELEC-{String(i).padStart(3, "0")}</TableCell>
                <TableCell>WH001</TableCell>
                <TableCell>A01-S01-B00{i}</TableCell>
                <TableCell>LOT-2024-{String(i).padStart(3, "0")}</TableCell>
                <TableCell>{100 * i}</TableCell>
                <TableCell>{100 * i}</TableCell>
                <TableCell>
                  <Badge variant={i % 3 === 0 ? "destructive" : "default"}>
                    {i % 3 === 0 ? "Bloqueado" : "Disponible"}
                  </Badge>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}