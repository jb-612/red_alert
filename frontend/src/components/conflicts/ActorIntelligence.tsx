import { useState, useCallback } from 'react'
import { Search } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { acledApi } from '@/api/acledClient'
import type { AcledActorProfile, AcledTopActorEntry } from '@/api/acledClient'
import { useAcledData } from '@/hooks/useAcledData'
import { useLabels } from '@/lib/labels'
import { ChartPanel } from '@/components/charts/ChartPanel'

const THEATER_COLORS: Record<string, string> = {
  core_me: 'bg-red-500/20 text-red-400',
  maritime: 'bg-blue-500/20 text-blue-400',
  extended_me: 'bg-amber-500/20 text-amber-400',
  global_terror: 'bg-purple-500/20 text-purple-400',
}

export function ActorIntelligence() {
  const { data, loading, error } = useAcledData(() => acledApi.getTopActors())
  const labels = useLabels()
  const [expandedActor, setExpandedActor] = useState<string | null>(null)
  const [profile, setProfile] = useState<AcledActorProfile | null>(null)
  const [profileLoading, setProfileLoading] = useState(false)
  const [query, setQuery] = useState('')
  const [searchProfile, setSearchProfile] = useState<AcledActorProfile | null>(null)
  const [searchLoading, setSearchLoading] = useState(false)
  const [searchError, setSearchError] = useState<string | null>(null)

  const actors = data?.actors ?? []

  const handleExpand = useCallback((actor: AcledTopActorEntry) => {
    if (expandedActor === actor.actor) {
      setExpandedActor(null)
      setProfile(null)
      return
    }
    setExpandedActor(actor.actor)
    setProfileLoading(true)
    acledApi.getAcledActorProfile(actor.actor)
      .then((result) => {
        setProfile(result)
        setProfileLoading(false)
      })
      .catch(() => {
        setProfileLoading(false)
      })
  }, [expandedActor])

  const handleSearch = useCallback(() => {
    if (!query.trim()) return
    setSearchLoading(true)
    setSearchError(null)
    setSearchProfile(null)
    acledApi.getAcledActorProfile(query.trim())
      .then((result) => {
        setSearchProfile(result)
        setSearchLoading(false)
      })
      .catch((err: unknown) => {
        setSearchError(err instanceof Error ? err.message : 'Unknown error')
        setSearchLoading(false)
      })
  }, [query])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleSearch()
  }, [handleSearch])

  function getLethalityBadge(lethality: number) {
    if (lethality >= 2) return 'bg-red-500/20 text-red-400'
    if (lethality >= 1) return 'bg-orange-500/20 text-orange-400'
    return 'bg-muted text-muted-foreground'
  }

  return (
    <ChartPanel title={labels.actorIntel} loading={loading} error={error}>
      {/* Actor grid */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        {actors.map((actor) => {
          const isExpanded = expandedActor === actor.actor
          return (
            <div key={actor.actor}>
              <Card
                className={`bg-card border-border cursor-pointer hover:bg-muted/50 transition-all ${isExpanded ? 'ring-2 ring-primary' : ''}`}
                onClick={() => handleExpand(actor)}
              >
                <CardContent className="p-4">
                  <div className="flex items-start justify-between mb-2">
                    <h4 className="text-sm font-bold text-foreground truncate flex-1">{actor.actor}</h4>
                    <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-bold shrink-0 ml-2 ${getLethalityBadge(actor.lethality)}`}>
                      {actor.lethality.toFixed(2)}
                    </span>
                  </div>
                  <div className="flex gap-4 text-xs">
                    <span className="text-muted-foreground">{actor.total_events.toLocaleString()} {labels.events}</span>
                    <span className="text-muted-foreground">{actor.total_fatalities.toLocaleString()} {labels.fatalities}</span>
                  </div>
                </CardContent>
              </Card>

              {/* Expanded profile */}
              {isExpanded && (
                <div className="mt-2 rounded-lg border border-border bg-card/50 p-4">
                  {profileLoading && (
                    <div className="flex items-center justify-center py-4">
                      <div className="animate-spin h-5 w-5 border-2 border-muted-foreground border-t-transparent rounded-full" />
                    </div>
                  )}
                  {!profileLoading && profile && (
                    <div className="space-y-2">
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
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Search bar */}
      <div className="border-t border-border pt-4">
        <div className="flex gap-2 mb-3">
          <div className="relative flex-1">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 size-3.5 text-muted-foreground" />
            <input
              type="text"
              placeholder={labels.searchActor}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              className="w-full rounded-md border border-input bg-background pl-8 pr-3 py-1.5 text-sm text-foreground placeholder:text-muted-foreground"
            />
          </div>
          <Button size="sm" onClick={handleSearch} disabled={searchLoading || !query.trim()}>
            {searchLoading ? labels.loading : 'Search'}
          </Button>
        </div>

        {searchError && <p className="text-sm text-red-400 mb-3">{searchError}</p>}

        {searchProfile && (
          <Card className="bg-card border-border">
            <CardContent className="p-4">
              <h3 className="text-lg font-bold text-foreground mb-3">{searchProfile.actor}</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wider">{labels.events}</p>
                  <p className="text-xl font-bold text-red-500">{searchProfile.total_events.toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wider">{labels.fatalities}</p>
                  <p className="text-xl font-bold text-orange-500">{searchProfile.total_fatalities.toLocaleString()}</p>
                </div>
              </div>
              <div className="mt-3 space-y-2">
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">{labels.countries}</p>
                  <div className="flex flex-wrap gap-1">
                    {searchProfile.countries.map((c) => (
                      <span key={c} className="inline-block rounded-full bg-blue-500/20 text-blue-400 px-2 py-0.5 text-xs">{c}</span>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">{labels.theaters}</p>
                  <div className="flex flex-wrap gap-1">
                    {searchProfile.theaters.map((t) => (
                      <span key={t} className={`inline-block rounded-full px-2 py-0.5 text-xs ${THEATER_COLORS[t] ?? 'bg-muted text-foreground'}`}>{t}</span>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </ChartPanel>
  )
}
