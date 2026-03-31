import { useState, useCallback, useEffect } from 'react'
import ReactECharts from 'echarts-for-react'
import type { EChartsOption, ECharts } from 'echarts'
import { Card, CardContent } from '@/components/ui/card'
import { acledApi } from '@/api/acledClient'
import type { AcledAnomalyResponse } from '@/api/acledClient'
import { useAcledFilterStore } from '@/store/acledFilters'
import { useThemeStore } from '@/store/theme'
import { getChartColors } from '@/lib/chart-theme'
import { useLabels } from '@/lib/labels'
import { exportPng, exportCsv } from '@/lib/export'
import { ChartPanel } from '@/components/charts/ChartPanel'

export function ConflictAnomalies() {
  const dark = useThemeStore((s) => s.dark)
  const colors = getChartColors(dark)
  const labels = useLabels()
  const [chartInstance, setChartInstance] = useState<ECharts | null>(null)
  const [threshold, setThreshold] = useState(2.0)
  const [data, setData] = useState<AcledAnomalyResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const { dateRange, countries, eventTypes, theaters, actor, granularity } = useAcledFilterStore()

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    acledApi.getAcledAnomalies(threshold)
      .then((result) => { if (!cancelled) { setData(result); setLoading(false) } })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Unknown error')
          setLoading(false)
        }
      })
    return () => { cancelled = true }
  }, [dateRange.from, dateRange.to, countries, eventTypes, theaters, actor, granularity, threshold])

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
        const p = params as { name: string; value: number; data: { z: number; dir: string; fat: number } }
        return `${p.name}<br/>${p.value} ${labels.events} (z=${p.data.z}, ${p.data.dir})<br/>${p.data.fat} ${labels.fatalities}`
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
          fat: a.fatalities,
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
    if (chartInstance) exportPng(chartInstance, 'conflict-anomalies')
  }, [chartInstance])

  const handleExportCsv = useCallback(() => {
    exportCsv(
      anomalies.map((a) => ({ date: a.date, count: a.count, fatalities: a.fatalities, z_score: a.z_score, direction: a.direction })),
      'conflict-anomalies',
    )
  }, [anomalies])

  return (
    <ChartPanel title={labels.anomalyDetection} loading={loading} error={error} onExportPng={handleExportPng} onExportCsv={handleExportCsv}>
      {/* Threshold slider */}
      <div className="flex items-center justify-end mb-3">
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">Sensitivity:</span>
          <input
            type="range"
            min="1"
            max="4"
            step="0.5"
            value={threshold}
            onChange={(e) => setThreshold(Number(e.target.value))}
            className="w-20 h-1.5 accent-red-500"
          />
          <span className="text-xs font-mono text-foreground w-6">{threshold}</span>
        </div>
      </div>

      {/* Metric cards */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        <Card className="bg-card border-border">
          <CardContent className="p-3">
            <p className="text-xs text-muted-foreground uppercase tracking-wider">Daily Mean</p>
            <p className="text-lg font-bold text-foreground">{mean.toFixed(1)}</p>
          </CardContent>
        </Card>
        <Card className="bg-card border-border">
          <CardContent className="p-3">
            <p className="text-xs text-muted-foreground uppercase tracking-wider">Std Dev</p>
            <p className="text-lg font-bold text-foreground">{std.toFixed(1)}</p>
          </CardContent>
        </Card>
        <Card className="bg-card border-border">
          <CardContent className="p-3">
            <p className="text-xs text-muted-foreground uppercase tracking-wider">Anomalies</p>
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
          No anomalies detected at threshold {threshold}
        </p>
      )}
    </ChartPanel>
  )
}
