import { useState, useCallback } from 'react'
import ReactECharts from 'echarts-for-react'
import type { EChartsOption, ECharts } from 'echarts'
import { acledApi } from '@/api/acledClient'
import { useAcledData } from '@/hooks/useAcledData'
import { useThemeStore } from '@/store/theme'
import { getChartColors } from '@/lib/chart-theme'
import { useLabels } from '@/lib/labels'
import { exportPng, exportCsv } from '@/lib/export'
import { ChartPanel } from '@/components/charts/ChartPanel'

export function CivilianImpact() {
  const { data, loading, error } = useAcledData(() => acledApi.getAcledCivilianImpact())
  const dark = useThemeStore((s) => s.dark)
  const colors = getChartColors(dark)
  const labels = useLabels()
  const [chartInstance, setChartInstance] = useState<ECharts | null>(null)

  const byCountry = (data?.by_country ?? []).slice(0, 10)
  const sorted = [...byCountry].reverse()

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
    if (chartInstance) exportPng(chartInstance, 'civilian-impact')
  }, [chartInstance])

  const handleExportCsv = useCallback(() => {
    exportCsv(
      (data?.by_country ?? []).map((c) => ({ country: c.country, civilian_events: c.civilian_events, civilian_fatalities: c.civilian_fatalities })),
      'civilian-impact',
    )
  }, [data])

  return (
    <ChartPanel title={labels.civilianImpact} loading={loading} error={error} onExportPng={handleExportPng} onExportCsv={handleExportCsv}>
      {byCountry.length > 0 ? (
        <ReactECharts option={option} style={{ height: 300 }} onChartReady={(instance) => setChartInstance(instance)} />
      ) : (
        <p className="text-sm text-muted-foreground text-center py-8">{labels.noData}</p>
      )}
    </ChartPanel>
  )
}
