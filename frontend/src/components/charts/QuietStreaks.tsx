import { useState, useCallback } from 'react'
import ReactECharts from 'echarts-for-react'
import type { EChartsOption, ECharts } from 'echarts'
import { Card, CardContent } from '@/components/ui/card'
import { api } from '@/api/client'
import { useApiData } from '@/hooks/useApiData'
import { useThemeStore } from '@/store/theme'
import { getChartColors } from '@/lib/chart-theme'
import { useLabels } from '@/lib/labels'
import { exportPng, exportCsv } from '@/lib/export'
import { ChartPanel } from './ChartPanel'

export function QuietStreaks() {
  const { data, loading, error } = useApiData(() => api.getQuietStreaks())
  const dark = useThemeStore((s) => s.dark)
  const colors = getChartColors(dark)
  const chartLabels = useLabels()
  const [chartInstance, setChartInstance] = useState<ECharts | null>(null)

  const current = data?.current_streak
  const longest = data?.longest_streak
  const streaks = data?.top_streaks ?? []

  const barLabels = streaks.map(
    (s) => `${s.start_date} \u2192 ${s.end_date}`,
  )

  const option: EChartsOption = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params: unknown) => {
        const p = (params as { name: string; value: number }[])[0]
        return `${p.name}<br/>${p.value} quiet ${chartLabels.days}`
      },
    },
    xAxis: {
      type: 'value',
      axisLabel: { color: colors.axisLabel },
      splitLine: { lineStyle: { color: colors.splitLine } },
    },
    yAxis: {
      type: 'category',
      data: barLabels,
      axisLabel: { color: colors.labelPrimary, fontSize: 10 },
      axisLine: { lineStyle: { color: colors.axisLine } },
    },
    series: [
      {
        type: 'bar',
        data: streaks.map((s) => s.days),
        itemStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 1, y2: 0,
            colorStops: [
              { offset: 0, color: '#10b981' },
              { offset: 1, color: '#22d3ee' },
            ],
          },
          borderRadius: [0, 4, 4, 0],
        },
        barMaxWidth: 18,
      },
    ],
    grid: { left: 170, right: 20, top: 10, bottom: 20 },
  }

  const handleExportPng = useCallback(() => {
    if (chartInstance) exportPng(chartInstance, 'quiet-streaks')
  }, [chartInstance])

  const handleExportCsv = useCallback(() => {
    exportCsv(
      streaks.map((s) => ({ start_date: s.start_date, end_date: s.end_date, days: s.days })),
      'quiet-streaks',
    )
  }, [streaks])

  return (
    <ChartPanel title={chartLabels.quietStreaks} loading={loading} error={error} onExportPng={handleExportPng} onExportCsv={handleExportCsv}>
      <div className="grid grid-cols-2 gap-4 mb-4">
        <Card className="bg-card border-border">
          <CardContent className="p-3">
            <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">
              Current Streak
            </p>
            <p className="text-2xl font-bold text-emerald-500">
              {current ? `${current.days} ${chartLabels.days}` : '\u2014'}
            </p>
            {current && (
              <p className="text-xs text-muted-foreground mt-1">
                Since {current.start_date}
              </p>
            )}
          </CardContent>
        </Card>
        <Card className="bg-card border-border">
          <CardContent className="p-3">
            <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">
              Longest Streak
            </p>
            <p className="text-2xl font-bold text-cyan-400">
              {longest ? `${longest.days} ${chartLabels.days}` : '\u2014'}
            </p>
            {longest && (
              <p className="text-xs text-muted-foreground mt-1">
                {longest.start_date} {'\u2192'} {longest.end_date}
              </p>
            )}
          </CardContent>
        </Card>
      </div>
      {streaks.length > 0 && (
        <ReactECharts
          option={option}
          style={{ height: Math.max(120, streaks.length * 35) }}
          onChartReady={(instance) => setChartInstance(instance)}
        />
      )}
    </ChartPanel>
  )
}
