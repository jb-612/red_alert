import type { ECharts } from 'echarts'

export function exportPng(instance: ECharts, filename: string): void {
  const url = instance.getDataURL({ type: 'png', pixelRatio: 2, backgroundColor: '#fff' })
  const link = document.createElement('a')
  link.href = url
  link.download = `${filename}.png`
  link.click()
}

export function exportCsv(data: Record<string, unknown>[], filename: string): void {
  if (data.length === 0) return
  const headers = Object.keys(data[0])
  const bom = '\uFEFF'
  const rows = data.map((row) =>
    headers.map((h) => {
      const val = row[h]
      if (typeof val === 'string') return `"${val.replace(/"/g, '""')}"`
      return String(val ?? '')
    }).join(','),
  )
  const csv = bom + [headers.join(','), ...rows].join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${filename}.csv`
  link.click()
  URL.revokeObjectURL(url)
}
