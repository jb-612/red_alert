import { useEffect, useState, useCallback } from 'react'
import ReactECharts from 'echarts-for-react'
import type { EChartsOption, ECharts } from 'echarts'
import { Card, CardContent } from '@/components/ui/card'
import { api } from '@/api/client'
import type { ComparisonData } from '@/api/client'
import { useFilterStore } from '@/store/filters'
import { useThemeStore } from '@/store/theme'
import { getChartColors } from '@/lib/chart-theme'
import { useLabels } from '@/lib/labels'
import { exportPng, exportCsv } from '@/lib/export'
import { ChartPanel } from './ChartPanel'

function DeltaArrow({ value }: { value: number }) {
  if (value > 0) return <span className="text-red-500">+{value}%</span>
  if (value < 0) return <span className="text-emerald-500">{value}%</span>
  return <span className="text-muted-foreground">0%</span>
}

export function PeriodComparison() {
  const { dateRange, comparisonRange, categories, location } = useFilterStore()
  const dark = useThemeStore((s) => s.dark)
  const colors = getChartColors(dark)
  const labels = useLabels()
  const [data, setData] = useState<ComparisonData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [chartInstance, setChartInstance] = useState<ECharts | null>(null)

  useEffect(() => {
    if (!dateRange.from || !dateRange.to || !comparisonRange.from || !comparisonRange.to) {
      setData(null)
      return
    }

    let cancelled = false
    setLoading(true)
    setError(null)

    api
      .getComparison(dateRange.from, dateRange.to, comparisonRange.from, comparisonRange.to)
      .then((result) => {
        if (!cancelled) { setData(result); setLoading(false) }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Unknown error')
          setLoading(false)
        }
      })

    return () => { cancelled = true }
  }, [dateRange.from, dateRange.to, comparisonRange.from, comparisonRange.to, categories, location])

  const a = data?.period_a
  const b = data?.period_b
  const delta = data?.delta

  const handleExportPng = useCallback(() => {
    if (chartInstance) exportPng(chartInstance, 'period-comparison')
  }, [chartInstance])

  const handleExportCsv = useCallback(() => {
    const rows: Record<string, unknown>[] = []
    for (const t of a?.timeline ?? []) {
      rows.push({ period: t.period, period_a_count: t.count, period_b_count: '' })
    }
    for (const t of b?.timeline ?? []) {
      const existing = rows.find((r) => r.period === t.period)
      if (existing) {
        existing.period_b_count = t.count
      } else {
        rows.push({ period: t.period, period_a_count: '', period_b_count: t.count })
      }
    }
    exportCsv(rows, 'period-comparison')
  }, [a, b])

  if (!dateRange.from || !dateRange.to || !comparisonRange.from || !comparisonRange.to) {
    return (
      <ChartPanel title={labels.periodComparison} loading={false} error={null}>
        <p className="text-sm text-muted-foreground text-center py-8">
          Select both date ranges to compare
        </p>
      </ChartPanel>
    )
  }

  const timelineOption: EChartsOption = {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis' },
    legend: {
      data: ['Period A', 'Period B'],
      textStyle: { color: colors.axisLabel },
      top: 0,
    },
    xAxis: {
      type: 'category',
      data: [
        ...(a?.timeline.map((t) => t.period) ?? []),
        ...(b?.timeline.map((t) => t.period) ?? []),
      ].filter((v, i, arr) => arr.indexOf(v) === i).sort(),
      axisLabel: { color: colors.axisLabel, fontSize: 10 },
      axisLine: { lineStyle: { color: colors.axisLine } },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: colors.axisLabel },
      splitLine: { lineStyle: { color: colors.splitLine } },
    },
    series: [
      {
        name: 'Period A',
        type: 'line',
        data: a?.timeline.map((t) => [t.period, t.count]) ?? [],
        lineStyle: { color: '#ef4444', width: 2 },
        itemStyle: { color: '#ef4444' },
        symbol: 'circle',
        symbolSize: 4,
      },
      {
        name: 'Period B',
        type: 'line',
        data: b?.timeline.map((t) => [t.period, t.count]) ?? [],
        lineStyle: { color: '#3b82f6', width: 2, type: 'dashed' },
        itemStyle: { color: '#3b82f6' },
        symbol: 'diamond',
        symbolSize: 4,
      },
    ],
    grid: { left: 50, right: 20, top: 30, bottom: 30 },
  }

  return (
    <ChartPanel title={labels.periodComparison} loading={loading} error={error} onExportPng={handleExportPng} onExportCsv={handleExportCsv}>
      {data && (
        <>
          <div className="grid grid-cols-3 gap-3 mb-4">
            <Card className="bg-card border-border">
              <CardContent className="p-3">
                <p className="text-xs text-muted-foreground uppercase tracking-wider">
                  Period A Alerts
                </p>
                <p className="text-xl font-bold text-red-500">
                  {a?.total_alerts.toLocaleString()}
                </p>
              </CardContent>
            </Card>
            <Card className="bg-card border-border">
              <CardContent className="p-3">
                <p className="text-xs text-muted-foreground uppercase tracking-wider">
                  Period B Alerts
                </p>
                <p className="text-xl font-bold text-blue-400">
                  {b?.total_alerts.toLocaleString()}
                </p>
              </CardContent>
            </Card>
            <Card className="bg-card border-border">
              <CardContent className="p-3">
                <p className="text-xs text-muted-foreground uppercase tracking-wider">
                  Change
                </p>
                <p className="text-xl font-bold">
                  {delta?.total_alerts_pct != null ? (
                    <DeltaArrow value={delta.total_alerts_pct} />
                  ) : (
                    <span className="text-muted-foreground">&mdash;</span>
                  )}
                </p>
                <p className="text-xs text-muted-foreground">
                  {delta && delta.total_alerts_delta > 0 ? '+' : ''}
                  {delta?.total_alerts_delta} {labels.alerts}
                </p>
              </CardContent>
            </Card>
          </div>
          <ReactECharts option={timelineOption} style={{ height: 200 }} onChartReady={(instance) => setChartInstance(instance)} />
        </>
      )}
    </ChartPanel>
  )
}
