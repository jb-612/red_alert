import { ArrowUp, ArrowDown, Minus } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { acledApi } from '@/api/acledClient'
import { useAcledData } from '@/hooks/useAcledData'
import { useLabels } from '@/lib/labels'

function TrendArrow({ pct }: { pct: number | null }) {
  if (pct === null) return <Minus className="size-4 text-muted-foreground" />
  if (pct > 0) return <ArrowUp className="size-4 text-red-500" />
  if (pct < 0) return <ArrowDown className="size-4 text-emerald-500" />
  return <Minus className="size-4 text-muted-foreground" />
}

function SeverityDot({ trendPct }: { trendPct: number | null }) {
  let color = 'bg-emerald-500'
  if (trendPct !== null && trendPct > 50) color = 'bg-red-500'
  else if (trendPct !== null && trendPct > 0) color = 'bg-amber-500'
  return <span className={`inline-block size-3 rounded-full ${color} animate-pulse`} />
}

export function SituationHeader() {
  const { data, loading } = useAcledData(() => acledApi.getSituation())
  const labels = useLabels()

  if (loading) {
    return (
      <div className="rounded-lg border border-border bg-card p-6">
        <div className="h-6 w-64 bg-muted rounded animate-pulse mb-4" />
        <div className="grid grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-16 bg-muted rounded animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  if (!data) return null

  const trendColor = data.trend_pct !== null && data.trend_pct > 0
    ? 'text-red-500'
    : data.trend_pct !== null && data.trend_pct < 0
      ? 'text-emerald-500'
      : 'text-muted-foreground'

  const stats = [
    {
      label: labels.events,
      value: data.total_events.toLocaleString(),
      sub: (
        <span className={`flex items-center gap-1 text-xs ${trendColor}`}>
          <TrendArrow pct={data.trend_pct} />
          {data.trend_pct !== null ? `${data.trend_pct > 0 ? '+' : ''}${data.trend_pct.toFixed(1)}%` : 'N/A'}
        </span>
      ),
      accent: 'text-red-500',
    },
    {
      label: labels.fatalities,
      value: data.total_fatalities.toLocaleString(),
      sub: <span className="text-xs text-muted-foreground">7d: {data.fatalities_last_7d.toLocaleString()}</span>,
      accent: 'text-orange-500',
    },
    {
      label: labels.countries,
      value: String(data.active_countries),
      sub: null,
      accent: 'text-blue-500',
    },
    {
      label: labels.escalationWarning,
      value: data.top_escalating_theater ?? '--',
      sub: null,
      accent: 'text-purple-500',
    },
  ]

  return (
    <div className="rounded-lg border border-border bg-card p-6">
      <div className="flex items-center gap-3 mb-4">
        <SeverityDot trendPct={data.trend_pct} />
        <h1 className="text-lg font-bold text-foreground tracking-wide">
          {labels.situationRoom} — {labels.conflictDay} {data.conflict_day_number}
        </h1>
      </div>

      <div className="grid grid-cols-4 gap-4">
        {stats.map((s) => (
          <Card key={s.label} className="bg-card border-border">
            <CardContent className="p-4">
              <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">{s.label}</p>
              <p className={`text-2xl font-bold ${s.accent}`}>{s.value}</p>
              {s.sub && <div className="mt-1">{s.sub}</div>}
            </CardContent>
          </Card>
        ))}
      </div>

      {data.last_event_date && (
        <p className="text-xs text-muted-foreground mt-3">
          Last updated: {data.last_event_date}
        </p>
      )}
    </div>
  )
}
