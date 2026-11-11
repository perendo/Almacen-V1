"use client"

import { useMemo, useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { EmptyState } from "@/components/ui/empty-state"
import { ErrorState } from "@/components/ui/error-state"
import { DataPagination } from "@/components/ui/pagination"
import { useAuth } from "@/hooks/useAuth"
import { useAuditLogs } from "@/hooks/useApi"
import { formatDateTime } from "@/lib/utils"
import type { AuditLog } from "@/types/master-data"

const PAGE_SIZE = 25
const AUDIT_ROLES = ["SuperAdmin", "Auditor"]

type Filters = { entity_type: string; action: string }

function csvEscape(value: string | null | undefined): string {
  const text = value ?? ""
  return `"${text.replace(/"/g, '""')}"`
}

export default function AuditPage() {
  const { hasRole } = useAuth()
  const allowed = hasRole(AUDIT_ROLES)

  const [page, setPage] = useState(1)
  const [draftFilters, setDraftFilters] = useState<Filters>({ entity_type: "", action: "" })
  const [filters, setFilters] = useState<Filters>({ entity_type: "", action: "" })

  const params = useMemo(() => {
    const query: Record<string, string> = {
      skip: String((page - 1) * PAGE_SIZE),
      limit: String(PAGE_SIZE),
    }
    if (filters.entity_type) query.entity_type = filters.entity_type
    if (filters.action) query.action = filters.action
    return query
  }, [page, filters])

  const { data: logs, isLoading, error, refetch, isFetching } = useAuditLogs(params, { enabled: allowed })

  const rows: AuditLog[] = logs ?? []

  function applyFilters(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setPage(1)
    setFilters({
      entity_type: draftFilters.entity_type.trim(),
      action: draftFilters.action.trim(),
    })
  }

  function clearFilters() {
    setDraftFilters({ entity_type: "", action: "" })
    setFilters({ entity_type: "", action: "" })
    setPage(1)
  }

  function exportCsv() {
    const header = ["id", "timestamp", "user_id", "action", "entity_type", "entity_id", "ip", "description"]
    const lines = [
      header.join(","),
      ...rows.map((log) =>
        [
          String(log.id),
          csvEscape(log.timestamp),
          csvEscape(log.user_id !== null ? String(log.user_id) : ""),
          csvEscape(log.action),
          csvEscape(log.entity_type),
          csvEscape(log.entity_id !== null ? String(log.entity_id) : ""),
          csvEscape(log.ip),
          csvEscape(log.description),
        ].join(",")
      ),
    ]
    const blob = new Blob([`\uFEFF${lines.join("\r\n")}`], { type: "text/csv;charset=utf-8" })
    const url = URL.createObjectURL(blob)
    const link = document.createElement("a")
    link.href = url
    link.download = `auditoria-${new Date().toISOString().slice(0, 10)}.csv`
    link.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Auditoría</h1>
          <p className="text-muted-foreground">Logs de auditoría y trazabilidad de acciones</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => void refetch()} disabled={!allowed || isFetching}>
            {isFetching ? "Actualizando…" : "Actualizar"}
          </Button>
          <Button onClick={exportCsv} disabled={!allowed || rows.length === 0}>
            Exportar página (CSV)
          </Button>
        </div>
      </div>

      {!allowed ? (
        <Alert>
          <AlertDescription>
            Acceso restringido. Los logs de auditoría solo están disponibles para los roles SuperAdmin y Auditor.
          </AlertDescription>
        </Alert>
      ) : (
        <>
          <form onSubmit={applyFilters} className="flex flex-col gap-2 sm:flex-row sm:items-end">
            <div className="space-y-1">
              <label htmlFor="audit-entity" className="text-xs font-medium text-muted-foreground">
                Entidad
              </label>
              <Input
                id="audit-entity"
                placeholder="Ej: Article, Stock"
                value={draftFilters.entity_type}
                onChange={(event) =>
                  setDraftFilters((current) => ({ ...current, entity_type: event.target.value }))
                }
                className="sm:w-48"
              />
            </div>
            <div className="space-y-1">
              <label htmlFor="audit-action" className="text-xs font-medium text-muted-foreground">
                Acción
              </label>
              <Input
                id="audit-action"
                placeholder="Ej: CREATE"
                value={draftFilters.action}
                onChange={(event) =>
                  setDraftFilters((current) => ({ ...current, action: event.target.value }))
                }
                className="sm:w-48"
              />
            </div>
            <Button type="submit" variant="secondary" disabled={isFetching}>
              Filtrar
            </Button>
            <Button type="button" variant="ghost" onClick={clearFilters} disabled={isFetching}>
              Limpiar
            </Button>
          </form>

          {isLoading ? (
            <div className="space-y-2 rounded-md border p-4">
              {[1, 2, 3, 4, 5].map((i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : null}

          {error && !isLoading ? (
            <ErrorState
              message={error instanceof Error ? error.message : "Error cargando los logs de auditoría"}
              onRetry={() => void refetch()}
            />
          ) : null}

          {!isLoading && !error ? (
            rows.length === 0 ? (
              <EmptyState
                title="No hay registros de auditoría"
                description="Las acciones sobre el sistema se registrarán aquí automáticamente."
              />
            ) : (
              <>
                <div className="rounded-md border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Fecha/Hora</TableHead>
                        <TableHead>Usuario</TableHead>
                        <TableHead>Acción</TableHead>
                        <TableHead>Entidad</TableHead>
                        <TableHead>ID Entidad</TableHead>
                        <TableHead>IP</TableHead>
                        <TableHead>Descripción</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {rows.map((log) => (
                        <TableRow key={log.id}>
                          <TableCell className="font-medium">{formatDateTime(log.timestamp)}</TableCell>
                          <TableCell>{log.user_id !== null ? `Usuario #${log.user_id}` : "Sistema"}</TableCell>
                          <TableCell>
                            <Badge variant="outline">{log.action}</Badge>
                          </TableCell>
                          <TableCell>{log.entity_type}</TableCell>
                          <TableCell>{log.entity_id ?? "—"}</TableCell>
                          <TableCell>{log.ip || "—"}</TableCell>
                          <TableCell className="max-w-xs truncate" title={log.description ?? undefined}>
                            {log.description || "—"}
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
        </>
      )}
    </div>
  )
}
