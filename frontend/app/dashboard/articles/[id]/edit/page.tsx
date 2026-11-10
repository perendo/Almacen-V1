export const dynamic = "force-dynamic"

import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"

export default function ArticleEditPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Editar Artículo</h1>
          <p className="text-muted-foreground">Modificar datos del artículo</p>
        </div>
        <Button variant="outline">Cancelar</Button>
        <Button>Guardar cambios</Button>
      </div>

      <div className="rounded-md border p-6">
        <form className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Código Interno</label>
              <input className="h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm" type="text" placeholder="ELEC-001" />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">EAN-13</label>
              <input className="h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm" type="text" placeholder="8400000000001" />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Familia</label>
              <select className="h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
                <option>Electrónica</option>
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Marca</label>
              <select className="h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
                <option>Samsung</option>
              </select>
            </div>
          </div>
        </form>
      </div>
    </div>
  )
}