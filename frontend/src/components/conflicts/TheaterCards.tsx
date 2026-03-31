import { ArrowUp, ArrowDown, Minus } from 'lucide-react'
import { acledApi } from '@/api/acledClient'
import { useAcledData } from '@/hooks/useAcledData'
import { useAcledFilterStore } from '@/store/acledFilters'
import { useLabels } from '@/lib/labels'

const THEATER_CONFIG: Record<string, { border: string; labelKey: 'coreME' | 'maritime' | 'extendedME' | 'globalTerror' }> = {
  core_me: { border: 'border-l-red-500', labelKey: 'coreME' },
  maritime: { border: 'border-l-blue-500', labelKey: 'maritime' },
  extended_me: { border: 'border-l-amber-500', labelKey: 'extendedME' },
  global_terror: { border: 'border-l-purple-500', labelKey: 'globalTerror' },
}

export function TheaterCards() {
  const { data: theaterData, loading: tLoading } = useAcledData(() => acledApi.getAcledByTheater())
  const { data: escalationData, loading: eLoading } = useAcledData(() => acledApi.getAcledEscalation())
  const labels = useLabels()
  const activeTheaters = useAcledFilterStore((s) => s.theaters)

  const loading = tLoading || eLoading

  if (loading) {
    return (
      <div className="grid grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-24 bg-muted rounded-lg animate-pulse" />
        ))}
      </div>
    )
  }

  const theaters = theaterData ?? []
  const escalations = escalationData?.theaters ?? []

  function getEscalation(theater: string) {
    return escalations.find((e) => e.theater === theater)
  }

  function handleClick(theater: string) {
    const store = useAcledFilterStore.getState()
    if (store.theaters.length === 1 && store.theaters[0] === theater) {
      store.setTheaters([])
    } else {
      store.setTheaters([theater])
    }
  }

  return (
    <div className="grid grid-cols-4 gap-4">
      {theaters.map((t) => {
        const config = THEATER_CONFIG[t.theater]
        if (!config) return null
        const esc = getEscalation(t.theater)
        const pct = esc?.change_pct ?? null
        const isActive = activeTheaters.includes(t.theater)
        const isUp = pct !== null && pct > 0
        const isDown = pct !== null && pct < 0

        return (
          <button
            key={t.theater}
            onClick={() => handleClick(t.theater)}
            className={`rounded-lg border border-border border-l-4 ${config.border} bg-card p-4 text-left transition-all hover:bg-muted/50 ${isActive ? 'ring-2 ring-primary' : ''}`}
          >
            <p className="text-sm font-semibold text-foreground mb-2">{labels[config.labelKey]}</p>
            <div className="flex items-baseline justify-between">
              <div>
                <span className="text-lg font-bold text-foreground">{t.count.toLocaleString()}</span>
                <span className="text-xs text-muted-foreground ml-1">{labels.events}</span>
              </div>
              <div className="flex items-center gap-1">
                {isUp && <ArrowUp className="size-3.5 text-red-500" />}
                {isDown && <ArrowDown className="size-3.5 text-emerald-500" />}
                {!isUp && !isDown && <Minus className="size-3.5 text-muted-foreground" />}
                <span className={`text-xs font-bold ${isUp ? 'text-red-500' : isDown ? 'text-emerald-500' : 'text-muted-foreground'}`}>
                  {pct !== null ? `${pct > 0 ? '+' : ''}${pct.toFixed(1)}%` : 'N/A'}
                </span>
              </div>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {t.fatalities.toLocaleString()} {labels.fatalities}
            </p>
          </button>
        )
      })}
    </div>
  )
}
