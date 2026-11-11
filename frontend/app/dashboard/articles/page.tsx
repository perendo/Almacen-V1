"use client"

export const dynamic = "force-dynamic"

import { useMemo, useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { EmptyState } from "@/components/ui/empty-state"
import { ErrorState } from "@/components/ui/error-state"
import { RoleGuard } from "@/components/role-guard"
import { useArticles, useStock } from "@/hooks/useArticles"
import { useArticleFamilies } from "@/hooks/useApi"
import type { Article } from "@/types/master-data"

const EDIT_ROLES = ["SuperAdmin", "Gerente de Almacén"]

export default function ArticlesPage() {
  const [search, setSearch] = useState("")
  const { data: articles, isLoading, error, refetch } = useArticles({ limit: "1000" })
  const { data: stock } = useStock({ limit: "1000" })
  const { data: families } = useArticleFamilies({ limit: "1000" })

  const familyNames = useMemo(() => {
    const map = new Map<number, string>()
    families?.forEach((family) => map.set(family.id, family.name))
    return map
  }, [families])

  const stockByArticle = useMemo(() => {
    const map = new Map<number, number>()
    stock?.forEach((item) => map.set(item.article_id, (map.get(item.article_id) ?? 0) + item.quantity))
    return map
  }, [stock])

  const filteredArticles = useMemo(() => {
    const list = articles ?? []
    const term = search.trim().toLowerCase()
    if (!term) return list
    return list.filter((article) =>
      [article.internal_code, article.ean13, article.supplier_reference]
        .filter((value): value is string => typeof value === "string")
        .some((value) => value.toLowerCase().includes(term))
    )
  }, [articles, search])

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Artículos</h1>
          <p className="text-muted-foreground">Maestro de artículos y existencias</p>
        </div>
        <Button variant="outline" onClick={() => void refetch()}>
          Actualizar
        </Button>
      </div>

      <div className="mb-4 flex items-center gap-2">
        <Input
          placeholder="Buscar por código interno, EAN o referencia de proveedor..."
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
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

      {error && !isLoading && (
        <ErrorState
          message={error instanceof Error ? error.message : "Error cargando artículos"}
          onRetry={() => void refetch()}
        />
      )}

      {!isLoading && !error && filteredArticles.length === 0 && (
        <EmptyState
          title={search ? "Ningún artículo coincide con la búsqueda" : "No hay artículos registrados"}
          description={
            search
              ? "Pruebe con otro código interno, EAN o referencia de proveedor."
              : "Cree artículos en el maestro para poder registrar stock y movimientos."
          }
        />
      )}

      {!isLoading && !error && filteredArticles.length > 0 && (
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Código Interno</TableHead>
                <TableHead>EAN-13</TableHead>
                <TableHead>Referencia proveedor</TableHead>
                <TableHead>Familia</TableHead>
                <TableHead>Stock</TableHead>
                <TableHead>Estado</TableHead>
                <TableHead className="text-right">Acciones</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredArticles.map((article: Article) => (
                <TableRow key={article.id}>
                  <TableCell className="font-medium">
                    <Link
                      href={`/dashboard/articles/${article.id}`}
                      className="text-primary underline-offset-4 hover:underline"
                    >
                      {article.internal_code}
                    </Link>
                  </TableCell>
                  <TableCell>{article.ean13 || "—"}</TableCell>
                  <TableCell>{article.supplier_reference || "—"}</TableCell>
                  <TableCell>
                    {article.family_id
                      ? familyNames.get(article.family_id) ?? `Familia #${article.family_id}`
                      : "—"}
                  </TableCell>
                  <TableCell>{stockByArticle.get(article.id) ?? 0}</TableCell>
                  <TableCell>
                    <Badge variant={article.is_active ? "default" : "destructive"}>
                      {article.is_active ? "Activo" : "Inactivo"}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      <Link href={`/dashboard/articles/${article.id}`}>
                        <Button variant="outline" size="sm">
                          Ver
                        </Button>
                      </Link>
                      <RoleGuard roles={EDIT_ROLES}>
                        <Link href={`/dashboard/articles/${article.id}/edit`}>
                          <Button variant="outline" size="sm">
                            Editar
                          </Button>
                        </Link>
                      </RoleGuard>
                    </div>
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
