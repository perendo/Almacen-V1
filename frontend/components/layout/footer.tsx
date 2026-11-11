import Link from "next/link"

interface FooterProps {
  className?: string
}

export default function Footer({ className }: FooterProps) {
  const year = 2026

  return (
    <footer
      className={`shrink-0 border-t border-border bg-card px-6 py-4 text-sm text-muted-foreground ${className ?? ""}`}
    >
      <div className="flex flex-col items-center justify-between gap-2 sm:flex-row">
        <p>© {year} WMS. Software distribuido bajo licencia MIT, «tal cual», sin garantías.</p>
        <nav aria-label="Enlaces legales" className="flex flex-wrap items-center gap-4">
          <Link className="underline-offset-4 hover:text-foreground hover:underline" href="/terminos">
            Términos y Condiciones
          </Link>
          <Link className="underline-offset-4 hover:text-foreground hover:underline" href="/privacidad">
            Política de Privacidad
          </Link>
          <Link className="underline-offset-4 hover:text-foreground hover:underline" href="/aviso-legal">
            Aviso Legal
          </Link>
        </nav>
      </div>
    </footer>
  )
}
