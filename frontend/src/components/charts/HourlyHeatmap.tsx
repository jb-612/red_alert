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

const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
const hours = Array.from({ length: 24 }, (_, i) => `${String(i).padStart(2, '0')}:00`)

export function HourlyHeatmap() {
  const { data, loading, error } = useApiData(() => api.getHeatmap())
  const dark = useThemeStore((s) => s.dark)
  const colors = getChartColors(dark)
  const labels = useLabels()
  const [chartInstance, setChartInstance] = useState<ECharts | null>(null)

  const cells = data ?? []
  const heatmapData: [number, number, number][] = cells.map((c) => [c.hour, c.weekday, c.count])
  const maxCount = Math.max(1, ...cells.map((c) => c.count))

  const option: EChartsOption = {
    backgroundColor: 'transparent',
    tooltip: {
      formatter: (params: unknown) => {
        const p = params as { value: [number, number, number] }
        return `${days[p.value[1]]} ${hours[p.value[0]]}: ${p.value[2]} alerts`
      },
    },
    xAxis: {
      type: 'category',
      data: hours,
      axisLabel: { color: colors.axisLabel, fontSize: 9, interval: 2 },
      axisLine: { lineStyle: { color: colors.axisLine } },
      splitArea: { show: true },
    },
    yAxis: {
      type: 'category',
      data: days,
      axisLabel: { color: colors.axisLabel, fontSize: 10 },
      axisLine: { lineStyle: { color: colors.axisLine } },
    },
    visualMap: {
      min: 0,
      max: maxCount,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: 0,
      inRange: {
        color: [colors.heatmapLow, '#f97316', '#ef4444'],
      },
      textStyle: { color: colors.visualMapText },
    },
    series: [
      {
        type: 'heatmap',
        data: heatmapData,
        label: { show: false },
        emphasis: {
          itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.5)' },
        },
      },
    ],
    grid: { left: 50, right: 20, top: 10, bottom: 60 },
  }

  const handleExportPng = useCallback(() => {
    if (chartInstance) exportPng(chartInstance, 'hourly-heatmap')
  }, [chartInstance])

  const handleExportCsv = useCallback(() => {
    exportCsv(
      cells.map((c) => ({ hour: c.hour, weekday: days[c.weekday], count: c.count })),
      'hourly-heatmap',
    )
  }, [cells])

  return (
    <ChartPanel title={labels.hourlyHeatmap} loading={loading} error={error} onExportPng={handleExportPng} onExportCsv={handleExportCsv}>
      <ReactECharts option={option} style={{ height: 280 }} onChartReady={(instance) => setChartInstance(instance)} />
    </ChartPanel>
  )
}
