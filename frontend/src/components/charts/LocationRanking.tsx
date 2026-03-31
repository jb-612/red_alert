import { useState, useCallback, useEffect } from 'react'
import ReactECharts from 'echarts-for-react'
import type { EChartsOption, ECharts } from 'echarts'
import { ArrowUpDown } from 'lucide-react'
import { api } from '@/api/client'
import type { LocationCount } from '@/api/client'
import { useFilterStore } from '@/store/filters'
import { useThemeStore } from '@/store/theme'
import { getChartColors } from '@/lib/chart-theme'
import { useLabels } from '@/lib/labels'
import { exportPng, exportCsv } from '@/lib/export'
import { ChartPanel } from './ChartPanel'

export function LocationRanking() {
  const dark = useThemeStore((s) => s.dark)
  const colors = getChartColors(dark)
  const labels = useLabels()
  const [chartInstance, setChartInstance] = useState<ECharts | null>(null)
  const [sortOrder, setSortOrder] = useState<'desc' | 'asc'>('desc')
  const [data, setData] = useState<LocationCount[] | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const { dateRange, categories, location, granularity, region } = useFilterStore()

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    api.getLocationsByCount(10, sortOrder)
      .then((result) => { if (!cancelled) { setData(result); setLoading(false) } })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Unknown error')
          setLoading(false)
        }
      })
    return () => { cancelled = true }
  }, [dateRange.from, dateRange.to, categories, location, granularity, region, sortOrder])

  const locations = data ?? []
  const sorted = [...locations].reverse()

  const option: EChartsOption = {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    xAxis: {
      type: 'value',
      axisLabel: { color: colors.axisLabel },
      splitLine: { lineStyle: { color: colors.splitLine } },
    },
    yAxis: {
      type: 'category',
      data: sorted.map((l) => l.location_name),
      axisLabel: { color: colors.labelPrimary, fontSize: 12 },
      axisLine: { lineStyle: { color: colors.axisLine } },
    },
    series: [
      {
        type: 'bar',
        data: sorted.map((l) => l.count),
        itemStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 1, y2: 0,
            colorStops: [
              { offset: 0, color: sortOrder === 'desc' ? '#ef4444' : '#22c55e' },
              { offset: 1, color: sortOrder === 'desc' ? '#f97316' : '#06b6d4' },
            ],
          },
          borderRadius: [0, 4, 4, 0],
        },
        barMaxWidth: 20,
      },
    ],
    grid: { left: 80, right: 30, top: 10, bottom: 20 },
  }

  const handleExportPng = useCallback(() => {
    if (chartInstance) exportPng(chartInstance, 'top-locations')
  }, [chartInstance])

  const handleExportCsv = useCallback(() => {
    exportCsv(
      locations.map((l) => ({ location: l.location_name, count: l.count })),
      'top-locations',
    )
  }, [locations])

  return (
    <ChartPanel title={labels.topLocations} loading={loading} error={error} onExportPng={handleExportPng} onExportCsv={handleExportCsv}>
      <div className="flex justify-end mb-2">
        <button
          onClick={() => setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc')}
          className="flex items-center gap-1.5 rounded px-2 py-1 text-xs text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
        >
          <ArrowUpDown className="h-3 w-3" />
          {sortOrder === 'desc' ? 'Most alerts' : 'Least alerts'}
        </button>
      </div>
      <ReactECharts option={option} style={{ height: 300 }} onChartReady={(instance) => setChartInstance(instance)} />
    </ChartPanel>
  )
}
