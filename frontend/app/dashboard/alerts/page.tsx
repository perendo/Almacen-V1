export const dynamic = "force-dynamic"

import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"

export default function AlertsPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Alertas</h1>
          <p className="text-muted-foreground">Stock mínimo, caducidad y productos sin movimiento</p>
        </div>
        <Button>Ver propuestas de reabastecimiento</Button>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Tipo</TableHead>
              <TableHead>Artículo</TableHead>
              <TableHead>Severidad</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead>Mensaje</TableHead>
              <TableHead className="text-right">Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {[1, 2, 3].map((i) => (
              <TableRow key={i}>
                <TableCell>
                  <Badge variant={i === 1 ? "destructive" : i === 2 ? "secondary" : "default"}>
                    {i === 1 ? "Caducidad" : i === 2 ? "Stock Mínimo" : "Stock Máximo"}
                  </Badge>
                </TableCell>
                <TableCell>ART-{String(i).padStart(3, "0")}</TableCell>
                <TableCell>
                  <Badge variant={i === 1 ? "destructive" : i === 2 ? "secondary" : "default"}>
                    {i === 1 ? "Crítica" : i === 2 ? "Media" : "Baja"}
                  </Badge>
                </TableCell>
                <TableCell>
                  <Badge variant="secondary">Abierta</Badge>
                </TableCell>
                <TableCell>Requiere atención inmediata</TableCell>
                <TableCell className="text-right">
                  <Button variant="outline" size="sm">Resolver</Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}