"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Skeleton } from "@/components/ui/skeleton"
import { EmptyState } from "@/components/ui/empty-state"
import { ErrorState } from "@/components/ui/error-state"
import { RoleGuard } from "@/components/role-guard"
import { useAuth } from "@/hooks/useAuth"
import { useArticleBrands, useArticleFamilies } from "@/hooks/useApi"
import { useArticle, useUpdateArticle } from "@/hooks/useArticles"
import { ApiError } from "@/lib/api"
import type { Article, ArticleUpdate } from "@/types/master-data"

const EDIT_ROLES = ["SuperAdmin", "Gerente de Almacén"]

const optionalNumber = z
  .string()
  .refine(
    (value) => value.trim() === "" || (Number.isFinite(Number(value)) && Number(value) >= 0),
    "Introduzca un número mayor o igual que 0"
  )

const articleSchema = z.object({
  internal_code: z.string().min(1, "El código interno es obligatorio").max(100),
  ean13: z
    .string()
    .regex(/^\d{0,13}$/, "El EAN-13 debe contener solo dígitos (máximo 13)")
    .optional(),
  supplier_reference: z.string().max(100, "Máximo 100 caracteres").optional(),
  family_id: z.string().optional(),
  brand_id: z.string().optional(),
  weight_kg: optionalNumber,
  volume_m3: optionalNumber,
  length_cm: optionalNumber,
  width_cm: optionalNumber,
  height_cm: optionalNumber,
  abc_class: z.enum(["A", "B", "C"]),
  is_serialized: z.boolean(),
  lot_required: z.boolean(),
  is_active: z.boolean(),
})

type ArticleFormValues = z.infer<typeof articleSchema>

const selectClassName =
  "h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"

function numberOrNull(value: string): number | null {
  return value.trim() === "" ? null : Number(value)
}

function idOrNull(value: string | undefined): number | null {
  if (!value) return null
  const parsed = Number(value)
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null
}

function toFormValues(article: Article): ArticleFormValues {
  return {
    internal_code: article.internal_code,
    ean13: article.ean13 ?? "",
    supplier_reference: article.supplier_reference ?? "",
    family_id: article.family_id ? String(article.family_id) : "",
    brand_id: article.brand_id ? String(article.brand_id) : "",
    weight_kg: article.weight_kg !== null ? String(article.weight_kg) : "",
    volume_m3: article.volume_m3 !== null ? String(article.volume_m3) : "",
    length_cm: article.length_cm !== null ? String(article.length_cm) : "",
    width_cm: article.width_cm !== null ? String(article.width_cm) : "",
    height_cm: article.height_cm !== null ? String(article.height_cm) : "",
    abc_class: article.abc_class === "A" || article.abc_class === "B" ? article.abc_class : "C",
    is_serialized: article.is_serialized,
    lot_required: article.lot_required,
    is_active: article.is_active,
  }
}

export default function ArticleEditPage() {
  const params = useParams<{ id: string }>()
  const router = useRouter()
  const articleId = Number(params?.id)
  const validId = Number.isFinite(articleId) && articleId > 0
  const { hasRole } = useAuth()
  const allowed = hasRole(EDIT_ROLES)

  const [submitError, setSubmitError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const articleQuery = useArticle(articleId)
  const familiesQuery = useArticleFamilies({ limit: "1000" })
  const brandsQuery = useArticleBrands({ limit: "1000" })
  const updateArticle = useUpdateArticle(articleId)

  const form = useForm<ArticleFormValues>({
    resolver: zodResolver(articleSchema),
    defaultValues: {
      internal_code: "",
      ean13: "",
      supplier_reference: "",
      family_id: "",
      brand_id: "",
      weight_kg: "",
      volume_m3: "",
      length_cm: "",
      width_cm: "",
      height_cm: "",
      abc_class: "C",
      is_serialized: false,
      lot_required: false,
      is_active: true,
    },
  })

  const article = articleQuery.data

  useEffect(() => {
    if (article) {
      form.reset(toFormValues(article))
    }
  }, [article, form])

  async function onSubmit(values: ArticleFormValues) {
    setSubmitError(null)
    setSuccess(null)
    const payload: ArticleUpdate = {
      internal_code: values.internal_code.trim(),
      ean13: values.ean13?.trim() ? values.ean13.trim() : null,
      supplier_reference: values.supplier_reference?.trim() ? values.supplier_reference.trim() : null,
      family_id: idOrNull(values.family_id),
      brand_id: idOrNull(values.brand_id),
      weight_kg: numberOrNull(values.weight_kg),
      volume_m3: numberOrNull(values.volume_m3),
      length_cm: numberOrNull(values.length_cm),
      width_cm: numberOrNull(values.width_cm),
      height_cm: numberOrNull(values.height_cm),
      is_serialized: values.is_serialized,
      lot_required: values.lot_required,
      abc_class: values.abc_class,
      is_active: values.is_active,
    }

    try {
      await updateArticle.mutateAsync(payload)
      setSuccess("Cambios guardados correctamente")
      router.push(`/dashboard/articles/${articleId}`)
    } catch (err) {
      if (err instanceof ApiError) {
        setSubmitError(typeof err.data?.detail === "string" ? err.data.detail : err.message)
      } else {
        setSubmitError(err instanceof Error ? err.message : "No se pudo guardar el artículo")
      }
    }
  }

  const isNotFound = articleQuery.error instanceof ApiError && articleQuery.error.status === 404

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Editar Artículo</h1>
          <p className="text-muted-foreground">
            {article ? `Modificando ${article.internal_code}` : "Modificar datos del artículo"}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => router.push(`/dashboard/articles/${articleId}`)}>
            Cancelar
          </Button>
          <Button
            type="submit"
            form="article-edit-form"
            disabled={!allowed || updateArticle.isPending || !article}
          >
            {updateArticle.isPending ? "Guardando…" : "Guardar cambios"}
          </Button>
        </div>
      </div>

      {!allowed ? (
        <Alert>
          <AlertDescription>
            Su rol no permite modificar artículos. Solo SuperAdmin y Gerente de Almacén pueden editar el
            maestro de artículos.
          </AlertDescription>
        </Alert>
      ) : null}

      {submitError ? (
        <Alert variant="destructive">
          <AlertDescription>{submitError}</AlertDescription>
        </Alert>
      ) : null}

      {success ? (
        <Alert>
          <AlertDescription>{success}</AlertDescription>
        </Alert>
      ) : null}

      {articleQuery.isLoading ? (
        <div className="space-y-4 rounded-md border p-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Skeleton key={i} className="h-10 w-full" />
          ))}
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
          message={articleQuery.error instanceof Error ? articleQuery.error.message : "Error cargando el artículo"}
          onRetry={() => void articleQuery.refetch()}
        />
      ) : null}

      {article ? (
        <RoleGuard roles={EDIT_ROLES}>
          <div className="rounded-md border p-6">
            <form id="article-edit-form" onSubmit={form.handleSubmit(onSubmit)} className="space-y-4" noValidate>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <label htmlFor="internal_code" className="text-sm font-medium">
                    Código Interno *
                  </label>
                  <Input id="internal_code" type="text" {...form.register("internal_code")} />
                  {form.formState.errors.internal_code ? (
                    <p className="text-xs text-destructive">{form.formState.errors.internal_code.message}</p>
                  ) : null}
                </div>

                <div className="space-y-2">
                  <label htmlFor="ean13" className="text-sm font-medium">
                    EAN-13
                  </label>
                  <Input id="ean13" type="text" inputMode="numeric" {...form.register("ean13")} />
                  {form.formState.errors.ean13 ? (
                    <p className="text-xs text-destructive">{form.formState.errors.ean13.message}</p>
                  ) : null}
                </div>

                <div className="space-y-2">
                  <label htmlFor="supplier_reference" className="text-sm font-medium">
                    Referencia proveedor
                  </label>
                  <Input id="supplier_reference" type="text" {...form.register("supplier_reference")} />
                  {form.formState.errors.supplier_reference ? (
                    <p className="text-xs text-destructive">
                      {form.formState.errors.supplier_reference.message}
                    </p>
                  ) : null}
                </div>

                <div className="space-y-2">
                  <label htmlFor="abc_class" className="text-sm font-medium">
                    Clase ABC
                  </label>
                  <select id="abc_class" className={selectClassName} {...form.register("abc_class")}>
                    <option value="A">A</option>
                    <option value="B">B</option>
                    <option value="C">C</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <label htmlFor="family_id" className="text-sm font-medium">
                    Familia
                  </label>
                  <select id="family_id" className={selectClassName} {...form.register("family_id")}>
                    <option value="">Sin familia</option>
                    {familiesQuery.data?.map((family) => (
                      <option key={family.id} value={family.id}>
                        {family.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-2">
                  <label htmlFor="brand_id" className="text-sm font-medium">
                    Marca
                  </label>
                  <select id="brand_id" className={selectClassName} {...form.register("brand_id")}>
                    <option value="">Sin marca</option>
                    {brandsQuery.data?.map((brand) => (
                      <option key={brand.id} value={brand.id}>
                        {brand.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-2">
                  <label htmlFor="weight_kg" className="text-sm font-medium">
                    Peso (kg)
                  </label>
                  <Input id="weight_kg" type="number" min="0" step="0.001" {...form.register("weight_kg")} />
                  {form.formState.errors.weight_kg ? (
                    <p className="text-xs text-destructive">{form.formState.errors.weight_kg.message}</p>
                  ) : null}
                </div>

                <div className="space-y-2">
                  <label htmlFor="volume_m3" className="text-sm font-medium">
                    Volumen (m³)
                  </label>
                  <Input id="volume_m3" type="number" min="0" step="0.001" {...form.register("volume_m3")} />
                  {form.formState.errors.volume_m3 ? (
                    <p className="text-xs text-destructive">{form.formState.errors.volume_m3.message}</p>
                  ) : null}
                </div>

                <div className="space-y-2">
                  <label htmlFor="length_cm" className="text-sm font-medium">
                    Largo (cm)
                  </label>
                  <Input id="length_cm" type="number" min="0" step="0.1" {...form.register("length_cm")} />
                  {form.formState.errors.length_cm ? (
                    <p className="text-xs text-destructive">{form.formState.errors.length_cm.message}</p>
                  ) : null}
                </div>

                <div className="space-y-2">
                  <label htmlFor="width_cm" className="text-sm font-medium">
                    Ancho (cm)
                  </label>
                  <Input id="width_cm" type="number" min="0" step="0.1" {...form.register("width_cm")} />
                  {form.formState.errors.width_cm ? (
                    <p className="text-xs text-destructive">{form.formState.errors.width_cm.message}</p>
                  ) : null}
                </div>

                <div className="space-y-2">
                  <label htmlFor="height_cm" className="text-sm font-medium">
                    Alto (cm)
                  </label>
                  <Input id="height_cm" type="number" min="0" step="0.1" {...form.register("height_cm")} />
                  {form.formState.errors.height_cm ? (
                    <p className="text-xs text-destructive">{form.formState.errors.height_cm.message}</p>
                  ) : null}
                </div>
              </div>

              <div className="flex flex-col gap-2 border-t border-border pt-4">
                <label className="flex items-center gap-2 text-sm">
                  <input type="checkbox" className="h-4 w-4 rounded border-input" {...form.register("lot_required")} />
                  Requiere control por lote
                </label>
                <label className="flex items-center gap-2 text-sm">
                  <input type="checkbox" className="h-4 w-4 rounded border-input" {...form.register("is_serialized")} />
                  Gestiona números de serie
                </label>
                <label className="flex items-center gap-2 text-sm">
                  <input type="checkbox" className="h-4 w-4 rounded border-input" {...form.register("is_active")} />
                  Artículo activo
                </label>
              </div>
            </form>
          </div>
        </RoleGuard>
      ) : null}
    </div>
  )
}
