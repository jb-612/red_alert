import ReactECharts from 'echarts-for-react'
import type { EChartsOption } from 'echarts'
import type { PulseBucket } from '@/api/acledPulseClient'
import { useThemeStore } from '@/store/theme'
import { getChartColors } from '@/lib/chart-theme'

interface Props {
  timeline: PulseBucket[]
  granularity: 'day' | 'month'
}

export function GlobalTimelineChart({ timeline, granularity }: Props) {
  const dark = useThemeStore((s) => s.dark)
  const colors = getChartColors(dark)

  const option: EChartsOption = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
    },
    legend: {
      data: ['Events', 'Fatalities'],
      textStyle: { color: colors.axisLabel },
      top: 4,
    },
    grid: { left: 60, right: 60, top: 40, bottom: 40 },
    xAxis: {
      type: 'category',
      data: timeline.map((b) => b.date),
      axisLabel: {
        color: colors.axisLabel,
        fontSize: 10,
        rotate: granularity === 'day' ? 40 : 0,
      },
      axisLine: { lineStyle: { color: colors.axisLine } },
    },
    yAxis: [
      {
        type: 'value',
        name: 'Events',
        nameTextStyle: { color: colors.axisLabel, fontSize: 11 },
        axisLabel: { color: colors.axisLabel },
        splitLine: { lineStyle: { color: colors.splitLine } },
      },
      {
        type: 'value',
        name: 'Fatalities',
        nameTextStyle: { color: colors.axisLabel, fontSize: 11 },
        position: 'right',
        axisLabel: { color: colors.axisLabel },
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: 'Events',
        type: 'bar',
        yAxisIndex: 0,
        data: timeline.map((b) => b.events),
        itemStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: '#f97316' },
              { offset: 1, color: '#b45309' },
            ],
          },
        },
      },
      {
        name: 'Fatalities',
        type: 'line',
        yAxisIndex: 1,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        data: timeline.map((b) => b.fatalities),
        lineStyle: { color: '#ef4444', width: 2 },
        itemStyle: { color: '#ef4444' },
        areaStyle: { color: 'rgba(239, 68, 68, 0.08)' },
      },
    ],
  }

  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <h3 className="text-sm font-semibold text-foreground mb-2">
        Global timeline ({granularity === 'day' ? 'daily' : 'monthly'} buckets)
      </h3>
      <ReactECharts option={option} style={{ height: 320 }} />
    </div>
  )
}
