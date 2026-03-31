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

const TYPE_COLORS: Record<string, string> = {
  'Battles': '#ef4444',
  'Explosions/Remote violence': '#f97316',
  'Violence against civilians': '#a855f7',
}

export function ConflictByType() {
  const { data, loading, error } = useAcledData(() => acledApi.getAcledByType())
  const dark = useThemeStore((s) => s.dark)
  const colors = getChartColors(dark)
  const labels = useLabels()
  const [chartInstance, setChartInstance] = useState<ECharts | null>(null)

  const types = data ?? []

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
        data: types.map((t, i) => ({
          name: t.event_type,
          value: t.count,
          itemStyle: {
            color: TYPE_COLORS[t.event_type] ?? ['#22c55e', '#06b6d4', '#6b7280', '#eab308'][i % 4],
          },
        })),
      },
    ],
  }

  const handleExportPng = useCallback(() => {
    if (chartInstance) exportPng(chartInstance, 'conflict-by-type')
  }, [chartInstance])

  const handleExportCsv = useCallback(() => {
    exportCsv(
      types.map((t) => ({ event_type: t.event_type, sub_event_type: t.sub_event_type ?? '', count: t.count, fatalities: t.fatalities })),
      'conflict-by-type',
    )
  }, [types])

  return (
    <ChartPanel title={labels.events} loading={loading} error={error} onExportPng={handleExportPng} onExportCsv={handleExportCsv}>
      <ReactECharts option={option} style={{ height: 280 }} onChartReady={(instance) => setChartInstance(instance)} />
    </ChartPanel>
  )
}
