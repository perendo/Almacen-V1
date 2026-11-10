import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"

export const dynamic = "force-dynamic"

export default function ArticleDetailPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Detalle de Artículo</h1>
          <p className="text-muted-foreground">Información completa del artículo</p>
        </div>
        <Button variant="outline">Editar artículo</Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="rounded-md border p-6">
          <h2 className="text-lg font-semibold mb-4">Datos Generales</h2>
          <Table>
            <TableBody>
              <TableRow>
                <TableCell className="w-1/3 font-medium">Código Interno</TableCell>
                <TableCell>ELEC-001</TableCell>
              </TableRow>
              <TableRow>
                <TableCell className="w-1/3 font-medium">EAN-13</TableCell>
                <TableCell>8400000000001</TableCell>
              </TableRow>
              <TableRow>
                <TableCell className="w-1/3 font-medium">Familia</TableCell>
                <TableCell>Electrónica</TableCell>
              </TableRow>
              <TableRow>
                <TableCell className="w-1/3 font-medium">Marca</TableCell>
                <TableCell>Samsung</TableCell>
              </TableRow>
              <TableRow>
                <TableCell className="w-1/3 font-medium">UOM Base</TableCell>
                <TableCell>Unidad</TableCell>
              </TableRow>
              <TableRow>
                <TableCell className="w-1/3 font-medium">Requiere Lote</TableCell>
                <TableCell><Badge variant="default">No</Badge></TableCell>
              </TableRow>
              <TableRow>
                <TableCell className="w-1/3 font-medium">Serializado</TableCell>
                <TableCell><Badge variant="default">No</Badge></TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </div>

        <div className="rounded-md border p-6">
          <h2 className="text-lg font-semibold mb-4">Stock por Ubicación</h2>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Almacén</TableHead>
                <TableHead>Ubicación</TableHead>
                <TableHead>Cantidad</TableHead>
                <TableHead>Disponible</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {[1, 2].map((i) => (
                <TableRow key={i}>
                  <TableCell>WH001</TableCell>
                  <TableCell>A01-S01-B00{i}</TableCell>
                  <TableCell>{100 * i}</TableCell>
                  <TableCell>{100 * i}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>
    </div>
  )
}