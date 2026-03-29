import { useState, useCallback } from 'react'
import ReactECharts from 'echarts-for-react'
import type { EChartsOption, ECharts } from 'echarts'
import { api } from '@/api/client'
import { useApiData } from '@/hooks/useApiData'
import { useThemeStore } from '@/store/theme'
import { getChartColors } from '@/lib/chart-theme'
import { useLabels } from '@/lib/labels'
import { exportPng, exportCsv } from '@/lib/export'
import { ChartPanel } from './ChartPanel'

export function LocationRanking() {
  const { data, loading, error } = useApiData(() => api.getLocationsByCount(10))
  const dark = useThemeStore((s) => s.dark)
  const colors = getChartColors(dark)
  const labels = useLabels()
  const [chartInstance, setChartInstance] = useState<ECharts | null>(null)

  const locations = data ?? []
  // Reverse so highest is at top in horizontal bar
  const sorted = [...locations].reverse()

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
      data: sorted.map((l) => l.location_name),
      axisLabel: { color: colors.labelPrimary, fontSize: 12 },
      axisLine: { lineStyle: { color: colors.axisLine } },
    },
    series: [
      {
        type: 'bar',
        data: sorted.map((l) => l.count),
        itemStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 1, y2: 0,
            colorStops: [
              { offset: 0, color: '#ef4444' },
              { offset: 1, color: '#f97316' },
            ],
          },
          borderRadius: [0, 4, 4, 0],
        },
        barMaxWidth: 20,
      },
    ],
    grid: { left: 80, right: 30, top: 10, bottom: 20 },
  }

  const handleExportPng = useCallback(() => {
    if (chartInstance) exportPng(chartInstance, 'top-locations')
  }, [chartInstance])

  const handleExportCsv = useCallback(() => {
    exportCsv(
      locations.map((l) => ({ location: l.location_name, count: l.count })),
      'top-locations',
    )
  }, [locations])

  return (
    <ChartPanel title={labels.topLocations} loading={loading} error={error} onExportPng={handleExportPng} onExportCsv={handleExportCsv}>
      <ReactECharts option={option} style={{ height: 320 }} onChartReady={(instance) => setChartInstance(instance)} />
    </ChartPanel>
  )
}
