import { useEffect, useState, useRef } from 'react'
import { useFilterStore } from '@/store/filters'

interface UseApiDataResult<T> {
  data: T | null
  loading: boolean
  error: string | null
}

// Simple in-memory cache with TTL
const cache = new Map<string, { data: unknown; timestamp: number }>()
const CACHE_TTL_MS = 60_000 // 60 seconds

function getCacheKey(): string {
  const { dateRange, categories, location, granularity, region } = useFilterStore.getState()
  return JSON.stringify({ from: dateRange.from, to: dateRange.to, categories, location, granularity, region })
}

export function useApiData<T>(fetcher: () => Promise<T>): UseApiDataResult<T> {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const fetcherRef = useRef(fetcher)
  fetcherRef.current = fetcher

  const { dateRange, categories, location, granularity, region } = useFilterStore()

  useEffect(() => {
    let cancelled = false
    const cacheKey = getCacheKey() + ':' + fetcherRef.current.toString().slice(0, 80)

    // Check cache first
    const cached = cache.get(cacheKey)
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
          cache.set(cacheKey, { data: result, timestamp: Date.now() })
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
  }, [dateRange.from, dateRange.to, categories, location, granularity, region])

  return { data, loading, error }
}
