import { Card, CardContent } from '@/components/ui/card'
import { api } from '@/api/client'
import { useApiData } from '@/hooks/useApiData'
import { useLabels } from '@/lib/labels'

export function KpiCards() {
  const { data, loading, error } = useApiData(() => api.getKpi())
  const labels = useLabels()

  if (loading) {
    return (
      <div className="grid grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i} className="bg-card border-border">
            <CardContent className="p-4">
              <div className="h-4 w-20 bg-muted rounded animate-pulse mb-2" />
              <div className="h-8 w-28 bg-muted rounded animate-pulse" />
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="grid grid-cols-4 gap-4">
        <Card className="bg-card border-border col-span-4">
          <CardContent className="p-4 text-red-400 text-sm">
            {error ?? 'Failed to load KPI data'}
          </CardContent>
        </Card>
      </div>
    )
  }

  const kpis = [
    {
      label: labels.totalAlerts,
      value: data.total_alerts.toLocaleString(),
      accent: 'text-red-500',
    },
    {
      label: labels.peakDay,
      value: data.peak_day.date,
      sub: `${data.peak_day.count.toLocaleString()} ${labels.alerts}`,
      accent: 'text-orange-500',
    },
    {
      label: labels.mostActive,
      value: `${data.most_active_category.name} (${data.most_active_category.percentage.toFixed(0)}%)`,
      accent: 'text-red-400',
    },
    {
      label: labels.longestQuiet,
      value: `${data.longest_quiet_days} ${labels.days}`,
      accent: 'text-emerald-500',
    },
  ]

  return (
    <div className="grid grid-cols-4 gap-4">
      {kpis.map((kpi) => (
        <Card key={kpi.label} className="bg-card border-border">
          <CardContent className="p-4">
            <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">
              {kpi.label}
            </p>
            <p className={`text-2xl font-bold ${kpi.accent}`}>{kpi.value}</p>
            {'sub' in kpi && kpi.sub && (
              <p className="text-xs text-muted-foreground mt-1">{kpi.sub}</p>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
