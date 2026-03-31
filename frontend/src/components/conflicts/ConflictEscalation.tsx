import { ArrowUp, ArrowDown, Minus } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { acledApi } from '@/api/acledClient'
import { useAcledData } from '@/hooks/useAcledData'
import { useLabels } from '@/lib/labels'
import { ChartPanel } from '@/components/charts/ChartPanel'

export function ConflictEscalation() {
  const { data, loading, error } = useAcledData(() => acledApi.getAcledEscalation())
  const labels = useLabels()

  const theaters = data?.theaters ?? []

  const theaterLabel = (key: string): string => {
    if (key === 'core_me') return labels.coreME
    if (key === 'maritime') return labels.maritime
    if (key === 'extended_me') return labels.extendedME
    if (key === 'global_terror') return labels.globalTerror
    return key
  }

  return (
    <ChartPanel title={labels.escalation} loading={loading} error={error}>
      <div className="space-y-3">
        {theaters.map((t) => {
          const pct = t.change_pct
          const isUp = pct !== null && pct > 0
          const isDown = pct !== null && pct < 0
          return (
            <Card key={t.theater} className="bg-card border-border">
              <CardContent className="p-3 flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-foreground">{theaterLabel(t.theater)}</p>
                  <p className="text-xs text-muted-foreground">
                    {t.current_week_count} {labels.events} this week ({t.fatalities_current} {labels.fatalities})
                  </p>
                </div>
                <div className="flex items-center gap-1.5">
                  {isUp && <ArrowUp className="size-4 text-red-500" />}
                  {isDown && <ArrowDown className="size-4 text-emerald-500" />}
                  {!isUp && !isDown && <Minus className="size-4 text-muted-foreground" />}
                  <span className={`text-sm font-bold ${isUp ? 'text-red-500' : isDown ? 'text-emerald-500' : 'text-muted-foreground'}`}>
                    {pct !== null ? `${pct > 0 ? '+' : ''}${pct.toFixed(1)}%` : 'N/A'}
                  </span>
                </div>
              </CardContent>
            </Card>
          )
        })}
        {theaters.length === 0 && (
          <p className="text-sm text-muted-foreground text-center py-4">{labels.noData}</p>
        )}
      </div>
    </ChartPanel>
  )
}
