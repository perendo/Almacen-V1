export const dynamic = "force-dynamic"

import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"

export default function ArticleFamiliesPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Familias de Artículos</h1>
          <p className="text-muted-foreground">Categorización de artículos por familia</p>
        </div>
        <Button>Nueva familia</Button>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nombre</TableHead>
              <TableHead>Código</TableHead>
              <TableHead>Empresa</TableHead>
              <TableHead className="text-right">Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {[
              { name: "Electrónica", code: "ELEC" },
              { name: "Alimentos", code: "ALIM" },
              { name: "Ferretería", code: "FERR" },
            ].map((f, i) => (
              <TableRow key={i}>
                <TableCell className="font-medium">{f.name}</TableCell>
                <TableCell>{f.code}</TableCell>
                <TableCell>Demo Company</TableCell>
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