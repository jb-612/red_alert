import { useState, useCallback, useMemo } from 'react'
import ReactECharts from 'echarts-for-react'
import type { EChartsOption, ECharts } from 'echarts'
import { acledApi } from '@/api/acledClient'
import type { AcledCountryMatrixEntry } from '@/api/acledClient'
import { useAcledData } from '@/hooks/useAcledData'
import { useAcledFilterStore } from '@/store/acledFilters'
import { useThemeStore } from '@/store/theme'
import { getChartColors } from '@/lib/chart-theme'
import { useLabels } from '@/lib/labels'
import { exportPng, exportCsv } from '@/lib/export'
import { ChartPanel } from '@/components/charts/ChartPanel'

type SortKey = 'country' | 'events' | 'fatalities'

function getTotals(entry: AcledCountryMatrixEntry) {
  let events = 0
  let fatalities = 0
  for (const cell of Object.values(entry.event_types)) {
    events += cell.count
    fatalities += cell.fatalities
  }
  return { events, fatalities }
}

function getDominantType(entry: AcledCountryMatrixEntry): string {
  let maxType = ''
  let maxCount = 0
  for (const [type, cell] of Object.entries(entry.event_types)) {
    if (cell.count > maxCount) {
      maxCount = cell.count
      maxType = type
    }
  }
  return maxType
}

export function CountryIntelligence() {
  const { data, loading, error } = useAcledData(() => acledApi.getCountryMatrix())
  const dark = useThemeStore((s) => s.dark)
  const colors = getChartColors(dark)
  const labels = useLabels()
  const [chartInstance, setChartInstance] = useState<ECharts | null>(null)
  const [sortKey, setSortKey] = useState<SortKey>('events')
  const [sortAsc, setSortAsc] = useState(false)

  const matrix = data?.matrix ?? []

  const sorted = useMemo(() => {
    return [...matrix].sort((a, b) => {
      if (sortKey === 'country') {
        const diff = a.country.localeCompare(b.country)
        return sortAsc ? diff : -diff
      }
      const aT = getTotals(a)
      const bT = getTotals(b)
      const diff = sortKey === 'events' ? aT.events - bT.events : aT.fatalities - bT.fatalities
      return sortAsc ? diff : -diff
    })
  }, [matrix, sortKey, sortAsc])

  // Gather all event types for heatmap
  const allEventTypes = useMemo(() => {
    const types = new Set<string>()
    for (const entry of matrix) {
      for (const t of Object.keys(entry.event_types)) {
        types.add(t)
      }
    }
    return Array.from(types).sort()
  }, [matrix])

  function handleSort(key: SortKey) {
    if (sortKey === key) {
      setSortAsc(!sortAsc)
    } else {
      setSortKey(key)
      setSortAsc(false)
    }
  }

  function handleCountryClick(country: string) {
    useAcledFilterStore.getState().setCountries([country])
  }

  function sortIndicator(key: SortKey) {
    if (sortKey !== key) return ''
    return sortAsc ? ' \u2191' : ' \u2193'
  }

  // Build heatmap data
  const heatmapData: [number, number, number][] = []
  const countryList = sorted.map((e) => e.country)

  for (let yi = 0; yi < sorted.length; yi++) {
    for (let xi = 0; xi < allEventTypes.length; xi++) {
      const cell = sorted[yi].event_types[allEventTypes[xi]]
      heatmapData.push([xi, yi, cell?.count ?? 0])
    }
  }

  const maxVal = Math.max(1, ...heatmapData.map((d) => d[2]))

  const heatmapOption: EChartsOption = {
    backgroundColor: 'transparent',
    tooltip: {
      position: 'top',
      formatter: (params: unknown) => {
        const p = params as { data: [number, number, number] }
        return `${countryList[p.data[1]]} / ${allEventTypes[p.data[0]]}: ${p.data[2]}`
      },
    },
    xAxis: {
      type: 'category',
      data: allEventTypes,
      axisLabel: { color: colors.axisLabel, fontSize: 10, rotate: 30 },
      splitArea: { show: true },
    },
    yAxis: {
      type: 'category',
      data: countryList,
      axisLabel: { color: colors.labelPrimary, fontSize: 11 },
    },
    visualMap: {
      min: 0,
      max: maxVal,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: 0,
      textStyle: { color: colors.visualMapText },
      inRange: {
        color: [colors.heatmapLow, '#f59e0b', '#ef4444'],
      },
    },
    series: [
      {
        type: 'heatmap',
        data: heatmapData,
        label: { show: false },
        emphasis: {
          itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0, 0, 0, 0.5)' },
        },
      },
    ],
    grid: { left: 100, right: 20, top: 10, bottom: 80 },
  }

  const handleExportPng = useCallback(() => {
    if (chartInstance) exportPng(chartInstance, 'country-intelligence')
  }, [chartInstance])

  const handleExportCsv = useCallback(() => {
    exportCsv(
      sorted.map((e) => {
        const t = getTotals(e)
        return { country: e.country, events: t.events, fatalities: t.fatalities, dominant_type: getDominantType(e) }
      }),
      'country-intelligence',
    )
  }, [sorted])

  return (
    <ChartPanel title={labels.countryIntel} loading={loading} error={error} onExportPng={handleExportPng} onExportCsv={handleExportCsv}>
      {/* Table */}
      <div className="overflow-auto max-h-[300px] mb-4">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-card">
            <tr className="border-b border-border text-left">
              <th
                className="py-2 px-2 text-xs text-muted-foreground font-semibold cursor-pointer hover:text-foreground"
                onClick={() => handleSort('country')}
              >
                {labels.countries}{sortIndicator('country')}
              </th>
              <th
                className="py-2 px-2 text-xs text-muted-foreground font-semibold cursor-pointer hover:text-foreground"
                onClick={() => handleSort('events')}
              >
                {labels.events}{sortIndicator('events')}
              </th>
              <th
                className="py-2 px-2 text-xs text-muted-foreground font-semibold cursor-pointer hover:text-foreground"
                onClick={() => handleSort('fatalities')}
              >
                {labels.fatalities}{sortIndicator('fatalities')}
              </th>
              <th className="py-2 px-2 text-xs text-muted-foreground font-semibold">
                {labels.dominantType}
              </th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((entry) => {
              const t = getTotals(entry)
              return (
                <tr
                  key={entry.country}
                  onClick={() => handleCountryClick(entry.country)}
                  className="border-b border-border/50 cursor-pointer hover:bg-muted/50 transition-colors"
                >
                  <td className="py-2 px-2 text-foreground font-medium">{entry.country}</td>
                  <td className="py-2 px-2 text-foreground">{t.events.toLocaleString()}</td>
                  <td className="py-2 px-2 text-foreground">{t.fatalities.toLocaleString()}</td>
                  <td className="py-2 px-2 text-muted-foreground text-xs">{getDominantType(entry)}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Heatmap */}
      {matrix.length > 0 && (
        <ReactECharts
          option={heatmapOption}
          style={{ height: Math.max(250, countryList.length * 28) }}
          onChartReady={(instance) => setChartInstance(instance)}
        />
      )}

      {matrix.length === 0 && (
        <p className="text-sm text-muted-foreground text-center py-8">{labels.noData}</p>
      )}
    </ChartPanel>
  )
}
