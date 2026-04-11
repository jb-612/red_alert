import type { PulseTheater } from '@/api/acledPulseClient'

interface Props {
  rollup: PulseTheater[]
}

const THEATER_LABELS: Record<string, string> = {
  core_me: 'Core Middle East',
  extended_me: 'Extended Middle East',
  maritime: 'Maritime',
  global_terror: 'Global terror / Western',
  other: 'Rest of world',
}

const THEATER_ACCENT: Record<string, string> = {
  core_me: 'border-red-500/40 bg-red-500/5',
  extended_me: 'border-amber-500/40 bg-amber-500/5',
  maritime: 'border-cyan-500/40 bg-cyan-500/5',
  global_terror: 'border-purple-500/40 bg-purple-500/5',
  other: 'border-slate-500/40 bg-slate-500/5',
}

function format(n: number): string {
  return n.toLocaleString('en-US')
}

function formatCompact(n: number): string {
  if (n >= 1_000_000_000) return `${(n / 1_000_000_000).toFixed(1)}B`
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`
  return format(n)
}

export function TheaterRollup({ rollup }: Props) {
  const totalEvents = rollup.reduce((sum, t) => sum + t.events, 0)

  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <h3 className="text-sm font-semibold text-foreground mb-3">Theater rollup</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-3">
        {rollup.map((t) => {
          const accent = THEATER_ACCENT[t.theater] ?? THEATER_ACCENT.other
          const label = THEATER_LABELS[t.theater] ?? t.theater
          const share = totalEvents > 0 ? (t.events / totalEvents) * 100 : 0
          return (
            <div key={t.theater} className={`rounded-md border ${accent} p-3`}>
              <div className="text-xs text-muted-foreground mb-1">{label}</div>
              <div className="text-lg font-mono font-semibold text-foreground">
                {format(t.events)}
              </div>
              <div className="text-[11px] text-muted-foreground mt-1">
                {t.countries} countries · {share.toFixed(1)}%
              </div>
              <div className="flex justify-between mt-2 text-[11px]">
                <span className="text-red-400 font-mono">{format(t.fatalities)} fat</span>
                <span className="text-amber-400 font-mono">{formatCompact(t.exposure)} exp</span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
