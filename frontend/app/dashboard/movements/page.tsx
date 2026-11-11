"use client"

export const dynamic = "force-dynamic"

import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"

export default function MovementsPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Movimientos de Stock</h1>
          <p className="text-muted-foreground">Entradas, salidas, traslados internos y ajustes</p>
        </div>
        <div className="flex gap-2">
          <Link href="/dashboard/movements/entry" className="inline-flex items-center justify-center rounded-md text-sm font-medium border border-input bg-background hover:bg-accent hover:text-accent-foreground px-4 py-2 transition-colors">
            Nueva entrada
          </Link>
          <Link href="/dashboard/movements/exit" className="inline-flex items-center justify-center rounded-md text-sm font-medium border border-input bg-background hover:bg-accent hover:text-accent-foreground px-4 py-2 transition-colors">
            Nueva salida
          </Link>
          <Link href="/dashboard/movements/transfer" className="inline-flex items-center justify-center rounded-md text-sm font-medium border border-input bg-background hover:bg-accent hover:text-accent-foreground px-4 py-2 transition-colors">
            Traspaso interno
          </Link>
        </div>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Fecha</TableHead>
              <TableHead>Tipo</TableHead>
              <TableHead>Artículo</TableHead>
              <TableHead>Cantidad</TableHead>
              <TableHead>Usuario</TableHead>
              <TableHead className="text-right">Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {[1, 2, 3].map((i) => (
              <TableRow key={i}>
                <TableCell className="font-medium">2024-01-{String(i).padStart(2, "0")}</TableCell>
                <TableCell>
                  <Badge variant={i === 1 ? "default" : i === 2 ? "destructive" : "secondary"}>
                    {i === 1 ? "Entrada" : i === 2 ? "Salida" : "Traspaso"}
                  </Badge>
                </TableCell>
                <TableCell>ELEC-00{i}</TableCell>
                <TableCell>{100 * i}</TableCell>
                <TableCell>Usuario {i}</TableCell>
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
