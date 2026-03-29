import { useCallback, useEffect, useRef } from 'react'
import { api } from '@/api/client'
import { usePlaybackStore } from '@/store/playback'

const BATCH_SIZE = 10

export function usePlayback() {
  const store = usePlaybackStore()
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Timer effect: run when playing, clear when paused
  useEffect(() => {
    if (store.playing && store.dates.length > 0) {
      timerRef.current = setInterval(() => {
        usePlaybackStore.getState().tick()
      }, 1000 / store.speed)
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [store.playing, store.speed, store.dates.length])

  const initPlayback = useCallback(async () => {
    const { setDates, setLoading, setProgress, addFrame } = usePlaybackStore.getState()
    setLoading(true)
    setProgress(0)

    // Fetch timeline to get dates with alerts
    const timeline = await api.getTimeline()
    const dates = timeline.buckets.map((b) => b.period).sort()
    if (dates.length === 0) {
      setLoading(false)
      return
    }
    setDates(dates)

    // Pre-fetch geo data in batches
    for (let i = 0; i < dates.length; i += BATCH_SIZE) {
      const batch = dates.slice(i, i + BATCH_SIZE)
      const results = await Promise.all(batch.map((d) => api.getGeoDataForDate(d)))
      for (let j = 0; j < batch.length; j++) {
        addFrame(batch[j], results[j])
      }
      setProgress(Math.min(100, Math.round(((i + batch.length) / dates.length) * 100)))
    }

    setLoading(false)
  }, [])

  const currentDate = store.dates[store.currentIndex] ?? null
  const currentGeoData = currentDate ? store.geoFrames.get(currentDate) ?? [] : []

  return {
    currentDate,
    currentGeoData,
    isPlaying: store.playing,
    isLoading: store.loading,
    progress: store.progress,
    speed: store.speed,
    currentIndex: store.currentIndex,
    totalFrames: store.dates.length,
    play: store.play,
    pause: store.pause,
    setSpeed: store.setSpeed,
    seekTo: store.seekTo,
    reset: store.reset,
    initPlayback,
  }
}
