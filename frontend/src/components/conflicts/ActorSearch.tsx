import { useState, useCallback } from 'react'
import { Search } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { acledApi } from '@/api/acledClient'
import type { AcledActorProfile } from '@/api/acledClient'
import { useLabels } from '@/lib/labels'
import { ChartPanel } from '@/components/charts/ChartPanel'

export function ActorSearch() {
  const labels = useLabels()
  const [query, setQuery] = useState('')
  const [profile, setProfile] = useState<AcledActorProfile | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSearch = useCallback(() => {
    if (!query.trim()) return
    setLoading(true)
    setError(null)
    setProfile(null)
    acledApi.getAcledActorProfile(query.trim())
      .then((result) => {
        setProfile(result)
        setLoading(false)
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Unknown error')
        setLoading(false)
      })
  }, [query])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleSearch()
  }, [handleSearch])

  return (
    <ChartPanel title={labels.actorProfile} loading={false} error={null}>
      <div className="flex gap-2 mb-4">
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
        <Button size="sm" onClick={handleSearch} disabled={loading || !query.trim()}>
          {loading ? labels.loading : 'Search'}
        </Button>
      </div>

      {error && (
        <p className="text-sm text-red-400 mb-4">{error}</p>
      )}

      {profile && (
        <Card className="bg-card border-border">
          <CardContent className="p-4">
            <h3 className="text-lg font-bold text-foreground mb-3">{profile.actor}</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-wider">{labels.events}</p>
                <p className="text-xl font-bold text-red-500">{profile.total_events.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-wider">{labels.fatalities}</p>
                <p className="text-xl font-bold text-orange-500">{profile.total_fatalities.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">{labels.countries}</p>
                <div className="flex flex-wrap gap-1">
                  {profile.countries.map((c) => (
                    <span key={c} className="inline-block rounded-full bg-muted px-2 py-0.5 text-xs text-foreground">{c}</span>
                  ))}
                </div>
              </div>
              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">{labels.theaters}</p>
                <div className="flex flex-wrap gap-1">
                  {profile.theaters.map((t) => (
                    <span key={t} className="inline-block rounded-full bg-muted px-2 py-0.5 text-xs text-foreground">{t}</span>
                  ))}
                </div>
              </div>
            </div>
            {profile.event_types.length > 0 && (
              <div className="mt-3">
                <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">{labels.events} Types</p>
                <div className="flex flex-wrap gap-1">
                  {profile.event_types.map((t) => (
                    <span key={t} className="inline-block rounded-full bg-muted px-2 py-0.5 text-xs text-foreground">{t}</span>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {!profile && !loading && !error && (
        <p className="text-sm text-muted-foreground text-center py-8">
          Enter an actor name to view their profile
        </p>
      )}
    </ChartPanel>
  )
}
