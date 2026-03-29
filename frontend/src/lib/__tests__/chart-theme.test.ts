import { describe, it, expect } from 'vitest'
import { getChartColors, getChartGrid } from '../chart-theme'

describe('getChartColors', () => {
  it('should return dark colors when dark=true', () => {
    const colors = getChartColors(true)
    expect(colors.axisLabel).toBe('#9ca3af')
    expect(colors.splitLine).toBe('#1f2937')
  })

  it('should return light colors when dark=false', () => {
    const colors = getChartColors(false)
    expect(colors.axisLabel).toBe('#4b5563')
    expect(colors.splitLine).toBe('#e5e7eb')
  })

  it('should have all required color properties', () => {
    const colors = getChartColors(true)
    const keys = ['axisLabel', 'axisLine', 'splitLine', 'labelPrimary', 'tooltipBg', 'tooltipBorder', 'visualMapText', 'heatmapLow']
    for (const key of keys) {
      expect(colors).toHaveProperty(key)
      expect(typeof colors[key as keyof typeof colors]).toBe('string')
    }
  })
})

describe('getChartGrid', () => {
  it('should return LTR grid with start=left', () => {
    const grid = getChartGrid('ltr', { start: 50, end: 20, top: 10, bottom: 30 })
    expect(grid.left).toBe(50)
    expect(grid.right).toBe(20)
  })

  it('should swap left/right for RTL', () => {
    const grid = getChartGrid('rtl', { start: 50, end: 20, top: 10, bottom: 30 })
    expect(grid.left).toBe(20)
    expect(grid.right).toBe(50)
  })

  it('should preserve top and bottom', () => {
    const grid = getChartGrid('ltr', { start: 50, end: 20, top: 10, bottom: 30 })
    expect(grid.top).toBe(10)
    expect(grid.bottom).toBe(30)
  })
})
