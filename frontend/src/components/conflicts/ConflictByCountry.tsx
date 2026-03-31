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

export function ConflictByCountry() {
  const { data, loading, error } = useAcledData(() => acledApi.getAcledByCountry())
  const dark = useThemeStore((s) => s.dark)
  const colors = getChartColors(dark)
  const labels = useLabels()
  const [chartInstance, setChartInstance] = useState<ECharts | null>(null)

  const countries = (data ?? []).slice(0, 10)
  const sorted = [...countries].reverse()

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
        data: sorted.map((c) => c.count),
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
    grid: { left: 100, right: 30, top: 10, bottom: 20 },
  }

  const handleExportPng = useCallback(() => {
    if (chartInstance) exportPng(chartInstance, 'conflict-by-country')
  }, [chartInstance])

  const handleExportCsv = useCallback(() => {
    exportCsv(
      (data ?? []).map((c) => ({ country: c.country, count: c.count, fatalities: c.fatalities })),
      'conflict-by-country',
    )
  }, [data])

  return (
    <ChartPanel title={`${labels.countries} (Top 10)`} loading={loading} error={error} onExportPng={handleExportPng} onExportCsv={handleExportCsv}>
      <ReactECharts option={option} style={{ height: 300 }} onChartReady={(instance) => setChartInstance(instance)} />
    </ChartPanel>
  )
}
