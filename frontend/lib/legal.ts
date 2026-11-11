export interface LegalDocument {
  titulo: string
  contenido: string
  version: string
}

export type LegalSlug = "terminos" | "privacidad" | "aviso-legal"

/**
 * URL base del backend sin el prefijo /api/v1: los endpoints legales
 * (`/terminos`, `/privacidad`, `/aviso-legal`) cuelgan de la raíz.
 */
export function legalApiBase(): string {
  const explicit = process.env.API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
  return explicit.replace(/\/api\/v1\/?$/, "").replace(/\/$/, "")
}

/**
 * Intenta obtener el documento legal publicado por la API. Si la API no
 * responde (build aislado, backend caído, etc.) devuelve null y la página
 * utiliza su contenido local de respaldo.
 */
export async function fetchLegalDocument(slug: LegalSlug): Promise<LegalDocument | null> {
  const url = `${legalApiBase()}/${slug}`

  try {
    const response = await fetch(url, {
      cache: "no-store",
      signal: AbortSignal.timeout(3000),
      headers: { Accept: "application/json" },
    })

    if (!response.ok) return null

    const data: unknown = await response.json()
    if (!data || typeof data !== "object") return null

    const record = data as Record<string, unknown>
    if (typeof record.contenido !== "string") return null

    return {
      titulo: typeof record.titulo === "string" ? record.titulo : slug,
      contenido: record.contenido,
      version: typeof record.version === "string" ? record.version : "—",
    }
  } catch {
    return null
  }
}
