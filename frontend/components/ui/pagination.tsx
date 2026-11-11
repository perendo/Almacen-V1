"use client"

import { ChevronLeft, ChevronRight } from "lucide-react"
import { Button } from "@/components/ui/button"

interface DataPaginationProps {
  page: number
  pageSize: number
  itemCount: number
  hasNext: boolean
  onPrevious: () => void
  onNext: () => void
  disabled?: boolean
}

export function DataPagination({
  page,
  pageSize,
  itemCount,
  hasNext,
  onPrevious,
  onNext,
  disabled = false,
}: DataPaginationProps) {
  const from = itemCount === 0 ? 0 : (page - 1) * pageSize + 1
  const to = (page - 1) * pageSize + itemCount

  return (
    <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
      <p className="text-sm text-muted-foreground">
        Mostrando {from}–{to}
      </p>
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={onPrevious}
          disabled={disabled || page <= 1}
          className="gap-1"
        >
          <ChevronLeft className="h-4 w-4" aria-hidden="true" />
          Anterior
        </Button>
        <span className="text-sm text-muted-foreground">Página {page}</span>
        <Button
          variant="outline"
          size="sm"
          onClick={onNext}
          disabled={disabled || !hasNext}
          className="gap-1"
        >
          Siguiente
          <ChevronRight className="h-4 w-4" aria-hidden="true" />
        </Button>
      </div>
    </div>
  )
}
