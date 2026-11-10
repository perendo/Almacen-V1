export const dynamic = "force-dynamic"

import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"

export default function WarehousesPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Almacenes</h1>
          <p className="text-muted-foreground">Gestión de almacenes por centro</p>
        </div>
        <Button>Nuevo almacén</Button>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nombre</TableHead>
              <TableHead>Código</TableHead>
              <TableHead>Tipo</TableHead>
              <TableHead>Capacidad Volumen</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead className="text-right">Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {[1].map((i) => (
              <TableRow key={i}>
                <TableCell className="font-medium">Almacén General</TableCell>
                <TableCell>WH001</TableCell>
                <TableCell>
                  <Badge variant="default">General</Badge>
                </TableCell>
                <TableCell>1,000 m³</TableCell>
                <TableCell><Badge variant="default">Activo</Badge></TableCell>
                <TableCell className="text-right">
                  <Button variant="outline" size="sm">Editar</Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}