import { create } from 'zustand'

function formatDate(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

const today = new Date()
const sixMonthsAgo = new Date(today)
sixMonthsAgo.setMonth(sixMonthsAgo.getMonth() - 6)
const defaultFrom = formatDate(sixMonthsAgo)
const defaultTo = formatDate(today)

interface AcledFilterState {
  dateRange: { from: string | null; to: string | null }
  countries: string[]
  eventTypes: string[]
  theaters: string[]
  actor: string | null
  granularity: 'day' | 'week' | 'month'
  setDateRange: (from: string | null, to: string | null) => void
  setCountries: (countries: string[]) => void
  setEventTypes: (eventTypes: string[]) => void
  setTheaters: (theaters: string[]) => void
  setActor: (actor: string | null) => void
  setGranularity: (granularity: 'day' | 'week' | 'month') => void
}

export const useAcledFilterStore = create<AcledFilterState>((set) => ({
  dateRange: { from: defaultFrom, to: defaultTo },
  countries: [],
  eventTypes: [],
  theaters: [],
  actor: null,
  granularity: 'day',
  setDateRange: (from, to) => set({ dateRange: { from, to } }),
  setCountries: (countries) => set({ countries }),
  setEventTypes: (eventTypes) => set({ eventTypes }),
  setTheaters: (theaters) => set({ theaters }),
  setActor: (actor) => set({ actor }),
  setGranularity: (granularity) => set({ granularity }),
}))
