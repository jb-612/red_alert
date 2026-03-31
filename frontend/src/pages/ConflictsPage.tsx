import { useEffect, useState, lazy, Suspense } from 'react'
import { ConflictSidebar } from '@/components/conflicts/ConflictSidebar'
import { SituationHeader } from '@/components/conflicts/SituationHeader'
import { TheaterCards } from '@/components/conflicts/TheaterCards'
import { acledApi } from '@/api/acledClient'
import type { AcledGeoPoint } from '@/api/acledClient'
import { useAcledFilterStore } from '@/store/acledFilters'

// Lazy load heavy components
const ConflictMap = lazy(() => import('@/components/conflicts/ConflictMap').then(m => ({ default: m.ConflictMap })))
const TheaterTimeline = lazy(() => import('@/components/conflicts/TheaterTimeline').then(m => ({ default: m.TheaterTimeline })))
const ForceAnalysis = lazy(() => import('@/components/conflicts/ForceAnalysis').then(m => ({ default: m.ForceAnalysis })))
const CountryIntelligence = lazy(() => import('@/components/conflicts/CountryIntelligence').then(m => ({ default: m.CountryIntelligence })))
const EscalationWarning = lazy(() => import('@/components/conflicts/EscalationWarning').then(m => ({ default: m.EscalationWarning })))
const CivilianDashboard = lazy(() => import('@/components/conflicts/CivilianDashboard').then(m => ({ default: m.CivilianDashboard })))
const ConflictAnomalies = lazy(() => import('@/components/conflicts/ConflictAnomalies').then(m => ({ default: m.ConflictAnomalies })))
const ActorIntelligence = lazy(() => import('@/components/conflicts/ActorIntelligence').then(m => ({ default: m.ActorIntelligence })))

function LazyFallback() {
  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="flex items-center justify-center h-[280px] text-muted-foreground">
        <div className="animate-spin h-6 w-6 border-2 border-muted-foreground border-t-transparent rounded-full" />
      </div>
    </div>
  )
}

export function ConflictsPage() {
  const [geoData, setGeoData] = useState<AcledGeoPoint[]>([])
  const { dateRange, countries, eventTypes, theaters, actor, granularity } = useAcledFilterStore()

  useEffect(() => {
    acledApi.getAcledGeo().then(setGeoData).catch(() => { /* handled by individual components */ })
  }, [dateRange.from, dateRange.to, countries, eventTypes, theaters, actor, granularity])

  return (
    <div className="flex flex-1 overflow-hidden">
      <ConflictSidebar />
      <main className="flex-1 overflow-y-auto p-6 space-y-6">
        <SituationHeader />
        <TheaterCards />
        <Suspense fallback={<LazyFallback />}>
          <div className="rounded-lg border border-border bg-card p-4">
            <h2 className="text-sm font-semibold text-foreground mb-3">Conflict Map</h2>
            <div className="h-[500px] rounded-lg overflow-hidden">
              <ConflictMap data={geoData} />
            </div>
          </div>
        </Suspense>
        <Suspense fallback={<LazyFallback />}><TheaterTimeline /></Suspense>
        <Suspense fallback={<LazyFallback />}><ForceAnalysis /></Suspense>
        <Suspense fallback={<LazyFallback />}><CountryIntelligence /></Suspense>
        <Suspense fallback={<LazyFallback />}><EscalationWarning /></Suspense>
        <Suspense fallback={<LazyFallback />}><CivilianDashboard /></Suspense>
        <Suspense fallback={<LazyFallback />}><ConflictAnomalies /></Suspense>
        <Suspense fallback={<LazyFallback />}><ActorIntelligence /></Suspense>
      </main>
    </div>
  )
}
