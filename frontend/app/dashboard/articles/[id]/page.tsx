"use client"

import { useMemo } from "react"
import Link from "next/link"
import { useParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { EmptyState } from "@/components/ui/empty-state"
import { ErrorState } from "@/components/ui/error-state"
import { RoleGuard } from "@/components/role-guard"
import {
  useArticleBrands,
  useArticleFamilies,
  useBins,
  useLots,
  useWarehouses,
} from "@/hooks/useApi"
import { useArticle, useArticleTranslations, useStock } from "@/hooks/useArticles"
import { ApiError } from "@/lib/api"
import { formatDate } from "@/lib/utils"
import type { StockOut } from "@/types/stock"

const EDIT_ROLES = ["SuperAdmin", "Gerente de Almacén"]

export default function ArticleDetailPage() {
  const params = useParams<{ id: string }>()
  const articleId = Number(params?.id)
  const validId = Number.isFinite(articleId) && articleId > 0

  const articleQuery = useArticle(articleId)
  const translationsQuery = useArticleTranslations(articleId)
  const stockQuery = useStock(
    { article_id: String(articleId), limit: "1000" },
    { enabled: validId }
  )
  const familiesQuery = useArticleFamilies({ limit: "1000" })
  const brandsQuery = useArticleBrands({ limit: "1000" })
  const warehousesQuery = useWarehouses({ limit: "1000" })
  const binsQuery = useBins({ limit: "1000" })
  const lotsQuery = useLots({ limit: "1000" })

  const article = articleQuery.data
  const stockRows: StockOut[] = stockQuery.data ?? []

  const translation = useMemo(() => {
    const list = translationsQuery.data ?? []
    return list.find((item) => item.language_code === "es") ?? list[0]
  }, [translationsQuery.data])

  const familyName = useMemo(
    () =>
      article?.family_id
        ? familiesQuery.data?.find((family) => family.id === article.family_id)?.name ?? `Familia #${article.family_id}`
        : "—",
    [article, familiesQuery.data]
  )

  const brandName = useMemo(
    () =>
      article?.brand_id
        ? brandsQuery.data?.find((brand) => brand.id === article.brand_id)?.name ?? `Marca #${article.brand_id}`
        : "—",
    [article, brandsQuery.data]
  )

  const warehouseCodes = useMemo(() => {
    const map = new Map<number, string>()
    warehousesQuery.data?.forEach((warehouse) => map.set(warehouse.id, warehouse.code))
    return map
  }, [warehousesQuery.data])

  const binCodes = useMemo(() => {
    const map = new Map<number, string>()
    binsQuery.data?.forEach((bin) => map.set(bin.id, bin.code))
    return map
  }, [binsQuery.data])

  const lotNumbers = useMemo(() => {
    const map = new Map<number, string>()
    lotsQuery.data?.forEach((lot) => map.set(lot.id, lot.lot_number))
    return map
  }, [lotsQuery.data])

  const isNotFound = articleQuery.error instanceof ApiError && articleQuery.error.status === 404

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{translation?.name || "Detalle de Artículo"}</h1>
          <p className="text-muted-foreground">Información completa del artículo</p>
        </div>
        <div className="flex gap-2">
          <Link href="/dashboard/articles">
            <Button variant="outline">Volver al listado</Button>
          </Link>
          {article ? (
            <RoleGuard roles={EDIT_ROLES}>
              <Link href={`/dashboard/articles/${article.id}/edit`}>
                <Button>Editar artículo</Button>
              </Link>
            </RoleGuard>
          ) : null}
        </div>
      </div>

      {articleQuery.isLoading ? (
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          <Skeleton className="h-72 w-full" />
          <Skeleton className="h-72 w-full" />
        </div>
      ) : null}

      {isNotFound ? (
        <EmptyState
          title="Artículo no encontrado"
          description={`No existe ningún artículo con el identificador ${params?.id ?? ""}.`}
          actionHref="/dashboard/articles"
          actionLabel="Volver al listado de artículos"
        />
      ) : null}

      {articleQuery.error && !isNotFound ? (
        <ErrorState
          message={
            articleQuery.error instanceof Error
              ? articleQuery.error.message
              : "Error cargando el artículo"
          }
          onRetry={() => void articleQuery.refetch()}
        />
      ) : null}

      {article ? (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div className="rounded-md border p-6">
            <h2 className="mb-4 text-lg font-semibold">Datos Generales</h2>
            <Table>
              <TableBody>
                <TableRow>
                  <TableCell className="w-1/3 font-medium">Código Interno</TableCell>
                  <TableCell>{article.internal_code}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell className="font-medium">EAN-13</TableCell>
                  <TableCell>{article.ean13 || "—"}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell className="font-medium">Referencia proveedor</TableCell>
                  <TableCell>{article.supplier_reference || "—"}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell className="font-medium">Nombre</TableCell>
                  <TableCell>{translation?.name || "—"}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell className="font-medium">Familia</TableCell>
                  <TableCell>{familyName}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell className="font-medium">Marca</TableCell>
                  <TableCell>{brandName}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell className="font-medium">Clase ABC</TableCell>
                  <TableCell>
                    <Badge variant="outline">{article.abc_class}</Badge>
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell className="font-medium">Requiere Lote</TableCell>
                  <TableCell>
                    <Badge variant={article.lot_required ? "default" : "secondary"}>
                      {article.lot_required ? "Sí" : "No"}
                    </Badge>
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell className="font-medium">Serializado</TableCell>
                  <TableCell>
                    <Badge variant={article.is_serialized ? "default" : "secondary"}>
                      {article.is_serialized ? "Sí" : "No"}
                    </Badge>
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell className="font-medium">Estado</TableCell>
                  <TableCell>
                    <Badge variant={article.is_active ? "default" : "destructive"}>
                      {article.is_active ? "Activo" : "Inactivo"}
                    </Badge>
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell className="font-medium">Peso / Volumen</TableCell>
                  <TableCell>
                    {article.weight_kg !== null ? `${article.weight_kg} kg` : "—"}
                    {" / "}
                    {article.volume_m3 !== null ? `${article.volume_m3} m³` : "—"}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell className="font-medium">Dimensiones</TableCell>
                  <TableCell>
                    {article.length_cm !== null || article.width_cm !== null || article.height_cm !== null
                      ? `${article.length_cm ?? "—"} × ${article.width_cm ?? "—"} × ${article.height_cm ?? "—"} cm`
                      : "—"}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell className="font-medium">Creado</TableCell>
                  <TableCell>{formatDate(article.created_at)}</TableCell>
                </TableRow>
                {translation?.description ? (
                  <TableRow>
                    <TableCell className="font-medium">Descripción</TableCell>
                    <TableCell className="whitespace-normal">{translation.description}</TableCell>
                  </TableRow>
                ) : null}
              </TableBody>
            </Table>
          </div>

          <div className="rounded-md border p-6">
            <h2 className="mb-4 text-lg font-semibold">Stock por Ubicación</h2>

            {stockQuery.isLoading ? (
              <div className="space-y-2">
                {[1, 2, 3].map((i) => (
                  <Skeleton key={i} className="h-10 w-full" />
                ))}
              </div>
            ) : stockQuery.error ? (
              <ErrorState
                title="No se pudo cargar el stock"
                message={
                  stockQuery.error instanceof Error
                    ? stockQuery.error.message
                    : "Error cargando las existencias del artículo"
                }
                onRetry={() => void stockQuery.refetch()}
              />
            ) : stockRows.length === 0 ? (
              <EmptyState
                title="Sin existencias"
                description="Este artículo todavía no tiene stock registrado en ninguna ubicación."
              />
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Almacén</TableHead>
                    <TableHead>Ubicación</TableHead>
                    <TableHead>Lote</TableHead>
                    <TableHead>Cantidad</TableHead>
                    <TableHead>Disponible</TableHead>
                    <TableHead>Estado</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {stockRows.map((item) => (
                    <TableRow key={item.id}>
                      <TableCell>
                        {warehouseCodes.get(item.warehouse_id) ?? `WH#${item.warehouse_id}`}
                      </TableCell>
                      <TableCell>
                        {item.bin_id ? binCodes.get(item.bin_id) ?? `Bin#${item.bin_id}` : "—"}
                      </TableCell>
                      <TableCell>
                        {item.lot_id ? lotNumbers.get(item.lot_id) ?? `Lote#${item.lot_id}` : "—"}
                      </TableCell>
                      <TableCell>{item.quantity}</TableCell>
                      <TableCell>{item.available_quantity}</TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            item.status === "available"
                              ? "default"
                              : item.status === "quarantined"
                                ? "secondary"
                                : "destructive"
                          }
                        >
                          {item.status}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </div>
        </div>
      ) : null}
    </div>
  )
}
