export const dynamic = "force-dynamic"

import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"

export default function LotsPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Lotes</h1>
          <p className="text-muted-foreground">Gestión de lotes y trazabilidad</p>
        </div>
        <Button>Nuevo lote</Button>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Número de Lote</TableHead>
              <TableHead>Artículo</TableHead>
              <TableHead>Fecha Caducidad</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead className="text-right">Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {[1, 2].map((i) => (
              <TableRow key={i}>
                <TableCell className="font-medium">LOT-2024-{String(i).padStart(3, "0")}</TableCell>
                <TableCell>ELEC-{String(i).padStart(3, "0")}</TableCell>
                <TableCell>2025-12-31</TableCell>
                <TableCell><Badge variant="default">Activo</Badge></TableCell>
                <TableCell className="text-right">
                  <Button variant="outline" size="sm">Ver</Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}