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

function computeRollingAvg(
  trend: { date: string; peaceful: boolean }[],
  window: number,
): { date: string; avg: number }[] {
  return trend.map((_, i) => {
    const start = Math.max(0, i - window + 1)
    const slice = trend.slice(start, i + 1)
    const avg = slice.filter((n) => n.peaceful).length / slice.length
    return { date: trend[i].date, avg: Math.round(avg * 100) }
  })
}

export function SleepScore() {
  const { data, loading, error } = useApiData(() => api.getSleepScore())
  const dark = useThemeStore((s) => s.dark)
  const colors = getChartColors(dark)
  const labels = useLabels()
  const [chartInstance, setChartInstance] = useState<ECharts | null>(null)

  const score = data?.score ?? 0
  const total = data?.total_nights ?? 0
  const peaceful = data?.peaceful_nights ?? 0
  const trend = data?.trend ?? []
  const rolling = computeRollingAvg(trend, 7)

  const scoreColor =
    score >= 80 ? '#10b981' : score >= 50 ? '#f59e0b' : '#ef4444'

  const option: EChartsOption = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      formatter: (params: unknown) => {
        const p = (params as { name: string; value: number }[])[0]
        return `${p.name}<br/>7-night avg: ${p.value}%`
      },
    },
    xAxis: {
      type: 'category',
      data: rolling.map((r) => r.date),
      axisLabel: { color: colors.axisLabel, fontSize: 10, rotate: 45 },
      axisLine: { lineStyle: { color: colors.axisLine } },
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      axisLabel: { color: colors.axisLabel, formatter: '{value}%' },
      splitLine: { lineStyle: { color: colors.splitLine } },
    },
    series: [
      {
        type: 'line',
        data: rolling.map((r) => r.avg),
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#10b981', width: 2 },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(16,185,129,0.3)' },
              { offset: 1, color: 'rgba(16,185,129,0.02)' },
            ],
          },
        },
      },
    ],
    dataZoom: [
      { type: 'inside', start: 0, end: 100 },
    ],
    grid: { left: 50, right: 20, top: 60, bottom: 50 },
  }

  const handleExportPng = useCallback(() => {
    if (chartInstance) exportPng(chartInstance, 'sleep-score')
  }, [chartInstance])

  const handleExportCsv = useCallback(() => {
    exportCsv(
      rolling.map((r) => ({ date: r.date, rolling_avg_pct: r.avg })),
      'sleep-score',
    )
  }, [rolling])

  return (
    <ChartPanel title={labels.sleepScore} loading={loading} error={error} onExportPng={handleExportPng} onExportCsv={handleExportCsv}>
      <div className="flex items-center gap-4 mb-3">
        <span className="text-4xl font-bold" style={{ color: scoreColor }}>
          {score.toFixed(0)}%
        </span>
        <div className="text-xs text-muted-foreground">
          <p>{peaceful} peaceful / {total} nights</p>
        </div>
      </div>
      {trend.length > 1 && (
        <ReactECharts option={option} style={{ height: 200 }} onChartReady={(instance) => setChartInstance(instance)} />
      )}
    </ChartPanel>
  )
}
