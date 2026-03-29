import { create } from 'zustand'
import type { GeoLocation } from '@/api/client'

type Speed = 1 | 2 | 5

interface PlaybackState {
  playing: boolean
  currentIndex: number
  speed: Speed
  dates: string[]
  geoFrames: Map<string, GeoLocation[]>
  loading: boolean
  progress: number

  play: () => void
  pause: () => void
  setSpeed: (s: Speed) => void
  seekTo: (index: number) => void
  tick: () => void
  reset: () => void
  setDates: (d: string[]) => void
  addFrame: (date: string, data: GeoLocation[]) => void
  setLoading: (loading: boolean) => void
  setProgress: (p: number) => void
}

export const usePlaybackStore = create<PlaybackState>((set, get) => ({
  playing: false,
  currentIndex: 0,
  speed: 1,
  dates: [],
  geoFrames: new Map(),
  loading: false,
  progress: 0,

  play: () => set({ playing: true }),
  pause: () => set({ playing: false }),
  setSpeed: (speed) => set({ speed }),
  seekTo: (index) => set({ currentIndex: index }),
  tick: () => {
    const { currentIndex, dates } = get()
    if (dates.length === 0) return
    const next = (currentIndex + 1) % dates.length
    set({ currentIndex: next, playing: next !== 0 })
  },
  reset: () => set({ playing: false, currentIndex: 0, dates: [], geoFrames: new Map(), loading: false, progress: 0 }),
  setDates: (dates) => set({ dates, currentIndex: 0 }),
  addFrame: (date, data) =>
    set((state) => {
      const frames = new Map(state.geoFrames)
      frames.set(date, data)
      return { geoFrames: frames }
    }),
  setLoading: (loading) => set({ loading }),
  setProgress: (progress) => set({ progress }),
}))
