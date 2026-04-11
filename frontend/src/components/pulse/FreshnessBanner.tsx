import type { ConflictPulseResponse } from '@/api/acledPulseClient'

interface Props {
  pulse: ConflictPulseResponse
}

function formatNumber(n: number): string {
  return n.toLocaleString('en-US')
}

function formatExposureMillions(n: number): string {
  if (n >= 1_000_000_000) return `${(n / 1_000_000_000).toFixed(1)}B`
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`
  return formatNumber(n)
}

function daysAgo(dateStr: string | null): string {
  if (!dateStr) return '—'
  const then = new Date(dateStr).getTime()
  const now = Date.now()
  const days = Math.round((now - then) / 86_400_000)
  if (days <= 0) return 'today'
  if (days === 1) return 'yesterday'
  return `${days} days ago`
}

export function FreshnessBanner({ pulse }: Props) {
  const window =
    pulse.window_start && pulse.window_end
      ? `${pulse.window_start} → ${pulse.window_end}`
      : '—'

  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h2 className="text-base font-semibold text-foreground">Global Conflict Pulse</h2>
          <p className="text-xs text-muted-foreground">
            Source: ACLED Explorer aggregates · window {window}
          </p>
        </div>
        <div className="text-right">
          <div className="text-xs text-muted-foreground">Last updated</div>
          <div className="text-sm font-mono text-foreground">
            {pulse.latest_update ?? '—'}
          </div>
          <div className="text-xs text-muted-foreground">{daysAgo(pulse.latest_update)}</div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div className="rounded-md bg-muted/40 p-3">
          <div className="text-xs text-muted-foreground">Events</div>
          <div className="text-2xl font-mono font-semibold text-foreground">
            {formatNumber(pulse.total_events)}
          </div>
        </div>
        <div className="rounded-md bg-muted/40 p-3">
          <div className="text-xs text-muted-foreground">Fatalities</div>
          <div className="text-2xl font-mono font-semibold text-red-400">
            {formatNumber(pulse.total_fatalities)}
          </div>
        </div>
        <div className="rounded-md bg-muted/40 p-3">
          <div className="text-xs text-muted-foreground">Population exposure</div>
          <div className="text-2xl font-mono font-semibold text-amber-400">
            {formatExposureMillions(pulse.total_exposure)}
          </div>
        </div>
      </div>
    </div>
  )
}
