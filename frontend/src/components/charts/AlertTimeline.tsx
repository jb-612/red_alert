import { useState, useCallback, useRef } from 'react'
import ReactECharts from 'echarts-for-react'
import type { EChartsOption, ECharts } from 'echarts'
import { api } from '@/api/client'
import { useApiData } from '@/hooks/useApiData'
import { useFilterStore } from '@/store/filters'
import { useThemeStore } from '@/store/theme'
import { getChartColors } from '@/lib/chart-theme'
import { useLabels } from '@/lib/labels'
import { exportPng, exportCsv } from '@/lib/export'
import { ChartPanel } from './ChartPanel'

export function AlertTimeline() {
  const { data, loading, error } = useApiData(() => api.getTimeline())
  const dark = useThemeStore((s) => s.dark)
  const colors = getChartColors(dark)
  const labels = useLabels()
  const [chartInstance, setChartInstance] = useState<ECharts | null>(null)
  const debounceTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const buckets = data?.buckets ?? []

  const handleDataZoom = useCallback(() => {
    if (debounceTimer.current) clearTimeout(debounceTimer.current)
    debounceTimer.current = setTimeout(() => {
      if (!chartInstance || buckets.length === 0) return
      const option = chartInstance.getOption() as { dataZoom?: Array<{ startValue?: number; endValue?: number }> }
      const zoom = option.dataZoom?.[0]
      if (zoom?.startValue != null && zoom?.endValue != null) {
        const startIdx = Math.max(0, Math.min(zoom.startValue, buckets.length - 1))
        const endIdx = Math.max(0, Math.min(zoom.endValue, buckets.length - 1))
        const fromDate = buckets[startIdx]?.period
        const toDate = buckets[endIdx]?.period
        if (fromDate && toDate) {
          useFilterStore.getState().setDateRange(fromDate, toDate)
        }
      }
    }, 500)
  }, [chartInstance, buckets])

  const option: EChartsOption = {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: buckets.map((b) => b.period),
      axisLabel: { color: colors.axisLabel, fontSize: 10 },
      axisLine: { lineStyle: { color: colors.axisLine } },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: colors.axisLabel },
      splitLine: { lineStyle: { color: colors.splitLine } },
    },
    dataZoom: [
      { type: 'inside', start: 0, end: 100 },
      { type: 'slider', start: 0, end: 100, height: 20, bottom: 8 },
    ],
    series: [
      {
        type: 'bar',
        data: buckets.map((b) => b.count),
        itemStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: '#ef4444' },
              { offset: 1, color: '#f97316' },
            ],
          },
        },
      },
    ],
    grid: { left: 50, right: 20, top: 20, bottom: 50 },
  }

  const handleExportPng = useCallback(() => {
    if (chartInstance) exportPng(chartInstance, 'alert-timeline')
  }, [chartInstance])

  const handleExportCsv = useCallback(() => {
    exportCsv(
      buckets.map((b) => ({ period: b.period, count: b.count })),
      'alert-timeline',
    )
  }, [buckets])

  return (
    <ChartPanel title={labels.alertTimeline} loading={loading} error={error} onExportPng={handleExportPng} onExportCsv={handleExportCsv}>
      <ReactECharts
        option={option}
        style={{ height: 280 }}
        onChartReady={(instance) => setChartInstance(instance)}
        onEvents={{ datazoom: handleDataZoom }}
      />
    </ChartPanel>
  )
}
