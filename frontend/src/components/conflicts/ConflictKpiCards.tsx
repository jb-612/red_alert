import { Card, CardContent } from '@/components/ui/card'
import { acledApi } from '@/api/acledClient'
import { useAcledData } from '@/hooks/useAcledData'
import { useLabels } from '@/lib/labels'

export function ConflictKpiCards() {
  const { data: theaterData, loading: tLoading } = useAcledData(() => acledApi.getAcledByTheater())
  const { data: countryData, loading: cLoading } = useAcledData(() => acledApi.getAcledByCountry())
  const labels = useLabels()

  const loading = tLoading || cLoading

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

  const theaters = theaterData ?? []
  const countries = countryData ?? []

  const totalEvents = theaters.reduce((sum, t) => sum + t.count, 0)
  const totalFatalities = theaters.reduce((sum, t) => sum + t.fatalities, 0)
  const activeCountries = countries.length
  const activeTheaters = theaters.length

  const kpis = [
    {
      label: labels.events,
      value: totalEvents.toLocaleString(),
      accent: 'text-red-500',
    },
    {
      label: labels.fatalities,
      value: totalFatalities.toLocaleString(),
      accent: 'text-orange-500',
    },
    {
      label: labels.countries,
      value: String(activeCountries),
      accent: 'text-blue-500',
    },
    {
      label: labels.theaters,
      value: String(activeTheaters),
      accent: 'text-purple-500',
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
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
