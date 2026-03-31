import { useEffect, useState, useRef } from 'react'
import { useAcledFilterStore } from '@/store/acledFilters'

interface UseAcledDataResult<T> {
  data: T | null
  loading: boolean
  error: string | null
}

// Simple in-memory cache with TTL
const acledCache = new Map<string, { data: unknown; timestamp: number }>()
const CACHE_TTL_MS = 60_000 // 60 seconds

function getAcledCacheKey(): string {
  const { dateRange, countries, eventTypes, theaters, actor, granularity } = useAcledFilterStore.getState()
  return JSON.stringify({ from: dateRange.from, to: dateRange.to, countries, eventTypes, theaters, actor, granularity })
}

export function useAcledData<T>(fetcher: () => Promise<T>): UseAcledDataResult<T> {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const fetcherRef = useRef(fetcher)
  fetcherRef.current = fetcher

  const { dateRange, countries, eventTypes, theaters, actor, granularity } = useAcledFilterStore()

  useEffect(() => {
    let cancelled = false
    const cacheKey = getAcledCacheKey() + ':' + fetcherRef.current.toString().slice(0, 80)

    // Check cache first
    const cached = acledCache.get(cacheKey)
    if (cached && Date.now() - cached.timestamp < CACHE_TTL_MS) {
      setData(cached.data as T)
      setLoading(false)
      setError(null)
      return
    }

    setLoading(true)
    setError(null)

    fetcherRef.current()
      .then((result) => {
        if (!cancelled) {
          setData(result)
          setLoading(false)
          acledCache.set(cacheKey, { data: result, timestamp: Date.now() })
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Unknown error')
          setLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [dateRange.from, dateRange.to, countries, eventTypes, theaters, actor, granularity])

  return { data, loading, error }
}
