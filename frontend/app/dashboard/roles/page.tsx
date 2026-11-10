export const dynamic = "force-dynamic"

import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"

export default function RolesPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Roles y Permisos</h1>
          <p className="text-muted-foreground">Matriz de roles RBAC por módulo y acción</p>
        </div>
        <Button>Nuevo rol</Button>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Rol</TableHead>
              <TableHead>Descripción</TableHead>
              <TableHead>Alcance</TableHead>
              <TableHead>Permisos</TableHead>
              <TableHead className="text-right">Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {[
              { name: "SuperAdmin", desc: "Acceso global multiempresa", scope: "Global", perms: "Todos" },
              { name: "Gerente de Almacén", desc: "Gestión total de centros y aprobaciones", scope: "Empresa", perms: "CRUD + Aprobar" },
              { name: "Operario de Almacén", desc: "Recepción, picking, packing y recuento", scope: "Almacén", perms: "Crear/Leer/Editar" },
              { name: "Auditor", desc: "Acceso en modo lectura a informes", scope: "Empresa", perms: "Solo lectura" },
            ].map((r, i) => (
              <TableRow key={i}>
                <TableCell className="font-medium">{r.name}</TableCell>
                <TableCell>{r.desc}</TableCell>
                <TableCell>{r.scope}</TableCell>
                <TableCell><Badge variant="default">{r.perms}</Badge></TableCell>
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