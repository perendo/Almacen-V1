import Link from "next/link"
import Footer from "@/components/layout/footer"

export interface LegalSection {
  title: string
  paragraphs?: string[]
  bullets?: string[]
}

interface LegalPageProps {
  title: string
  subtitle: string
  updatedAt: string
  remoteSummary?: {
    contenido: string
    version: string
  } | null
  sections: LegalSection[]
}

export default function LegalPageLayout({
  title,
  subtitle,
  updatedAt,
  remoteSummary,
  sections,
}: LegalPageProps) {
  return (
    <div className="flex min-h-screen flex-col bg-background">
      <header className="border-b border-border bg-card">
        <div className="mx-auto flex w-full max-w-3xl flex-col gap-2 px-6 py-6 sm:flex-row sm:items-center sm:justify-between">
          <Link href="/" className="text-lg font-semibold text-foreground underline-offset-4 hover:underline">
            WMS
          </Link>
          <nav className="flex items-center gap-4 text-sm">
            <Link className="text-muted-foreground underline-offset-4 hover:text-foreground hover:underline" href="/">
              Inicio
            </Link>
            <Link
              className="text-muted-foreground underline-offset-4 hover:text-foreground hover:underline"
              href="/login"
            >
              Iniciar sesión
            </Link>
          </nav>
        </div>
      </header>

      <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-10">
        <h1 className="text-3xl font-semibold text-foreground">{title}</h1>
        <p className="mt-2 text-muted-foreground">{subtitle}</p>
        <p className="mt-1 text-xs text-muted-foreground">Última actualización: {updatedAt}</p>

        {remoteSummary ? (
          <div className="mt-6 rounded-lg border border-border bg-card p-4">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Documento publicado por la API (versión {remoteSummary.version})
            </p>
            <p className="mt-2 text-sm text-foreground">{remoteSummary.contenido}</p>
          </div>
        ) : null}

        <div className="mt-8 space-y-8">
          {sections.map((section) => (
            <section key={section.title} className="space-y-3">
              <h2 className="text-xl font-semibold text-foreground">{section.title}</h2>
              {section.paragraphs?.map((paragraph) => (
                <p key={paragraph} className="text-sm leading-relaxed text-foreground/90">
                  {paragraph}
                </p>
              ))}
              {section.bullets?.length ? (
                <ul className="list-disc space-y-2 pl-6 text-sm leading-relaxed text-foreground/90">
                  {section.bullets.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              ) : null}
            </section>
          ))}
        </div>
      </main>

      <Footer />
    </div>
  )
}
