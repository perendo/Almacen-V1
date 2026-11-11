"use client"

import { useMemo, useState } from "react"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert as AlertBanner, AlertDescription } from "@/components/ui/alert"
import { EmptyState } from "@/components/ui/empty-state"
import { ErrorState } from "@/components/ui/error-state"
import { DataPagination } from "@/components/ui/pagination"
import { RoleGuard } from "@/components/role-guard"
import { useAlerts, useResolveAlert } from "@/hooks/useApi"
import { useArticles } from "@/hooks/useArticles"
import { formatDateTime } from "@/lib/utils"
import type { Alert } from "@/types/master-data"

const PAGE_SIZE = 20
const CAN_RESOLVE = ["SuperAdmin", "Gerente de Almacén"]

function severityVariant(severity: string): "default" | "secondary" | "destructive" | "outline" {
  if (severity === "critical" || severity === "high") return "destructive"
  if (severity === "medium") return "secondary"
  return "outline"
}

function alertTypeLabel(type: string): string {
  switch (type) {
    case "expiry":
      return "Caducidad"
    case "min_stock":
      return "Stock mínimo"
    case "max_stock":
      return "Stock máximo"
    case "dead_stock":
      return "Sin movimiento"
    default:
      return type
  }
}

export default function AlertsPage() {
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState("open")
  const [actionError, setActionError] = useState<string | null>(null)
  const [resolvingId, setResolvingId] = useState<number | null>(null)

  const params = useMemo(
    () => ({
      skip: String((page - 1) * PAGE_SIZE),
      limit: String(PAGE_SIZE),
      ...(statusFilter ? { status: statusFilter } : {}),
    }),
    [page, statusFilter]
  )

  const { data: alerts, isLoading, error, refetch, isFetching } = useAlerts(params)
  const { data: articles } = useArticles({ limit: "1000" })
  const resolveAlert = useResolveAlert()

  const articleCodes = useMemo(() => {
    const map = new Map<number, string>()
    articles?.forEach((article) => map.set(article.id, article.internal_code))
    return map
  }, [articles])

  const rows: Alert[] = alerts ?? []

  async function handleResolve(alert: Alert) {
    setActionError(null)
    setResolvingId(alert.id)
    try {
      await resolveAlert.mutateAsync({ id: alert.id })
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "No se pudo resolver la alerta")
    } finally {
      setResolvingId(null)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Alertas</h1>
          <p className="text-muted-foreground">Stock mínimo, caducidad y productos sin movimiento</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <label htmlFor="alert-status" className="text-sm text-muted-foreground">
            Estado
          </label>
          <select
            id="alert-status"
            className="h-10 rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            value={statusFilter}
            onChange={(event) => {
              setStatusFilter(event.target.value)
              setPage(1)
            }}
          >
            <option value="">Todas</option>
            <option value="open">Abiertas</option>
            <option value="acknowledged">Reconocidas</option>
            <option value="resolved">Resueltas</option>
          </select>
          <Button variant="outline" onClick={() => void refetch()} disabled={isFetching}>
            {isFetching ? "Actualizando…" : "Actualizar"}
          </Button>
        </div>
      </div>

      {actionError ? (
        <AlertBanner variant="destructive">
          <AlertDescription>{actionError}</AlertDescription>
        </AlertBanner>
      ) : null}

      {isLoading ? (
        <div className="space-y-2 rounded-md border p-4">
          {[1, 2, 3, 4, 5].map((i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      ) : null}

      {error && !isLoading ? (
        <ErrorState
          message={error instanceof Error ? error.message : "Error cargando alertas"}
          onRetry={() => void refetch()}
        />
      ) : null}

      {!isLoading && !error ? (
        rows.length === 0 ? (
          <EmptyState
            title="No hay alertas para este filtro"
            description="Cuando el sistema detecte stock mínimo, caducidades próximas o productos sin movimiento aparecerán aquí."
          />
        ) : (
          <>
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Tipo</TableHead>
                    <TableHead>Artículo</TableHead>
                    <TableHead>Severidad</TableHead>
                    <TableHead>Estado</TableHead>
                    <TableHead>Mensaje</TableHead>
                    <TableHead>Creada</TableHead>
                    <TableHead className="text-right">Acciones</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {rows.map((alert) => (
                    <TableRow key={alert.id}>
                      <TableCell>
                        <Badge variant="outline">{alertTypeLabel(alert.alert_type)}</Badge>
                      </TableCell>
                      <TableCell className="font-medium">
                        {alert.article_id
                          ? articleCodes.get(alert.article_id) ?? `Artículo #${alert.article_id}`
                          : "—"}
                      </TableCell>
                      <TableCell>
                        <Badge variant={severityVariant(alert.severity)}>{alert.severity}</Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={alert.status === "resolved" ? "secondary" : "default"}>
                          {alert.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="max-w-xs truncate" title={alert.message ?? undefined}>
                        {alert.message || "—"}
                      </TableCell>
                      <TableCell>{formatDateTime(alert.created_at)}</TableCell>
                      <TableCell className="text-right">
                        {alert.status === "resolved" ? (
                          <span className="text-xs text-muted-foreground">
                            {alert.resolved_at ? formatDateTime(alert.resolved_at) : "Resuelta"}
                          </span>
                        ) : (
                          <RoleGuard
                            roles={CAN_RESOLVE}
                            fallback={<span className="text-xs text-muted-foreground">Solo lectura</span>}
                          >
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => void handleResolve(alert)}
                              disabled={resolvingId === alert.id}
                            >
                              {resolvingId === alert.id ? "Resolviendo…" : "Resolver"}
                            </Button>
                          </RoleGuard>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            <DataPagination
              page={page}
              pageSize={PAGE_SIZE}
              itemCount={rows.length}
              hasNext={rows.length === PAGE_SIZE}
              onPrevious={() => setPage((current) => Math.max(1, current - 1))}
              onNext={() => setPage((current) => current + 1)}
              disabled={isFetching}
            />
          </>
        )
      ) : null}
    </div>
  )
}
