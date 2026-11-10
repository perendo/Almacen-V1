export const dynamic = "force-dynamic"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription } from "@/components/ui/alert"

export default function DashboardPage() {
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
            <Badge variant="outline">1,240</Badge>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">85%</div>
            <p className="text-xs text-muted-foreground">vs mes anterior</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Alertas Activas</CardTitle>
            <Badge variant="destructive">12</Badge>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-destructive">3 críticas</div>
            <p className="text-xs text-muted-foreground">requieren atención inmediata</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pedidos Pendientes</CardTitle>
            <Badge variant="secondary">24</Badge>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">18 procesados</div>
            <p className="text-xs text-muted-foreground">6 en cola de picking</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Exactitud Inventario</CardTitle>
            <Badge variant="default">98.4%</Badge>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">±0.5%</div>
            <p className="text-xs text-muted-foreground">desviación vs conteo físico</p>
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
              <div className="flex items-center gap-3 p-3 border rounded-lg">
                <AlertVariant type="warning" />
                <div className="flex-1">
                  <p className="text-sm font-medium">Lote LOT-2024-001</p>
                  <p className="text-xs text-muted-foreground">Caduca en 7 días • Artículo: ELEC-001</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 border rounded-lg">
                <AlertVariant type="critical" />
                <div className="flex-1">
                  <p className="text-sm font-medium">Stock mínimo alcanzado</p>
                  <p className="text-xs text-muted-foreground">Artículo: ALIM-005 • Warehouse: WH001</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 border rounded-lg">
                <AlertVariant type="info" />
                <div className="flex-1">
                  <p className="text-sm font-medium">Reabastecimiento sugerido</p>
                  <p className="text-xs text-muted-foreground">25 unidades de FERR-012</p>
                </div>
              </div>
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
              <div className="flex items-center justify-between p-3 border rounded-lg">
                <div>
                  <p className="text-sm font-medium">Entrada de stock</p>
                  <p className="text-xs text-muted-foreground">PO-2024-150 • 2h ago</p>
                </div>
                <Badge variant="default">+150 unid.</Badge>
              </div>
              <div className="flex items-center justify-between p-3 border rounded-lg">
                <div>
                  <p className="text-sm font-medium">Salida de stock</p>
                  <p className="text-xs text-muted-foreground">SO-2024-089 • 4h ago</p>
                </div>
                <Badge variant="destructive">-85 unid.</Badge>
              </div>
              <div className="flex items-center justify-between p-3 border rounded-lg">
                <div>
                  <p className="text-sm font-medium">Traspaso interno</p>
                  <p className="text-xs text-muted-foreground">WH001 → WH002 • 6h ago</p>
                </div>
                <Badge variant="secondary">40 unid.</Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function AlertVariant({ type }: { type: "warning" | "critical" | "info" }) {
  const variants = {
    warning: "bg-amber-500/10 text-amber-600",
    critical: "bg-red-500/10 text-red-600",
    info: "bg-blue-500/10 text-blue-600",
  }
  return <div className={`w-8 h-8 rounded-full flex items-center justify-center ${variants[type]}`}>
    {type === "warning" && "⚠"}
    {type === "critical" && "●"}
    {type === "info" && "ℹ"}
  </div>
}