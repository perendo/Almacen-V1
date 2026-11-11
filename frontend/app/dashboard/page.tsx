"use client"

export const dynamic = "force-dynamic"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { useStock } from "@/hooks/useArticles"
import { useAlerts } from "@/hooks/useApi"
import type { StockOut } from "@/types/stock"
import type { Alert as AlertType } from "@/types/master-data"

export default function DashboardPage() {
  const { data: stock, isLoading: stockLoading } = useStock()
  const { data: alerts, isLoading: alertsLoading } = useAlerts()

  const totalStock = stockLoading ? 0 : (stock as StockOut[] | undefined)?.reduce((acc, item) => acc + item.quantity, 0) ?? 0
  const activeAlerts = alertsLoading ? 0 : (alerts as AlertType[] | undefined)?.filter((a) => a.status === "open").length ?? 0

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Dashboard</h1>
          <p className="text-muted-foreground">Resumen de operaciones del almacén</p>
        </div>
        <Button variant="outline">Exportar informe</Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Stock Total</CardTitle>
            <Badge variant="outline">{totalStock}</Badge>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalStock}</div>
            <p className="text-xs text-muted-foreground">unidades en almacén</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Alertas Activas</CardTitle>
            <Badge variant="destructive">{activeAlerts}</Badge>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-destructive">
              {activeAlerts} críticas
            </div>
            <p className="text-xs text-muted-foreground">requieren atención inmediata</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pedidos Pendientes</CardTitle>
            <Badge variant="secondary">—</Badge>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">—</div>
            <p className="text-xs text-muted-foreground">sin datos de pedidos</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Exactitud Inventario</CardTitle>
            <Badge variant="default">—</Badge>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">—</div>
            <p className="text-xs text-muted-foreground">sin conteo físico reciente</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Alertas Recientes</CardTitle>
            <CardDescription>Lotes próximos a caducar y stock mínimo</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {alertsLoading ? (
                <div className="h-32 flex items-center justify-center">
                  <Skeleton className="h-full w-full" />
                </div>
              ) : (alerts as AlertType[] | undefined)?.length ? (
                (alerts as AlertType[]).slice(0, 3).map((alert) => (
                  <div key={alert.id} className="flex items-center gap-3 p-3 border rounded-lg">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      alert.severity === "critical" ? "bg-red-500/10 text-red-600" :
                      alert.severity === "high" ? "bg-amber-500/10 text-amber-600" :
                      "bg-blue-500/10 text-blue-600"
                    }`}>
                      {alert.severity === "critical" ? "●" : alert.severity === "high" ? "⚠" : "ℹ"}
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium">{alert.message || "Alerta sin mensaje"}</p>
                      <p className="text-xs text-muted-foreground">
                        {alert.alert_type} • {alert.severity}
                      </p>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">No hay alertas activas</p>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Movimientos Recientes</CardTitle>
            <CardDescription>Últimas entradas y salidas de stock</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {stockLoading ? (
                <div className="h-32 flex items-center justify-center">
                  <Skeleton className="h-full w-full" />
                </div>
              ) : (stock as StockOut[] | undefined)?.length ? (
                (stock as StockOut[]).slice(0, 3).map((item) => (
                  <div key={item.id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div>
                      <p className="text-sm font-medium">Movimiento de stock</p>
                      <p className="text-xs text-muted-foreground">
                        Artículo: {item.article_id} • Ubicación: {item.warehouse_id}
                      </p>
                    </div>
                    <Badge variant="default">{item.quantity} unid.</Badge>
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">No hay movimientos registrados</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function Skeleton({ className }: { className?: string }) {
  return <div className={`animate-pulse bg-muted ${className ?? ""}`} />
}
