export const dynamic = "force-dynamic"

import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"

export default function MovementsPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Movimientos de Stock</h1>
          <p className="text-muted-foreground">Entradas, salidas, traslados internos y ajustes</p>
        </div>
        <div className="flex gap-2">
          <Button>Nueva entrada</Button>
          <Button variant="outline">Nueva salida</Button>
          <Button variant="outline">Traspaso interno</Button>
        </div>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Fecha</TableHead>
              <TableHead>Tipo</TableHead>
              <TableHead>Artículo</TableHead>
              <TableHead>Cantidad</TableHead>
              <TableHead>Usuario</TableHead>
              <TableHead className="text-right">Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {[1, 2, 3].map((i) => (
              <TableRow key={i}>
                <TableCell className="font-medium">2024-01-{String(i).padStart(2, "0")}</TableCell>
                <TableCell>
                  <Badge variant={i === 1 ? "default" : i === 2 ? "destructive" : "secondary"}>
                    {i === 1 ? "Entrada" : i === 2 ? "Salida" : "Traspaso"}
                  </Badge>
                </TableCell>
                <TableCell>ELEC-00{i}</TableCell>
                <TableCell>{100 * i}</TableCell>
                <TableCell>Usuario {i}</TableCell>
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