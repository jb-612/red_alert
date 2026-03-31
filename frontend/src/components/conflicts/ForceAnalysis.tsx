import { useState, useCallback } from 'react'
import { acledApi } from '@/api/acledClient'
import type { AcledTopActorEntry, AcledActorProfile } from '@/api/acledClient'
import { useAcledData } from '@/hooks/useAcledData'
import { useLabels } from '@/lib/labels'
import { ChartPanel } from '@/components/charts/ChartPanel'

type SortKey = 'total_events' | 'total_fatalities' | 'lethality'

const THEATER_COLORS: Record<string, string> = {
  core_me: 'bg-red-500/20 text-red-400',
  maritime: 'bg-blue-500/20 text-blue-400',
  extended_me: 'bg-amber-500/20 text-amber-400',
  global_terror: 'bg-purple-500/20 text-purple-400',
}

export function ForceAnalysis() {
  const { data, loading, error } = useAcledData(() => acledApi.getTopActors())
  const labels = useLabels()
  const [sortKey, setSortKey] = useState<SortKey>('total_events')
  const [sortAsc, setSortAsc] = useState(false)
  const [selectedActor, setSelectedActor] = useState<string | null>(null)
  const [profile, setProfile] = useState<AcledActorProfile | null>(null)
  const [profileLoading, setProfileLoading] = useState(false)

  const actors = data?.actors ?? []

  const sorted = [...actors].sort((a, b) => {
    const diff = a[sortKey] - b[sortKey]
    return sortAsc ? diff : -diff
  })

  function handleSort(key: SortKey) {
    if (sortKey === key) {
      setSortAsc(!sortAsc)
    } else {
      setSortKey(key)
      setSortAsc(false)
    }
  }

  const handleSelectActor = useCallback((actor: AcledTopActorEntry) => {
    if (selectedActor === actor.actor) {
      setSelectedActor(null)
      setProfile(null)
      return
    }
    setSelectedActor(actor.actor)
    setProfileLoading(true)
    acledApi.getAcledActorProfile(actor.actor)
      .then((result) => {
        setProfile(result)
        setProfileLoading(false)
      })
      .catch(() => {
        setProfileLoading(false)
      })
  }, [selectedActor])

  function sortIndicator(key: SortKey) {
    if (sortKey !== key) return ''
    return sortAsc ? ' \u2191' : ' \u2193'
  }

  return (
    <ChartPanel title={labels.forceAnalysis} loading={loading} error={error}>
      <div className="grid grid-cols-2 gap-6">
        {/* Left: Sortable table */}
        <div className="overflow-auto max-h-[400px]">
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-card">
              <tr className="border-b border-border text-left">
                <th className="py-2 px-2 text-xs text-muted-foreground font-semibold">{labels.actors}</th>
                <th
                  className="py-2 px-2 text-xs text-muted-foreground font-semibold cursor-pointer hover:text-foreground"
                  onClick={() => handleSort('total_events')}
                >
                  {labels.events}{sortIndicator('total_events')}
                </th>
                <th
                  className="py-2 px-2 text-xs text-muted-foreground font-semibold cursor-pointer hover:text-foreground"
                  onClick={() => handleSort('total_fatalities')}
                >
                  {labels.fatalities}{sortIndicator('total_fatalities')}
                </th>
                <th
                  className="py-2 px-2 text-xs text-muted-foreground font-semibold cursor-pointer hover:text-foreground"
                  onClick={() => handleSort('lethality')}
                >
                  {labels.lethality}{sortIndicator('lethality')}
                </th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((actor) => (
                <tr
                  key={actor.actor}
                  onClick={() => handleSelectActor(actor)}
                  className={`border-b border-border/50 cursor-pointer hover:bg-muted/50 transition-colors ${selectedActor === actor.actor ? 'bg-muted/70' : ''}`}
                >
                  <td className="py-2 px-2 text-foreground font-medium truncate max-w-[160px]">{actor.actor}</td>
                  <td className="py-2 px-2 text-foreground">{actor.total_events.toLocaleString()}</td>
                  <td className="py-2 px-2 text-foreground">{actor.total_fatalities.toLocaleString()}</td>
                  <td className="py-2 px-2">
                    <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-bold ${actor.lethality >= 1 ? 'bg-red-500/20 text-red-400' : 'bg-muted text-muted-foreground'}`}>
                      {actor.lethality.toFixed(2)}
                    </span>
                  </td>
                </tr>
              ))}
              {sorted.length === 0 && (
                <tr>
                  <td colSpan={4} className="text-center py-8 text-muted-foreground">{labels.noData}</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Right: Actor profile */}
        <div className="rounded-lg border border-border bg-card/50 p-4">
          {profileLoading && (
            <div className="flex items-center justify-center h-full text-muted-foreground">
              <div className="animate-spin h-6 w-6 border-2 border-muted-foreground border-t-transparent rounded-full" />
            </div>
          )}
          {!profileLoading && profile && (
            <div>
              <h3 className="text-lg font-bold text-foreground mb-3">{profile.actor}</h3>
              <div className="grid grid-cols-2 gap-3 mb-4">
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wider">{labels.events}</p>
                  <p className="text-xl font-bold text-red-500">{profile.total_events.toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wider">{labels.fatalities}</p>
                  <p className="text-xl font-bold text-orange-500">{profile.total_fatalities.toLocaleString()}</p>
                </div>
              </div>
              <div className="space-y-3">
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">{labels.countries}</p>
                  <div className="flex flex-wrap gap-1">
                    {profile.countries.map((c) => (
                      <span key={c} className="inline-block rounded-full bg-blue-500/20 text-blue-400 px-2 py-0.5 text-xs">{c}</span>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">{labels.events} Types</p>
                  <div className="flex flex-wrap gap-1">
                    {profile.event_types.map((t) => (
                      <span key={t} className="inline-block rounded-full bg-muted px-2 py-0.5 text-xs text-foreground">{t}</span>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">{labels.theaters}</p>
                  <div className="flex flex-wrap gap-1">
                    {profile.theaters.map((t) => (
                      <span key={t} className={`inline-block rounded-full px-2 py-0.5 text-xs ${THEATER_COLORS[t] ?? 'bg-muted text-foreground'}`}>{t}</span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
          {!profileLoading && !profile && (
            <div className="flex items-center justify-center h-full text-sm text-muted-foreground">
              Select an actor from the table to view profile
            </div>
          )}
        </div>
      </div>
    </ChartPanel>
  )
}
