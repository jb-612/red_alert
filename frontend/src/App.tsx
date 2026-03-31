import { useEffect, useState, lazy, Suspense } from 'react'
import { Header } from '@/components/layout/Header'
import { Sidebar } from '@/components/layout/Sidebar'
import { KpiCards } from '@/components/charts/KpiCards'
import { AlertTimeline } from '@/components/charts/AlertTimeline'
import { CategoryBreakdown } from '@/components/charts/CategoryBreakdown'
import { HourlyHeatmap } from '@/components/charts/HourlyHeatmap'
import { AlertMap } from '@/components/map/AlertMap'
import { RegionBreadcrumb } from '@/components/drilldown/RegionBreadcrumb'
import { api } from '@/api/client'
import type { GeoLocation } from '@/api/client'
import { useFilterStore } from '@/store/filters'
import { useLocaleStore } from '@/store/locale'

// Lazy load below-the-fold components
const LocationRanking = lazy(() => import('@/components/charts/LocationRanking').then(m => ({ default: m.LocationRanking })))
const SleepScore = lazy(() => import('@/components/charts/SleepScore').then(m => ({ default: m.SleepScore })))
const BestWeekdays = lazy(() => import('@/components/charts/BestWeekdays').then(m => ({ default: m.BestWeekdays })))
const QuietStreaks = lazy(() => import('@/components/charts/QuietStreaks').then(m => ({ default: m.QuietStreaks })))
const PeriodComparison = lazy(() => import('@/components/charts/PeriodComparison').then(m => ({ default: m.PeriodComparison })))
const AnomalyDetection = lazy(() => import('@/components/charts/AnomalyDetection').then(m => ({ default: m.AnomalyDetection })))
const PrealertCorrelation = lazy(() => import('@/components/charts/PrealertCorrelation').then(m => ({ default: m.PrealertCorrelation })))

function LazyFallback() {
  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="flex items-center justify-center h-[280px] text-muted-foreground">
        <div className="animate-spin h-6 w-6 border-2 border-muted-foreground border-t-transparent rounded-full" />
      </div>
    </div>
  )
}

export default function App() {
  const [geoData, setGeoData] = useState<GeoLocation[]>([])
  const comparisonMode = useFilterStore((s) => s.comparisonMode)
  useLocaleStore((s) => s.dir) // subscribe to trigger re-render on locale change

  useEffect(() => {
    api.getGeoData().then(setGeoData).catch(() => { /* handled by individual components */ })
  }, [])

  return (
    <div className="flex h-screen flex-col bg-background text-foreground">
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto p-6 space-y-6">
          <KpiCards />
          <div className="rounded-lg border border-border bg-card p-4">
            <h2 className="text-sm font-semibold text-foreground mb-3">Alert Map</h2>
            <div className="h-[450px] rounded-lg overflow-hidden">
              <AlertMap data={geoData} />
            </div>
            <RegionBreadcrumb />
          </div>
          <AlertTimeline />
          <div className="grid grid-cols-2 gap-6">
            <CategoryBreakdown />
            <HourlyHeatmap />
          </div>
          <Suspense fallback={<LazyFallback />}>
            <LocationRanking />
          </Suspense>
          <div className="grid grid-cols-2 gap-6">
            <Suspense fallback={<LazyFallback />}><SleepScore /></Suspense>
            <Suspense fallback={<LazyFallback />}><BestWeekdays /></Suspense>
          </div>
          <Suspense fallback={<LazyFallback />}><QuietStreaks /></Suspense>
          {comparisonMode && (
            <Suspense fallback={<LazyFallback />}><PeriodComparison /></Suspense>
          )}
          <Suspense fallback={<LazyFallback />}><AnomalyDetection /></Suspense>
          <Suspense fallback={<LazyFallback />}><PrealertCorrelation /></Suspense>
        </main>
      </div>
    </div>
  )
}
