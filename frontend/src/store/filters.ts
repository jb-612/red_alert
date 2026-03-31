import { create } from 'zustand'

function formatDate(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

const today = new Date()
const sixMonthsAgo = new Date(today)
sixMonthsAgo.setMonth(sixMonthsAgo.getMonth() - 6)
const defaultFrom = formatDate(sixMonthsAgo)
const defaultTo = formatDate(today)

interface FilterState {
  dateRange: { from: string | null; to: string | null }
  categories: number[]
  location: string | null
  granularity: 'day' | 'week' | 'month'
  region: string | null
  drillPath: string[]
  comparisonMode: boolean
  comparisonRange: { from: string | null; to: string | null }
  setDateRange: (from: string | null, to: string | null) => void
  setCategories: (categories: number[]) => void
  setLocation: (location: string | null) => void
  setGranularity: (granularity: 'day' | 'week' | 'month') => void
  setRegion: (region: string | null) => void
  pushDrill: (level: string) => void
  popDrill: (index: number) => void
  resetDrill: () => void
  setComparisonMode: (on: boolean) => void
  setComparisonRange: (from: string | null, to: string | null) => void
}

export const useFilterStore = create<FilterState>((set) => ({
  dateRange: { from: defaultFrom, to: defaultTo },
  categories: [],
  location: null,
  granularity: 'day',
  region: null,
  drillPath: [],
  setDateRange: (from, to) => set({ dateRange: { from, to } }),
  setCategories: (categories) => set({ categories }),
  setLocation: (location) => set({ location }),
  setGranularity: (granularity) => set({ granularity }),
  setRegion: (region) => set({ region }),
  pushDrill: (level) => set((state) => ({ drillPath: [...state.drillPath, level] })),
  popDrill: (index) => set((state) => ({ drillPath: state.drillPath.slice(0, index + 1) })),
  resetDrill: () => set({ drillPath: [], region: null }),
  comparisonMode: false,
  comparisonRange: { from: null, to: null },
  setComparisonMode: (on) => set({ comparisonMode: on }),
  setComparisonRange: (from, to) => set({ comparisonRange: { from, to } }),
}))
