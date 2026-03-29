import { useEffect, useState } from 'react'
import { useFilterStore } from '@/store/filters'

interface UseApiDataResult<T> {
  data: T | null
  loading: boolean
  error: string | null
}

export function useApiData<T>(fetcher: () => Promise<T>): UseApiDataResult<T> {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const { dateRange, categories, location, granularity } = useFilterStore()

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)

    fetcher()
      .then((result) => {
        if (!cancelled) {
          setData(result)
          setLoading(false)
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
  }, [dateRange.from, dateRange.to, categories, location, granularity])

  return { data, loading, error }
}
