"use client"

import { useState } from "react"
import { useAuth } from "@/hooks/useAuth"
import { usePathname } from "next/navigation"
import { Menu, Sun, Moon } from "lucide-react"

export default function Navbar() {
  const { user } = useAuth()
  const pathname = usePathname()
  const [theme, setTheme] = useState("light")

  return (
    <header className="sticky top-0 z-40 flex h-16 items-center gap-4 border-b border-background bg-background/80 px-4 backdrop-blur">
      <button className="md:hidden rounded-md p-2 text-foreground/70 hover:text-foreground hover:bg-accent">
        <Menu className="h-5 w-5" />
      </button>
      <div className="flex-1"></div>
      <button className="rounded-md p-2 text-foreground/70 hover:text-foreground hover:bg-accent" onClick={() => setTheme(theme === "light" ? "dark" : "light")}>
        {theme === "light" ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
      </button>
      <div className="flex items-center gap-2">
        <span className="hidden md:block text-sm text-muted-foreground">{user?.company_id ? `Empresa #${user.company_id}` : ""}</span>
        <span className="hidden md:block text-xs font-medium bg-secondary px-2 py-1 rounded-full text-secondary-foreground">{user?.roles?.join(", ") ?? "-"}</span>
        <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=" alt="user" className="h-8 w-8 rounded-full" />
      </div>
    </header>
  )
}