import { useState, useCallback } from 'react'
import ReactECharts from 'echarts-for-react'
import type { EChartsOption, ECharts } from 'echarts'
import { Card, CardContent } from '@/components/ui/card'
import { acledApi } from '@/api/acledClient'
import { useAcledData } from '@/hooks/useAcledData'
import { useThemeStore } from '@/store/theme'
import { getChartColors } from '@/lib/chart-theme'
import { useLabels } from '@/lib/labels'
import { exportPng, exportCsv } from '@/lib/export'
import { ChartPanel } from '@/components/charts/ChartPanel'

export function CivilianDashboard() {
  const { data, loading, error } = useAcledData(() => acledApi.getAcledCivilianImpact())
  const { data: situation } = useAcledData(() => acledApi.getSituation())
  const dark = useThemeStore((s) => s.dark)
  const colors = getChartColors(dark)
  const labels = useLabels()
  const [chartInstance, setChartInstance] = useState<ECharts | null>(null)

  const byCountry = (data?.by_country ?? []).slice(0, 10)
  const sorted = [...byCountry].reverse()

  const totalEvents = data?.total_civilian_events ?? 0
  const totalCivilianFatalities = data?.total_civilian_fatalities ?? 0
  const totalAllEvents = situation?.total_events ?? 1
  const civilianRatio = totalAllEvents > 0 ? ((totalEvents / totalAllEvents) * 100).toFixed(1) : '0'

  const option: EChartsOption = {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    xAxis: {
      type: 'value',
      axisLabel: { color: colors.axisLabel },
      splitLine: { lineStyle: { color: colors.splitLine } },
    },
    yAxis: {
      type: 'category',
      data: sorted.map((c) => c.country),
      axisLabel: { color: colors.labelPrimary, fontSize: 12 },
      axisLine: { lineStyle: { color: colors.axisLine } },
    },
    series: [
      {
        type: 'bar',
        data: sorted.map((c) => c.civilian_fatalities),
        itemStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 1, y2: 0,
            colorStops: [
              { offset: 0, color: '#a855f7' },
              { offset: 1, color: '#ef4444' },
            ],
          },
          borderRadius: [0, 4, 4, 0],
        },
        barMaxWidth: 20,
      },
    ],
    grid: { left: 100, right: 30, top: 10, bottom: 20 },
  }

  const handleExportPng = useCallback(() => {
    if (chartInstance) exportPng(chartInstance, 'civilian-dashboard')
  }, [chartInstance])

  const handleExportCsv = useCallback(() => {
    exportCsv(
      (data?.by_country ?? []).map((c) => ({ country: c.country, civilian_events: c.civilian_events, civilian_fatalities: c.civilian_fatalities })),
      'civilian-dashboard',
    )
  }, [data])

  return (
    <ChartPanel title={labels.civilianDashboard} loading={loading} error={error} onExportPng={handleExportPng} onExportCsv={handleExportCsv}>
      {/* KPI cards */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <Card className="bg-card border-border">
          <CardContent className="p-4">
            <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">{labels.civilianImpact}</p>
            <p className="text-2xl font-bold text-purple-500">{totalEvents.toLocaleString()}</p>
          </CardContent>
        </Card>
        <Card className="bg-card border-border">
          <CardContent className="p-4">
            <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">{labels.civilianRatio}</p>
            <p className="text-2xl font-bold text-orange-500">{civilianRatio}%</p>
            <p className="text-xs text-muted-foreground mt-1">{totalCivilianFatalities.toLocaleString()} {labels.fatalities}</p>
          </CardContent>
        </Card>
      </div>

      {/* Bar chart */}
      {byCountry.length > 0 ? (
        <ReactECharts option={option} style={{ height: 300 }} onChartReady={(instance) => setChartInstance(instance)} />
      ) : (
        <p className="text-sm text-muted-foreground text-center py-8">{labels.noData}</p>
      )}
    </ChartPanel>
  )
}
