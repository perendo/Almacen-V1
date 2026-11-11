import type { ReactNode } from "react"
import Link from "next/link"
import { PackageOpen } from "lucide-react"

interface EmptyStateProps {
  title: string
  description?: string
  action?: ReactNode
  actionHref?: string
  actionLabel?: string
}

export function EmptyState({ title, description, action, actionHref, actionLabel }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 rounded-md border border-dashed border-border bg-card px-6 py-12 text-center">
      <PackageOpen className="h-8 w-8 text-muted-foreground" aria-hidden="true" />
      <p className="text-sm font-medium text-foreground">{title}</p>
      {description ? <p className="max-w-md text-sm text-muted-foreground">{description}</p> : null}
      {action}
      {actionHref && actionLabel ? (
        <Link className="text-sm font-medium text-primary underline-offset-4 hover:underline" href={actionHref}>
          {actionLabel}
        </Link>
      ) : null}
    </div>
  )
}
