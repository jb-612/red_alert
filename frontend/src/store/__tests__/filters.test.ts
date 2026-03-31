import { describe, it, expect, beforeEach } from 'vitest'
import { useFilterStore } from '../filters'

// Helper: test that a string matches YYYY-MM-DD format
function isValidDateString(s: unknown): s is string {
  if (typeof s !== 'string') return false
  return /^\d{4}-\d{2}-\d{2}$/.test(s) && !isNaN(Date.parse(s))
}

// Helper: difference in calendar days between two YYYY-MM-DD strings
function daysDiff(a: string, b: string): number {
  const msPerDay = 1000 * 60 * 60 * 24
  return Math.abs(Date.parse(b) - Date.parse(a)) / msPerDay
}

// Capture the initial state at module load time (before any beforeEach resets)
const INITIAL_DATE_RANGE = { ...useFilterStore.getState().dateRange }

describe('useFilterStore — default date range', () => {
  // These tests check the store's module-level initialization defaults,
  // captured in INITIAL_DATE_RANGE before any test manipulation.

  it('dateRange.from is not null on fresh store initialisation', () => {
    expect(INITIAL_DATE_RANGE.from).not.toBeNull()
  })

  it('dateRange.to is not null on fresh store initialisation', () => {
    expect(INITIAL_DATE_RANGE.to).not.toBeNull()
  })

  it('dateRange.from is a valid YYYY-MM-DD string', () => {
    expect(isValidDateString(INITIAL_DATE_RANGE.from)).toBe(true)
  })

  it('dateRange.to is a valid YYYY-MM-DD string', () => {
    expect(isValidDateString(INITIAL_DATE_RANGE.to)).toBe(true)
  })

  it('dateRange.from is approximately 6 months before dateRange.to (within 5 days)', () => {
    expect(typeof INITIAL_DATE_RANGE.from).toBe('string')
    expect(typeof INITIAL_DATE_RANGE.to).toBe('string')

    const diff = daysDiff(INITIAL_DATE_RANGE.from as string, INITIAL_DATE_RANGE.to as string)
    // 6 months ≈ 180 days — allow ±5 days tolerance for month-length variation
    expect(diff).toBeGreaterThanOrEqual(175)
    expect(diff).toBeLessThanOrEqual(185)
  })

  it('dateRange.to is on or very close to today (within 1 day)', () => {
    expect(typeof INITIAL_DATE_RANGE.to).toBe('string')

    const today = new Date()
    const todayStr = today.toISOString().slice(0, 10)
    // Allow 1-day drift to handle timezone edge cases at midnight
    const diff = daysDiff(INITIAL_DATE_RANGE.to as string, todayStr)
    expect(diff).toBeLessThanOrEqual(1)
  })

  // --- setDateRange overrides the defaults ---

  it('setDateRange overrides the default from/to values', () => {
    const { setDateRange } = useFilterStore.getState()
    setDateRange('2024-01-01', '2024-06-30')
    const { dateRange } = useFilterStore.getState()
    expect(dateRange.from).toBe('2024-01-01')
    expect(dateRange.to).toBe('2024-06-30')
  })

  it('setDateRange can reset back to null values', () => {
    const { setDateRange } = useFilterStore.getState()
    setDateRange(null, null)
    const { dateRange } = useFilterStore.getState()
    expect(dateRange.from).toBeNull()
    expect(dateRange.to).toBeNull()
  })
})

describe('useFilterStore — existing functionality', () => {
  beforeEach(() => {
    useFilterStore.setState({
      dateRange: { from: null, to: null },
      categories: [],
      location: null,
      granularity: 'day',
      region: null,
      drillPath: [],
      comparisonMode: false,
      comparisonRange: { from: null, to: null },
    })
  })

  it('setCategories updates the categories array', () => {
    useFilterStore.getState().setCategories([1, 2, 3])
    expect(useFilterStore.getState().categories).toEqual([1, 2, 3])
  })

  it('setCategories replaces (not appends) existing categories', () => {
    useFilterStore.getState().setCategories([1])
    useFilterStore.getState().setCategories([4, 5])
    expect(useFilterStore.getState().categories).toEqual([4, 5])
  })

  it('setLocation updates location to a string value', () => {
    useFilterStore.getState().setLocation('תל אביב')
    expect(useFilterStore.getState().location).toBe('תל אביב')
  })

  it('setLocation can clear location to null', () => {
    useFilterStore.getState().setLocation('Beer Sheva')
    useFilterStore.getState().setLocation(null)
    expect(useFilterStore.getState().location).toBeNull()
  })

  it('setGranularity updates to week', () => {
    useFilterStore.getState().setGranularity('week')
    expect(useFilterStore.getState().granularity).toBe('week')
  })

  it('setGranularity updates to month', () => {
    useFilterStore.getState().setGranularity('month')
    expect(useFilterStore.getState().granularity).toBe('month')
  })

  it('setGranularity updates to day', () => {
    useFilterStore.getState().setGranularity('month')
    useFilterStore.getState().setGranularity('day')
    expect(useFilterStore.getState().granularity).toBe('day')
  })

  it('setRegion updates region value', () => {
    useFilterStore.getState().setRegion('North')
    expect(useFilterStore.getState().region).toBe('North')
  })

  it('setRegion can clear region to null', () => {
    useFilterStore.getState().setRegion('South')
    useFilterStore.getState().setRegion(null)
    expect(useFilterStore.getState().region).toBeNull()
  })

  it('pushDrill appends a level to drillPath', () => {
    useFilterStore.getState().pushDrill('zone-1')
    expect(useFilterStore.getState().drillPath).toEqual(['zone-1'])
  })

  it('pushDrill appends multiple levels in order', () => {
    useFilterStore.getState().pushDrill('zone-1')
    useFilterStore.getState().pushDrill('city-a')
    expect(useFilterStore.getState().drillPath).toEqual(['zone-1', 'city-a'])
  })

  it('popDrill trims path to given index (inclusive)', () => {
    useFilterStore.getState().pushDrill('zone-1')
    useFilterStore.getState().pushDrill('city-a')
    useFilterStore.getState().pushDrill('street-x')
    // popDrill(0) means keep only index 0 => ['zone-1']
    useFilterStore.getState().popDrill(0)
    expect(useFilterStore.getState().drillPath).toEqual(['zone-1'])
  })

  it('resetDrill clears drillPath and resets region to null', () => {
    useFilterStore.getState().setRegion('Center')
    useFilterStore.getState().pushDrill('zone-1')
    useFilterStore.getState().resetDrill()
    expect(useFilterStore.getState().drillPath).toEqual([])
    expect(useFilterStore.getState().region).toBeNull()
  })

  it('setComparisonMode enables comparison mode', () => {
    useFilterStore.getState().setComparisonMode(true)
    expect(useFilterStore.getState().comparisonMode).toBe(true)
  })

  it('setComparisonMode disables comparison mode', () => {
    useFilterStore.getState().setComparisonMode(true)
    useFilterStore.getState().setComparisonMode(false)
    expect(useFilterStore.getState().comparisonMode).toBe(false)
  })

  it('setComparisonRange updates comparisonRange', () => {
    useFilterStore.getState().setComparisonRange('2023-01-01', '2023-06-30')
    const { comparisonRange } = useFilterStore.getState()
    expect(comparisonRange.from).toBe('2023-01-01')
    expect(comparisonRange.to).toBe('2023-06-30')
  })

  it('setComparisonRange can clear to null', () => {
    useFilterStore.getState().setComparisonRange('2023-01-01', '2023-06-30')
    useFilterStore.getState().setComparisonRange(null, null)
    const { comparisonRange } = useFilterStore.getState()
    expect(comparisonRange.from).toBeNull()
    expect(comparisonRange.to).toBeNull()
  })
})
