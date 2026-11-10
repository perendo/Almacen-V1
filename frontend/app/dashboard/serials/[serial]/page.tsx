export const dynamic = "force-dynamic"

import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"

export default function SerialDetailPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Trazabilidad de Serie</h1>
          <p className="text-muted-foreground">Historial completo de ubicaciones y movimientos</p>
        </div>
        <Link href="/dashboard/serials">
          <Button variant="outline">Volver a listado</Button>
        </Link>
      </div>

      <div className="rounded-md border p-6">
        <h2 className="text-lg font-semibold mb-4">Serie: SN-2024-0001</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 border rounded-lg">
            <h3 className="text-sm font-semibold text-muted-foreground">Artículo</h3>
            <p className="text-sm">ELEC-001 - Componente Electrónico</p>
          </div>
          <div className="p-4 border rounded-lg">
            <h3 className="text-sm font-semibold text-muted-foreground">Ubicación actual</h3>
            <p className="text-sm">{`WH001 &gt; Z01 &gt; A01 &gt; S01 &gt; B001`}</p>
          </div>
          <div className="p-4 border rounded-lg">
            <h3 className="text-sm font-semibold text-muted-foreground">Estado</h3>
            <p className="text-sm">En stock</p>
          </div>
          <div className="p-4 border rounded-lg">
            <h3 className="text-sm font-semibold text-muted-foreground">Lote</h3>
            <p className="text-sm">LOT-2024-001</p>
          </div>
        </div>

        <div className="mt-6">
          <h3 className="text-sm font-semibold text-muted-foreground">Historial de Movimientos</h3>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Fecha</TableHead>
                <TableHead>Tipo</TableHead>
                <TableHead>Origen</TableHead>
                <TableHead>Destino</TableHead>
                <TableHead>Usuario</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {[1, 2].map((i) => (
                <TableRow key={i}>
                  <TableCell className="font-medium">2024-01-{String(i).padStart(2, "0")}</TableCell>
                  <TableCell>
                    <Badge variant={i === 1 ? "default" : "secondary"}>
                      {i === 1 ? "Entrada" : "Traspaso"}
                    </Badge>
                  </TableCell>
                  <TableCell>Recepción</TableCell>
                  <TableCell>WH001-B001</TableCell>
                  <TableCell>Usuario {i}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>
    </div>
  )
}