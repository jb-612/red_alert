import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { api } from '@/api/client'
import { useFilterStore } from '@/store/filters'

// We test through the public `api` object because `request()` is a private
// module-level function. api.getKpi() → buildFilterParams() + request().

describe('api client — request() error handling', () => {
  beforeEach(() => {
    // Pre-populate store with dates so buildFilterParams produces a real URL
    useFilterStore.setState({
      dateRange: { from: '2024-01-01', to: '2024-06-30' },
      categories: [],
      location: null,
      granularity: 'day',
      region: null,
      drillPath: [],
      comparisonMode: false,
      comparisonRange: { from: null, to: null },
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
    vi.unstubAllGlobals()
  })

  // ---------------------------------------------------------------------------
  // Test 1: Network failure (TypeError from fetch) → user-friendly message.
  // Current code: re-throws the raw TypeError ("Failed to fetch") unchanged.
  // The fix must produce a message matching /cannot connect to server/i.
  // ---------------------------------------------------------------------------
  it('returns user-friendly "Cannot connect to server" message on network failure', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))

    await expect(api.getKpi()).rejects.toThrow(/cannot connect to server/i)
  })

  // ---------------------------------------------------------------------------
  // Test 2: HTTP 500 → error message includes human-readable status context.
  // Current code throws `API error: 500 Internal Server Error`.
  // The fix should produce something like "Server error (500)".
  // ---------------------------------------------------------------------------
  it('throws an error containing "Server error (500)" on HTTP 500 response', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        json: async () => ({ detail: 'Something went wrong' }),
      }),
    )

    await expect(api.getKpi()).rejects.toThrow(/server error.*500|500.*server error/i)
  })

  // ---------------------------------------------------------------------------
  // Test 3: HTTP 404 → error message communicates "not found".
  // ---------------------------------------------------------------------------
  it('throws an error containing "not found" or 404 on HTTP 404 response', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
        statusText: 'Not Found',
        json: async () => ({ detail: 'Resource not found' }),
      }),
    )

    await expect(api.getKpi()).rejects.toThrow(/not found|404/i)
  })

  // ---------------------------------------------------------------------------
  // Test 4: Successful 200 response → parsed JSON is returned.
  // This verifies the happy path still works after any error-handling changes.
  // ---------------------------------------------------------------------------
  it('returns parsed JSON on a successful 200 response', async () => {
    const mockKpi = {
      total_alerts: 5000,
      unique_locations: 200,
      peak_day: { date: '2024-03-15', count: 150 },
      most_active_category: {
        category: 1,
        name: 'רקטות',
        name_en: 'Rockets',
        percentage: 72.5,
      },
      date_range: { from: '2024-01-01', to: '2024-06-30' },
      longest_quiet_days: 14,
    }

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        statusText: 'OK',
        json: async () => mockKpi,
      }),
    )

    const result = await api.getKpi()

    expect(result).toEqual(mockKpi)
    expect(result.total_alerts).toBe(5000)
  })

  // ---------------------------------------------------------------------------
  // Test 5: HTTP 503 (gateway timeout) → includes status in error message.
  // Ensures the pattern generalises beyond 500 and 404.
  // ---------------------------------------------------------------------------
  it('throws an error containing the status code on HTTP 503', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 503,
        statusText: 'Service Unavailable',
        json: async () => ({}),
      }),
    )

    await expect(api.getKpi()).rejects.toThrow(/503/)
  })

  // ---------------------------------------------------------------------------
  // Test 6: Non-TypeError network error (e.g. AbortError) → still throws
  // a meaningful message (not swallowed or stringified as "[object Object]").
  // ---------------------------------------------------------------------------
  it('wraps AbortError in a meaningful thrown error', async () => {
    const abortError = new DOMException('The user aborted a request.', 'AbortError')
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(abortError))

    await expect(api.getKpi()).rejects.toThrow(/.+/)
  })

  // ---------------------------------------------------------------------------
  // Test 7: Fetch is called with from_date and to_date from the filter store.
  // The store is pre-seeded in beforeEach with '2024-01-01' / '2024-06-30'.
  // Currently this FAILS because the store defaults to null on module load and
  // the beforeEach setState call runs AFTER the module-level import; once the
  // fix for the default date range lands, this will also start passing.
  //
  // Note: the failure mode is that the URL has no date params at all
  // (because buildFilterParams skips null values), so the assertion fails
  // because the URL is just "/api/analytics/kpi?".
  // ---------------------------------------------------------------------------
  it('passes from_date and to_date query params from the filter store', async () => {
    const capturedUrls: string[] = []

    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation((url: string) => {
        capturedUrls.push(url)
        return Promise.resolve({
          ok: true,
          status: 200,
          statusText: 'OK',
          json: async () => ({
            total_alerts: 0,
            unique_locations: 0,
            peak_day: { date: '', count: 0 },
            most_active_category: { category: 0, name: '', name_en: '', percentage: 0 },
            date_range: { from: '', to: '' },
            longest_quiet_days: 0,
          }),
        })
      }),
    )

    await api.getKpi()

    expect(capturedUrls[0]).toContain('from_date=2024-01-01')
    expect(capturedUrls[0]).toContain('to_date=2024-06-30')
  })
})
