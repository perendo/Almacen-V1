export const dynamic = "force-dynamic"

import Link from "next/link"
import { Button } from "@/components/ui/button"

export default function SerialsPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Números de Serie</h1>
          <p className="text-muted-foreground">Seguimiento unitario de productos electrónicos y maquinaria</p>
        </div>
        <Button>Nuevo número de serie</Button>
      </div>

      <div className="rounded-md border">
        <div className="p-6">
          <div className="flex items-center gap-2 mb-4">
            <Link href="/dashboard/serials/[serial]">
              <Button variant="outline">Ver trazabilidad de un número de serie</Button>
            </Link>
          </div>
          <p className="text-muted-foreground">
            El seguimiento por número de serie permite rastrear un producto individual desde su entrada hasta su venta, incluyendo ubicación histórica y cliente destino.
          </p>
        </div>
      </div>
    </div>
  )
}