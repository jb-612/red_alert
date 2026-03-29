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

export function BestWeekdays() {
  const { data, loading, error } = useApiData(() => api.getBestWeekdays())
  const dark = useThemeStore((s) => s.dark)
  const colors = getChartColors(dark)
  const labels = useLabels()
  const [chartInstance, setChartInstance] = useState<ECharts | null>(null)

  const weekdays = data?.weekdays ?? []
  const hotHours = data?.hot_hours ?? []

  const maxCount = Math.max(...weekdays.map((d) => d.alert_count), 1)

  const barColors = weekdays.map((d) => {
    const ratio = d.alert_count / maxCount
    if (ratio < 0.2) return '#10b981'
    if (ratio < 0.5) return '#22d3ee'
    if (ratio < 0.75) return '#f59e0b'
    return '#ef4444'
  })

  const option: EChartsOption = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
    },
    xAxis: {
      type: 'value',
      axisLabel: { color: colors.axisLabel },
      splitLine: { lineStyle: { color: colors.splitLine } },
    },
    yAxis: {
      type: 'category',
      data: weekdays.map((d) => d.weekday_name),
      axisLabel: { color: colors.labelPrimary, fontSize: 12 },
      axisLine: { lineStyle: { color: colors.axisLine } },
    },
    series: [
      {
        type: 'bar',
        data: weekdays.map((d, i) => ({
          value: d.alert_count,
          itemStyle: { color: barColors[i] },
        })),
        barMaxWidth: 18,
        itemStyle: { borderRadius: [0, 4, 4, 0] },
      },
    ],
    grid: { left: 90, right: 20, top: 10, bottom: 20 },
  }

  const formatHour = (h: number) => `${String(h).padStart(2, '0')}:00`

  const handleExportPng = useCallback(() => {
    if (chartInstance) exportPng(chartInstance, 'best-weekdays')
  }, [chartInstance])

  const handleExportCsv = useCallback(() => {
    exportCsv(
      weekdays.map((d) => ({ weekday: d.weekday_name, alert_count: d.alert_count, rank: d.rank })),
      'best-weekdays',
    )
  }, [weekdays])

  return (
    <ChartPanel title={labels.bestWeekdays} loading={loading} error={error} onExportPng={handleExportPng} onExportCsv={handleExportCsv}>
      <ReactECharts option={option} style={{ height: 200 }} onChartReady={(instance) => setChartInstance(instance)} />
      {hotHours.length > 0 && (
        <div className="mt-3 border-t border-border pt-3">
          <p className="text-xs text-muted-foreground uppercase tracking-wider mb-2">
            Peak Alert Hour by Location
          </p>
          <div className="space-y-1">
            {hotHours.map((hh) => (
              <div
                key={hh.location_name}
                className="flex justify-between text-sm"
              >
                <span className="text-foreground truncate me-2">
                  {hh.location_name}
                </span>
                <span className="text-orange-400 font-mono whitespace-nowrap">
                  {formatHour(hh.peak_hour)} ({hh.alert_count})
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </ChartPanel>
  )
}
