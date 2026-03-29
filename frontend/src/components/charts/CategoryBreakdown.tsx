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

const CATEGORY_COLORS: Record<string, string> = {
  'Rockets': '#ef4444',
  '\u05E8\u05E7\u05D8\u05D5\u05EA': '#ef4444',
  'UAV': '#f97316',
  '\u05DB\u05DC\u05D9 \u05D8\u05D9\u05E1 \u05E2\u05D5\u05D9\u05DF': '#f97316',
  'Infiltration': '#eab308',
  '\u05D7\u05D3\u05D9\u05E8\u05EA \u05DE\u05D7\u05D1\u05DC\u05D9\u05DD': '#eab308',
  'All Clear': '#22c55e',
  '\u05D9\u05E8\u05D9 \u05E0"\u05D8': '#22c55e',
  'Earthquake': '#6b7280',
  '\u05E8\u05E2\u05D9\u05D3\u05EA \u05D0\u05D3\u05DE\u05D4': '#6b7280',
}

function getColor(desc: string, index: number): string {
  for (const [key, color] of Object.entries(CATEGORY_COLORS)) {
    if (desc.includes(key)) return color
  }
  const fallback = ['#ef4444', '#f97316', '#eab308', '#22c55e', '#6b7280', '#8b5cf6', '#06b6d4']
  return fallback[index % fallback.length]
}

export function CategoryBreakdown() {
  const { data, loading, error } = useApiData(() => api.getCategories())
  const dark = useThemeStore((s) => s.dark)
  const colors = getChartColors(dark)
  const labels = useLabels()
  const [chartInstance, setChartInstance] = useState<ECharts | null>(null)

  const categories = data ?? []

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
        data: categories.map((d, i) => ({
          name: d.category_desc || `Category ${d.category}`,
          value: d.count,
          itemStyle: { color: getColor(d.category_desc, i) },
        })),
      },
    ],
  }

  const handleExportPng = useCallback(() => {
    if (chartInstance) exportPng(chartInstance, 'category-breakdown')
  }, [chartInstance])

  const handleExportCsv = useCallback(() => {
    exportCsv(
      categories.map((d) => ({ category: d.category, description: d.category_desc, count: d.count })),
      'category-breakdown',
    )
  }, [categories])

  return (
    <ChartPanel title={labels.categoryBreakdown} loading={loading} error={error} onExportPng={handleExportPng} onExportCsv={handleExportCsv}>
      <ReactECharts option={option} style={{ height: 280 }} onChartReady={(instance) => setChartInstance(instance)} />
    </ChartPanel>
  )
}
