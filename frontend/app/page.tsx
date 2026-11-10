import Link from "next/link"

export default function Page() {
  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-4xl mx-auto">
        <div className="card p-6 mb-6">
          <h1 className="text-2xl font-semibold mb-2">WMS - Gestión de Almacén e Inventario</h1>
          <p className="text-muted-foreground">
            Sistema de gestión de almacén e inventario con multitenencia, trazabilidad completa y control de inventario.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link href="/dashboard" className="card p-4 hover:border-primary transition-colors">
            <h3 className="font-semibold">Dashboard</h3>
            <p className="text-sm text-muted-foreground">Vista general con KPIs y alertas</p>
          </Link>
          <Link href="/dashboard/articles" className="card p-4 hover:border-primary transition-colors">
            <h3 className="font-semibold">Artículos</h3>
            <p className="text-sm text-muted-foreground">Maestros de artículos y existencias</p>
          </Link>
          <Link href="/dashboard/stock" className="card p-4 hover:border-primary transition-colors">
            <h3 className="font-semibold">Stock</h3>
            <p className="text-sm text-muted-foreground">Gestión de inventario por ubicación</p>
          </Link>
        </div>
      </div>
    </div>
  )
}