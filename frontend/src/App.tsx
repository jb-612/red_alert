import { useEffect, useState } from 'react'
import { Header } from '@/components/layout/Header'
import { Sidebar } from '@/components/layout/Sidebar'
import { KpiCards } from '@/components/charts/KpiCards'
import { AlertTimeline } from '@/components/charts/AlertTimeline'
import { CategoryBreakdown } from '@/components/charts/CategoryBreakdown'
import { HourlyHeatmap } from '@/components/charts/HourlyHeatmap'
import { LocationRanking } from '@/components/charts/LocationRanking'
import { SleepScore } from '@/components/charts/SleepScore'
import { BestWeekdays } from '@/components/charts/BestWeekdays'
import { QuietStreaks } from '@/components/charts/QuietStreaks'
import { AnomalyDetection } from '@/components/charts/AnomalyDetection'
import { PeriodComparison } from '@/components/charts/PeriodComparison'
import { PrealertCorrelation } from '@/components/charts/PrealertCorrelation'
import { AlertMap } from '@/components/map/AlertMap'
import { RegionBreadcrumb } from '@/components/drilldown/RegionBreadcrumb'
import { api } from '@/api/client'
import type { GeoLocation } from '@/api/client'
import { useFilterStore } from '@/store/filters'
import { useLocaleStore } from '@/store/locale'

export default function App() {
  const [geoData, setGeoData] = useState<GeoLocation[]>([])
  const comparisonMode = useFilterStore((s) => s.comparisonMode)
  const _dir = useLocaleStore((s) => s.dir) // subscribe to trigger re-render on locale change

  useEffect(() => {
    api.getGeoData().then(setGeoData)
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
          <LocationRanking />
          <div className="grid grid-cols-2 gap-6">
            <SleepScore />
            <BestWeekdays />
          </div>
          <QuietStreaks />
          {comparisonMode && <PeriodComparison />}
          <AnomalyDetection />
          <PrealertCorrelation />
        </main>
      </div>
    </div>
  )
}
