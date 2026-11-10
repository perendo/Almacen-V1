export const dynamic = "force-dynamic"

import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"

export default function AdjustmentsPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Ajustes y Mermas</h1>
          <p className="text-muted-foreground">Bajas, mermas, caducidad y entradas extraordinarias</p>
        </div>
        <Button>Nuevo ajuste</Button>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Tipo</TableHead>
              <TableHead>Motivo</TableHead>
              <TableHead>Artículo</TableHead>
              <TableHead>Cantidad</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead className="text-right">Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {[1, 2].map((i) => (
              <TableRow key={i}>
                <TableCell>
                  <Badge variant="destructive">Pérdida</Badge>
                </TableCell>
                <TableCell>Merma por caducidad</TableCell>
                <TableCell>ALIM-00{i}</TableCell>
                <TableCell>{5 * i}</TableCell>
                <TableCell>
                  <Badge variant={i === 1 ? "secondary" : "default"}>
                    {i === 1 ? "Pendiente" : "Aprobado"}
                  </Badge>
                </TableCell>
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