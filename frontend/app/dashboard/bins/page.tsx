export const dynamic = "force-dynamic"

import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"

export default function BinsPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Huecos (Bins)</h1>
          <p className="text-muted-foreground">Gestión de ubicaciones de almacenamiento</p>
        </div>
        <Button>Nuevo bin</Button>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Código</TableHead>
              <TableHead>Estantería</TableHead>
              <TableHead>Capacidad Volumen</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead className="text-right">Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {[1].map((i) => (
              <TableRow key={i}>
                <TableCell className="font-medium">B001</TableCell>
                <TableCell>Estantería 1</TableCell>
                <TableCell>10 m³</TableCell>
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