export const dynamic = "force-dynamic"

import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"

export default function InventoryPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Inventarios Físicos</h1>
          <p className="text-muted-foreground">Conteos cíclicos y generales</p>
        </div>
        <Button>Nuevo conteo</Button>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Almacén</TableHead>
              <TableHead>Tipo</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead>Fecha</TableHead>
              <TableHead className="text-right">Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {[1, 2].map((i) => (
              <TableRow key={i}>
                <TableCell className="font-medium">WH001</TableCell>
                <TableCell>{i === 1 ? "Cíclico" : "General"}</TableCell>
                <TableCell>
                  <Badge variant={i === 1 ? "default" : "secondary"}>
                    {i === 1 ? "En progreso" : "Completado"}
                  </Badge>
                </TableCell>
                <TableCell>2024-01-{String(i).padStart(2, "0")}</TableCell>
                <TableCell className="text-right">
                  <Button variant="outline" size="sm">Ver líneas</Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}