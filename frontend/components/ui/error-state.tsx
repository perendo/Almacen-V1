"use client"

import { AlertCircle, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"

interface ErrorStateProps {
  title?: string
  message?: string
  onRetry?: () => void
}

export function ErrorState({
  title = "No se pudieron cargar los datos",
  message = "Compruebe su conexión con la API e inténtelo de nuevo.",
  onRetry,
}: ErrorStateProps) {
  return (
    <div role="alert" className="rounded-lg border border-destructive/40 bg-destructive/10 p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start">
        <AlertCircle className="h-5 w-5 shrink-0 text-destructive" aria-hidden="true" />
        <div className="flex-1">
          <p className="text-sm font-medium text-foreground">{title}</p>
          <p className="mt-1 text-sm text-muted-foreground">{message}</p>
        </div>
        {onRetry ? (
          <Button variant="outline" size="sm" onClick={onRetry} className="gap-2">
            <RefreshCw className="h-4 w-4" aria-hidden="true" />
            Reintentar
          </Button>
        ) : null}
      </div>
    </div>
  )
}
