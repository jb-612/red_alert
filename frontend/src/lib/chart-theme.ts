export interface ChartColors {
  axisLabel: string
  axisLine: string
  splitLine: string
  labelPrimary: string
  tooltipBg: string
  tooltipBorder: string
  visualMapText: string
  heatmapLow: string
}

const darkColors: ChartColors = {
  axisLabel: '#9ca3af',
  axisLine: '#374151',
  splitLine: '#1f2937',
  labelPrimary: '#d1d5db',
  tooltipBg: '#1f2937',
  tooltipBorder: '#374151',
  visualMapText: '#9ca3af',
  heatmapLow: '#1a1a2e',
}

const lightColors: ChartColors = {
  axisLabel: '#4b5563',
  axisLine: '#d1d5db',
  splitLine: '#e5e7eb',
  labelPrimary: '#374151',
  tooltipBg: '#ffffff',
  tooltipBorder: '#e5e7eb',
  visualMapText: '#6b7280',
  heatmapLow: '#fef3c7',
}

export function getChartColors(dark: boolean): ChartColors {
  return dark ? darkColors : lightColors
}

export function getChartGrid(dir: string, margins: { start: number; end: number; top: number; bottom: number }) {
  const isRtl = dir === 'rtl'
  return {
    left: isRtl ? margins.end : margins.start,
    right: isRtl ? margins.start : margins.end,
    top: margins.top,
    bottom: margins.bottom,
    containLabel: false,
  }
}
