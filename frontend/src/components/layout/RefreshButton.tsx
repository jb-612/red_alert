import { useState } from 'react'
import { RefreshCw } from 'lucide-react'
import { refreshAll, type SyncResponse } from '@/api/syncClient'
import { Button } from '@/components/ui/button'

type Status = 'idle' | 'loading' | 'success' | 'error'

function formatNumber(n: number): string {
  return n.toLocaleString('en-US')
}

function statusLabel(status: Status, result: SyncResponse | null, error: string | null): string {
  if (status === 'loading') return 'Refreshing…'
  if (status === 'error') return error ?? 'Refresh failed'
  if (status === 'success' && result) {
    const sourceWord = result.ok_count === 1 ? 'source' : 'sources'
    return `${result.ok_count}/${result.results.length} ${sourceWord} · ${formatNumber(result.total_rows)} rows`
  }
  return 'Refresh data'
}

interface ResultPanelProps {
  result: SyncResponse
}

function ResultPanel({ result }: ResultPanelProps) {
  return (
    <div className="absolute right-0 top-full mt-2 z-50 w-80 rounded-md border border-border bg-popover shadow-lg p-3 text-sm">
      <div className="flex items-center justify-between mb-2 pb-2 border-b border-border">
        <span className="font-semibold text-foreground">Refresh complete</span>
        <span className="text-xs text-muted-foreground font-mono">
          {result.total_elapsed_seconds.toFixed(1)}s
        </span>
      </div>
      <ul className="space-y-1.5">
        {result.results.map((r) => (
          <li key={r.source} className="flex items-start justify-between gap-2">
            <div className="flex items-center gap-2 min-w-0">
              <span
                className={`inline-block h-2 w-2 rounded-full shrink-0 ${
                  r.status === 'ok' ? 'bg-green-500' : 'bg-red-500'
                }`}
              />
              <span className="text-foreground truncate">{r.label}</span>
            </div>
            <div className="text-right text-xs font-mono shrink-0">
              {r.status === 'ok' ? (
                <>
                  <span className="text-foreground">{formatNumber(r.rows_synced)}</span>
                  <span className="text-muted-foreground"> rows · {r.elapsed_seconds.toFixed(1)}s</span>
                </>
              ) : (
                <span className="text-red-400" title={r.error ?? ''}>
                  {r.error?.slice(0, 40) ?? 'error'}
                </span>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}

export function RefreshButton() {
  const [status, setStatus] = useState<Status>('idle')
  const [result, setResult] = useState<SyncResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [showPanel, setShowPanel] = useState(false)

  const handleClick = async () => {
    if (status === 'loading') return
    setStatus('loading')
    setError(null)
    setShowPanel(false)
    try {
      const resp = await refreshAll()
      setResult(resp)
      setStatus(resp.error_count === 0 ? 'success' : 'error')
      setShowPanel(true)
      window.setTimeout(() => setShowPanel(false), 6000)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err)
      setError(msg)
      setStatus('error')
    }
  }

  const icon = (
    <RefreshCw
      className={`size-3.5 ${status === 'loading' ? 'animate-spin' : ''}`}
      aria-hidden
    />
  )

  const statusColor =
    status === 'success'
      ? 'text-green-500'
      : status === 'error'
      ? 'text-red-400'
      : 'text-muted-foreground'

  return (
    <div className="relative">
      <Button
        variant="ghost"
        size="sm"
        onClick={handleClick}
        disabled={status === 'loading'}
        className={`flex items-center gap-2 ${statusColor}`}
        title={statusLabel(status, result, error)}
      >
        {icon}
        <span className="text-xs">{statusLabel(status, result, error)}</span>
      </Button>
      {showPanel && result && <ResultPanel result={result} />}
    </div>
  )
}
