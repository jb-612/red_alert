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

export function AnomalyDetection() {
  const { data, loading, error } = useApiData(() => api.getAnomalies())
  const dark = useThemeStore((s) => s.dark)
  const colors = getChartColors(dark)
  const labels = useLabels()
  const [chartInstance, setChartInstance] = useState<ECharts | null>(null)

  const anomalies = data?.anomalies ?? []
  const mean = data?.mean_daily_count ?? 0
  const std = data?.std_daily_count ?? 0
  const totalDays = data?.total_days_analyzed ?? 0

  const highAnomalies = anomalies.filter((a) => a.direction === 'high')
  const lowAnomalies = anomalies.filter((a) => a.direction === 'low')

  const option: EChartsOption = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      formatter: (params: unknown) => {
        const p = params as { name: string; value: number; data: { z: number; dir: string } }
        return `${p.name}<br/>${p.value} ${labels.alerts} (z=${p.data.z}, ${p.data.dir})`
      },
    },
    xAxis: {
      type: 'category',
      data: anomalies.map((a) => a.date),
      axisLabel: { color: colors.axisLabel, fontSize: 10, rotate: 45 },
      axisLine: { lineStyle: { color: colors.axisLine } },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: colors.axisLabel },
      splitLine: { lineStyle: { color: colors.splitLine } },
    },
    series: [
      {
        type: 'bar',
        data: anomalies.map((a) => ({
          value: a.count,
          z: a.z_score,
          dir: a.direction,
          itemStyle: {
            color: a.direction === 'high' ? '#ef4444' : '#3b82f6',
          },
        })),
        barMaxWidth: 24,
        itemStyle: { borderRadius: [4, 4, 0, 0] },
      },
    ],
    grid: { left: 50, right: 20, top: 10, bottom: 60 },
  }

  const handleExportPng = useCallback(() => {
    if (chartInstance) exportPng(chartInstance, 'anomaly-detection')
  }, [chartInstance])

  const handleExportCsv = useCallback(() => {
    exportCsv(
      anomalies.map((a) => ({ date: a.date, count: a.count, z_score: a.z_score, direction: a.direction })),
      'anomaly-detection',
    )
  }, [anomalies])

  return (
    <ChartPanel title={labels.anomalyDetection} loading={loading} error={error} onExportPng={handleExportPng} onExportCsv={handleExportCsv}>
      <div className="grid grid-cols-3 gap-3 mb-4">
        <Card className="bg-card border-border">
          <CardContent className="p-3">
            <p className="text-xs text-muted-foreground uppercase tracking-wider">
              Daily Mean
            </p>
            <p className="text-lg font-bold text-foreground">{mean.toFixed(1)}</p>
          </CardContent>
        </Card>
        <Card className="bg-card border-border">
          <CardContent className="p-3">
            <p className="text-xs text-muted-foreground uppercase tracking-wider">
              Std Dev
            </p>
            <p className="text-lg font-bold text-foreground">{std.toFixed(1)}</p>
          </CardContent>
        </Card>
        <Card className="bg-card border-border">
          <CardContent className="p-3">
            <p className="text-xs text-muted-foreground uppercase tracking-wider">
              Anomalies
            </p>
            <p className="text-lg font-bold">
              <span className="text-red-500">{highAnomalies.length} high</span>
              {' / '}
              <span className="text-blue-400">{lowAnomalies.length} low</span>
            </p>
            <p className="text-xs text-muted-foreground">{totalDays} {labels.days} analyzed</p>
          </CardContent>
        </Card>
      </div>
      {anomalies.length > 0 && (
        <ReactECharts option={option} style={{ height: 200 }} onChartReady={(instance) => setChartInstance(instance)} />
      )}
      {anomalies.length === 0 && totalDays > 0 && (
        <p className="text-sm text-muted-foreground text-center py-8">
          No anomalies detected at threshold {data?.threshold ?? 2.0}
        </p>
      )}
    </ChartPanel>
  )
}
