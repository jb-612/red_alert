import { useEffect, useState, lazy, Suspense } from 'react'
import { ConflictSidebar } from '@/components/conflicts/ConflictSidebar'
import { ConflictKpiCards } from '@/components/conflicts/ConflictKpiCards'
import { acledApi } from '@/api/acledClient'
import type { AcledGeoPoint } from '@/api/acledClient'
import { useAcledFilterStore } from '@/store/acledFilters'

// Lazy load heavy components
const ConflictMap = lazy(() => import('@/components/conflicts/ConflictMap').then(m => ({ default: m.ConflictMap })))
const ConflictByTheater = lazy(() => import('@/components/conflicts/ConflictByTheater').then(m => ({ default: m.ConflictByTheater })))
const ConflictByType = lazy(() => import('@/components/conflicts/ConflictByType').then(m => ({ default: m.ConflictByType })))
const TheaterTimeline = lazy(() => import('@/components/conflicts/TheaterTimeline').then(m => ({ default: m.TheaterTimeline })))
const ConflictByCountry = lazy(() => import('@/components/conflicts/ConflictByCountry').then(m => ({ default: m.ConflictByCountry })))
const ConflictEscalation = lazy(() => import('@/components/conflicts/ConflictEscalation').then(m => ({ default: m.ConflictEscalation })))
const CivilianImpact = lazy(() => import('@/components/conflicts/CivilianImpact').then(m => ({ default: m.CivilianImpact })))
const ConflictAnomalies = lazy(() => import('@/components/conflicts/ConflictAnomalies').then(m => ({ default: m.ConflictAnomalies })))
const ActorSearch = lazy(() => import('@/components/conflicts/ActorSearch').then(m => ({ default: m.ActorSearch })))

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
        <ConflictKpiCards />
        <Suspense fallback={<LazyFallback />}>
          <div className="rounded-lg border border-border bg-card p-4">
            <h2 className="text-sm font-semibold text-foreground mb-3">Conflict Map</h2>
            <div className="h-[500px] rounded-lg overflow-hidden">
              <ConflictMap data={geoData} />
            </div>
          </div>
        </Suspense>
        <div className="grid grid-cols-2 gap-6">
          <Suspense fallback={<LazyFallback />}><ConflictByTheater /></Suspense>
          <Suspense fallback={<LazyFallback />}><ConflictByType /></Suspense>
        </div>
        <Suspense fallback={<LazyFallback />}><TheaterTimeline /></Suspense>
        <Suspense fallback={<LazyFallback />}><ConflictByCountry /></Suspense>
        <div className="grid grid-cols-2 gap-6">
          <Suspense fallback={<LazyFallback />}><ConflictEscalation /></Suspense>
          <Suspense fallback={<LazyFallback />}><CivilianImpact /></Suspense>
        </div>
        <Suspense fallback={<LazyFallback />}><ConflictAnomalies /></Suspense>
        <Suspense fallback={<LazyFallback />}><ActorSearch /></Suspense>
      </main>
    </div>
  )
}
