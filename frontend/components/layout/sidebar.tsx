"use client"

import Link from "next/link"
import { useAuth } from "@/hooks/useAuth"
import { useRouter } from "next/navigation"
import { LogOut, LayoutDashboard, Box, Truck, Barcode, AlertTriangle, Shield, Users, ClipboardList, Building2, Warehouse, ShieldCheck, List, FileText, Package, RefreshCw, AlertCircle } from "lucide-react"

const NAV_ITEMS = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Empresas", href: "/dashboard/companies", icon: Building2 },
  { name: "Centros", href: "/dashboard/centers", icon: Building2 },
  { name: "Almacenes", href: "/dashboard/warehouses", icon: Warehouse },
  { name: "Zonas", href: "/dashboard/zones", icon: Package },
  { name: "Pasillos", href: "/dashboard/aisles", icon: List },
  { name: "Estanterías", href: "/dashboard/shelves", icon: List },
  { name: "Bins", href: "/dashboard/bins", icon: Package },
  { name: "Artículos", href: "/dashboard/articles", icon: Box },
  { name: "Familias", href: "/dashboard/article-families", icon: Box },
  { name: "Marcas", href: "/dashboard/article-brands", icon: Box },
  { name: "UOMs", href: "/dashboard/uoms", icon: Box },
  { name: "Stock", href: "/dashboard/stock", icon: Barcode },
  { name: "Movimientos", href: "/dashboard/movements", icon: Truck },
  { name: "Lotes", href: "/dashboard/lots", icon: ClipboardList },
  { name: "Series", href: "/dashboard/serials", icon: Package },
  { name: "Inventarios", href: "/dashboard/inventory", icon: RefreshCw },
  { name: "Ajustes", href: "/dashboard/adjustments", icon: AlertCircle },
  { name: "Alertas", href: "/dashboard/alerts", icon: AlertTriangle },
  { name: "Informes", href: "/dashboard/reports", icon: FileText },
  { name: "Auditoría", href: "/dashboard/audit", icon: ShieldCheck },
  { name: "Usuarios", href: "/dashboard/users", icon: Users },
  { name: "Roles", href: "/dashboard/roles", icon: ShieldCheck },
]

export default function Sidebar() {
  const { user, logout } = useAuth()
  const router = useRouter()

  return (
    <aside className="flex h-screen w-64 shrink-0 flex-col bg-card border-r border-border">
      <div className="flex-1 overflow-y-auto p-4">
        <Link href="/" className="flex items-center gap-2 mb-6">
          <Box className="h-6 w-6 text-primary" />
          <span className="font-semibold text-foreground">WMS</span>
        </Link>
        <nav className="space-y-1">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon
            return (
              <Link
                key={item.name}
                href={item.href}
                className="flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md transition-colors hover:bg-accent hover:text-accent-foreground"
              >
                <Icon className="h-4 w-4" />
                {item.name}
              </Link>
            )
          })}
        </nav>
      </div>
      <div className="p-4 border-t border-border">
        <div className="flex items-center gap-3 px-3 py-2">
          <div className="flex-1">
            <p className="text-sm font-medium text-foreground">{user?.full_name}</p>
            <p className="text-xs text-muted-foreground">{user?.email}</p>
          </div>
          <button
            onClick={() => {
              logout()
              router.push("/login")
            }}
            className="text-xs text-destructive hover:text-destructive/90 flex items-center gap-1"
          >
            <LogOut className="h-3 w-3" /> Cerrar sesión
          </button>
        </div>
      </div>
    </aside>
  )
}