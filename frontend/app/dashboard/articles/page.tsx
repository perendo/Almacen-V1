export const dynamic = "force-dynamic"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"

export default function ArticlesPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Artículos</h1>
          <p className="text-muted-foreground">Maestro de artículos y existencias</p>
        </div>
        <Button>Nuevo artículo</Button>
      </div>

      <div className="flex items-center gap-2 mb-4">
        <Input placeholder="Buscar por código interno, EAN o descripción..." />
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Código Interno</TableHead>
              <TableHead>EAN-13</TableHead>
              <TableHead>Descripción</TableHead>
              <TableHead>Familia</TableHead>
              <TableHead>Stock</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead className="text-right">Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {[1, 2, 3].map((i) => (
              <TableRow key={i}>
                <TableCell className="font-medium">ELEC-{String(i).padStart(3, "0")}</TableCell>
                <TableCell>84000000000{i}</TableCell>
                <TableCell>Componente Electrónico {i}</TableCell>
                <TableCell>Electrónica</TableCell>
                <TableCell>120</TableCell>
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