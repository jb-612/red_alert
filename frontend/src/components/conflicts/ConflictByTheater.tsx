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

export function ConflictByTheater() {
  const { data, loading, error } = useAcledData(() => acledApi.getAcledByTheater())
  const dark = useThemeStore((s) => s.dark)
  const colors = getChartColors(dark)
  const labels = useLabels()
  const [chartInstance, setChartInstance] = useState<ECharts | null>(null)

  const theaters = data ?? []

  const theaterLabel = (key: string): string => {
    if (key === 'core_me') return labels.coreME
    if (key === 'maritime') return labels.maritime
    if (key === 'extended_me') return labels.extendedME
    if (key === 'global_terror') return labels.globalTerror
    return key
  }

  const option: EChartsOption = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)',
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: true,
        itemStyle: { borderRadius: 6, borderColor: 'transparent', borderWidth: 2 },
        label: { color: colors.labelPrimary, fontSize: 11 },
        data: theaters.map((t) => ({
          name: theaterLabel(t.theater),
          value: t.count,
          itemStyle: { color: THEATER_COLORS[t.theater] ?? '#6b7280' },
        })),
      },
    ],
  }

  const handleExportPng = useCallback(() => {
    if (chartInstance) exportPng(chartInstance, 'conflict-by-theater')
  }, [chartInstance])

  const handleExportCsv = useCallback(() => {
    exportCsv(
      theaters.map((t) => ({ theater: t.theater, count: t.count, fatalities: t.fatalities })),
      'conflict-by-theater',
    )
  }, [theaters])

  return (
    <ChartPanel title={labels.theaters} loading={loading} error={error} onExportPng={handleExportPng} onExportCsv={handleExportCsv}>
      <ReactECharts option={option} style={{ height: 280 }} onChartReady={(instance) => setChartInstance(instance)} />
    </ChartPanel>
  )
}
