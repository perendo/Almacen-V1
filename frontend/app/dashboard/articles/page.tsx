"use client"

export const dynamic = "force-dynamic"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { useArticles } from "@/hooks/useArticles"
import type { Article } from "@/types/master-data"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert } from "@/components/ui/alert"

export default function ArticlesPage() {
  const { data: articles, isLoading, error } = useArticles()

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

      {isLoading && (
        <div className="rounded-md border p-4">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="flex items-center gap-4 py-3 border-b last:border-b-0">
              <Skeleton className="h-10 w-24" />
              <Skeleton className="h-10 w-32" />
              <Skeleton className="h-10 w-40" />
              <Skeleton className="h-10 w-32" />
              <Skeleton className="h-10 w-16" />
              <Skeleton className="h-10 w-16" />
            </div>
          ))}
        </div>
      )}

      {error && (
        <Alert variant="destructive">
          Error cargando artículos. Intente nuevamente.
        </Alert>
      )}

      {!isLoading && !error && (
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
              {(articles as Article[] | undefined)?.map((article) => (
                <TableRow key={article.id}>
                  <TableCell className="font-medium">{article.internal_code}</TableCell>
                  <TableCell>{article.ean13 || "—"}</TableCell>
                  <TableCell>{article.supplier_reference || article.internal_code}</TableCell>
                  <TableCell>{article.family_id ? "Familia " + article.family_id : "—"}</TableCell>
                  <TableCell>—</TableCell>
                  <TableCell>
                    <Badge variant={article.is_active ? "default" : "destructive"}>
                      {article.is_active ? "Activo" : "Inactivo"}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <Button variant="outline" size="sm">Editar</Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  )
}
