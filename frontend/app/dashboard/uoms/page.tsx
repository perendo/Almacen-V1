export const dynamic = "force-dynamic"

import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"

export default function UomsPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Unidades de Medida</h1>
          <p className="text-muted-foreground">Unidades de compra, almacenamiento y venta</p>
        </div>
        <Button>Nueva UOM</Button>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Código</TableHead>
              <TableHead>Nombre</TableHead>
              <TableHead>Tipo</TableHead>
              <TableHead>Es Base</TableHead>
              <TableHead className="text-right">Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {[
              { code: "UNI", name: "Unidad", type: "Almacenamiento", base: "Sí" },
              { code: "CAJA", name: "Caja", type: "Almacenamiento", base: "No" },
              { code: "PALET", name: "Palé", type: "Almacenamiento", base: "No" },
            ].map((u, i) => (
              <TableRow key={i}>
                <TableCell className="font-medium">{u.code}</TableCell>
                <TableCell>{u.name}</TableCell>
                <TableCell>{u.type}</TableCell>
                <TableCell>{u.base}</TableCell>
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