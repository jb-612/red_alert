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

const WINDOW_OPTIONS = [5, 10, 15, 30, 60]

export function PrealertCorrelation() {
  const [windowMinutes, setWindowMinutes] = useState(30)
  const { data, loading, error } = useApiData(
    () => api.getPrealertCorrelation(windowMinutes),
  )
  const dark = useThemeStore((s) => s.dark)
  const colors = getChartColors(dark)
  const labels = useLabels()
  const [chartInstance, setChartInstance] = useState<ECharts | null>(null)

  const locations = data?.locations ?? []
  const overallPct = ((data?.overall_probability ?? 0) * 100).toFixed(1)

  const sorted = [...locations].reverse()

  const option: EChartsOption = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params: unknown) => {
        const p = (params as { name: string; value: number; data: { fol: number; tot: number } }[])[0]
        return `${p.name}<br/>${(p.value * 100).toFixed(1)}% (${p.data.fol}/${p.data.tot})`
      },
    },
    xAxis: {
      type: 'value',
      min: 0,
      max: 1,
      axisLabel: { color: colors.axisLabel, formatter: (v: number) => `${(v * 100).toFixed(0)}%` },
      splitLine: { lineStyle: { color: colors.splitLine } },
    },
    yAxis: {
      type: 'category',
      data: sorted.map((l) => l.location_name),
      axisLabel: { color: colors.labelPrimary, fontSize: 11 },
      axisLine: { lineStyle: { color: colors.axisLine } },
    },
    series: [
      {
        type: 'bar',
        data: sorted.map((l) => ({
          value: l.probability,
          fol: l.followed_by_actual,
          tot: l.total_prealerts,
          itemStyle: {
            color: l.probability > 0.7
              ? '#ef4444'
              : l.probability > 0.4
                ? '#f59e0b'
                : '#10b981',
          },
        })),
        barMaxWidth: 18,
        itemStyle: { borderRadius: [0, 4, 4, 0] },
      },
    ],
    grid: { left: 100, right: 20, top: 10, bottom: 20 },
  }

  const handleExportPng = useCallback(() => {
    if (chartInstance) exportPng(chartInstance, 'prealert-correlation')
  }, [chartInstance])

  const handleExportCsv = useCallback(() => {
    exportCsv(
      locations.map((l) => ({
        location: l.location_name,
        total_prealerts: l.total_prealerts,
        followed_by_actual: l.followed_by_actual,
        probability: l.probability,
      })),
      'prealert-correlation',
    )
  }, [locations])

  return (
    <ChartPanel
      title={labels.prealertCorrelation}
      loading={loading}
      error={error}
      onExportPng={handleExportPng}
      onExportCsv={handleExportCsv}
    >
      <div className="flex items-center gap-4 mb-4">
        <Card className="bg-card border-border flex-1">
          <CardContent className="p-3">
            <p className="text-xs text-muted-foreground uppercase tracking-wider">
              Overall Probability
            </p>
            <p className="text-3xl font-bold text-orange-500">{overallPct}%</p>
            <p className="text-xs text-muted-foreground">
              {data?.overall_followed ?? 0} / {data?.overall_total_prealerts ?? 0} pre-alerts
            </p>
          </CardContent>
        </Card>
        <div className="flex flex-col gap-1">
          <p className="text-xs text-muted-foreground uppercase tracking-wider">
            Window
          </p>
          <div className="flex gap-1">
            {WINDOW_OPTIONS.map((w) => (
              <button
                key={w}
                onClick={() => setWindowMinutes(w)}
                className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
                  windowMinutes === w
                    ? 'bg-orange-600 text-white'
                    : 'bg-muted text-muted-foreground hover:bg-muted/80'
                }`}
              >
                {w}m
              </button>
            ))}
          </div>
        </div>
      </div>
      {locations.length > 0 && (
        <ReactECharts
          option={option}
          style={{ height: Math.max(150, sorted.length * 30) }}
          onChartReady={(instance) => setChartInstance(instance)}
        />
      )}
      {locations.length === 0 && !loading && (
        <p className="text-sm text-muted-foreground text-center py-4">
          No locations with enough pre-alerts
        </p>
      )}
    </ChartPanel>
  )
}
