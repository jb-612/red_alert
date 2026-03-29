import { FileDown, ImageDown } from 'lucide-react'
import type { ReactNode } from 'react'

interface ChartPanelProps {
  title: string
  loading: boolean
  error: string | null
  children: ReactNode
  onExportPng?: () => void
  onExportCsv?: () => void
}

export function ChartPanel({ title, loading, error, children, onExportPng, onExportCsv }: ChartPanelProps) {
  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-foreground">{title}</h2>
        {!loading && !error && (onExportPng || onExportCsv) && (
          <div className="flex gap-1">
            {onExportPng && (
              <button
                onClick={onExportPng}
                className="rounded p-1 text-muted-foreground hover:text-foreground"
                title="Export PNG"
              >
                <ImageDown className="h-3.5 w-3.5" />
              </button>
            )}
            {onExportCsv && (
              <button
                onClick={onExportCsv}
                className="rounded p-1 text-muted-foreground hover:text-foreground"
                title="Export CSV"
              >
                <FileDown className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
        )}
      </div>
      {loading ? (
        <div className="flex items-center justify-center h-[280px] text-muted-foreground">
          <div className="animate-spin h-6 w-6 border-2 border-muted-foreground border-t-transparent rounded-full" />
        </div>
      ) : error ? (
        <div className="flex items-center justify-center h-[280px] text-red-400 text-sm">
          {error}
        </div>
      ) : (
        children
      )}
    </div>
  )
}
