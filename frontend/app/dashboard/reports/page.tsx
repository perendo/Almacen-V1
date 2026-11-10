import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"

export const dynamic = "force-dynamic"

export default function ReportsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Informes y Cuadro de Mando</h1>
        <p className="text-muted-foreground">Valoración, rotación, KPIs y exportación de datos</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Valoración de Existencias</CardTitle>
            <CardDescription>Informe por PMP y FIFO</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground text-sm">Genera informes de valoración contable de existencias.</p>
          </CardContent>
          <CardFooter>
            <Button>Generar informe</Button>
          </CardFooter>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Rotación de Inventario</CardTitle>
            <CardDescription>Coeficiente por artículo y almacén</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground text-sm">Calcula la rotación de inventario por artículo, familia y almacén.</p>
          </CardContent>
          <CardFooter>
            <Button>Generar informe</Button>
          </CardFooter>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>KPIs de Rendimiento</CardTitle>
            <CardDescription>Exactitud, cycle time, OTIF</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground text-sm">Indicadores clave de rendimiento del almacén.</p>
          </CardContent>
          <CardFooter>
            <Button>Ver KPIs</Button>
          </CardFooter>
        </Card>
      </div>

      <div className="rounded-md border p-6">
        <h2 className="text-lg font-semibold mb-4">Exportación de Datos</h2>
        <p className="text-muted-foreground">Descarga informes y tablas en formatos estándar (CSV, Excel, PDF).</p>
        <div className="flex gap-2 mt-4">
          <Button>Exportar CSV</Button>
          <Button variant="outline">Exportar Excel</Button>
          <Button variant="outline">Exportar PDF</Button>
        </div>
      </div>
    </div>
  )
}