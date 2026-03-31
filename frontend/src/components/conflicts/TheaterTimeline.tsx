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

const THEATER_COLORS: Record<string, string> = {
  core_me: '#ef4444',
  maritime: '#3b82f6',
  extended_me: '#f59e0b',
  global_terror: '#a855f7',
}

export function TheaterTimeline() {
  const { data, loading, error } = useAcledData(() => acledApi.getAcledTheaterTimeline())
  const dark = useThemeStore((s) => s.dark)
  const colors = getChartColors(dark)
  const labels = useLabels()
  const [chartInstance, setChartInstance] = useState<ECharts | null>(null)

  const series = data?.series ?? []

  // Collect all unique periods across all series
  const allPeriods = Array.from(
    new Set(series.flatMap((s) => s.buckets.map((b) => b.period)))
  ).sort()

  const theaterLabel = (key: string): string => {
    if (key === 'core_me') return labels.coreME
    if (key === 'maritime') return labels.maritime
    if (key === 'extended_me') return labels.extendedME
    if (key === 'global_terror') return labels.globalTerror
    return key
  }

  const option: EChartsOption = {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis' },
    legend: {
      data: series.map((s) => theaterLabel(s.theater)),
      textStyle: { color: colors.labelPrimary, fontSize: 11 },
      top: 0,
    },
    xAxis: {
      type: 'category',
      data: allPeriods,
      axisLabel: { color: colors.axisLabel, fontSize: 10, rotate: 45 },
      axisLine: { lineStyle: { color: colors.axisLine } },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: colors.axisLabel },
      splitLine: { lineStyle: { color: colors.splitLine } },
    },
    series: series.map((s) => {
      const countMap = new Map(s.buckets.map((b) => [b.period, b.count]))
      return {
        name: theaterLabel(s.theater),
        type: 'line' as const,
        areaStyle: { opacity: 0.3 },
        smooth: true,
        data: allPeriods.map((p) => countMap.get(p) ?? 0),
        itemStyle: { color: THEATER_COLORS[s.theater] ?? '#6b7280' },
        lineStyle: { width: 2 },
      }
    }),
    grid: { left: 50, right: 20, top: 40, bottom: 60 },
  }

  const handleExportPng = useCallback(() => {
    if (chartInstance) exportPng(chartInstance, 'theater-timeline')
  }, [chartInstance])

  const handleExportCsv = useCallback(() => {
    const rows: Record<string, unknown>[] = []
    for (const s of series) {
      for (const b of s.buckets) {
        rows.push({ theater: s.theater, period: b.period, count: b.count, fatalities: b.fatalities })
      }
    }
    exportCsv(rows, 'theater-timeline')
  }, [series])

  return (
    <ChartPanel title={labels.theaterTimeline} loading={loading} error={error} onExportPng={handleExportPng} onExportCsv={handleExportCsv}>
      <ReactECharts option={option} style={{ height: 300 }} onChartReady={(instance) => setChartInstance(instance)} />
    </ChartPanel>
  )
}
