import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import { useFilterStore } from '@/store/filters'

// Mock echarts-for-react so we don't need a real canvas in jsdom
vi.mock('echarts-for-react', () => ({
  default: vi.fn(({ style }: { style?: React.CSSProperties }) => (
    <div data-testid="echarts-mock" style={style} />
  )),
}))

// Mock lucide-react icons used by ChartPanel
vi.mock('lucide-react', () => ({
  ImageDown: () => <svg data-testid="icon-image-down" />,
  FileDown: () => <svg data-testid="icon-file-down" />,
}))

// Mock the export utilities to avoid DOM canvas APIs
vi.mock('@/lib/export', () => ({
  exportPng: vi.fn(),
  exportCsv: vi.fn(),
}))

// Import after vi.mock() calls — Vitest hoists vi.mock() so this is safe
import { PeriodComparison } from '../PeriodComparison'

// Minimal ComparisonData satisfying the API contract
const mockComparisonData = {
  period_a: {
    from_date: '2024-01-01',
    to_date: '2024-03-31',
    total_alerts: 120,
    unique_locations: 15,
    top_categories: [],
    top_locations: [],
    timeline: [
      { period: '2024-01-01', count: 40 },
      { period: '2024-02-01', count: 45 },
      { period: '2024-03-01', count: 35 },
    ],
  },
  period_b: {
    from_date: '2023-01-01',
    to_date: '2023-03-31',
    total_alerts: 100,
    unique_locations: 12,
    top_categories: [],
    top_locations: [],
    timeline: [
      { period: '2023-01-01', count: 30 },
      { period: '2023-02-01', count: 35 },
      { period: '2023-03-01', count: 35 },
    ],
  },
  delta: {
    total_alerts_delta: 20,
    total_alerts_pct: 20.0,
    unique_locations_delta: 3,
  },
}

function resetStoreToNullDates() {
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
}

describe('PeriodComparison — hooks safety (Rules of Hooks)', () => {
  beforeEach(() => {
    resetStoreToNullDates()
    vi.restoreAllMocks()
    vi.unstubAllGlobals()
  })

  afterEach(() => {
    resetStoreToNullDates()
    vi.restoreAllMocks()
    vi.unstubAllGlobals()
  })

  // -------------------------------------------------------------------------
  // Test 1: null dateRange — component renders a prompt, not crash.
  // The hooks-after-early-return bug does NOT affect this test because the
  // null-dates branch is taken on mount and there's no previous render to
  // compare against (first mount, hook count is consistent within that render).
  // -------------------------------------------------------------------------
  it('renders prompt text when dateRange is null (no crash on first mount)', () => {
    expect(() => render(<PeriodComparison />)).not.toThrow()
    expect(
      screen.getByText(/select both date ranges to compare/i),
    ).toBeInTheDocument()
  })

  // -------------------------------------------------------------------------
  // Test 2: dateRange set, comparisonRange still null — renders prompt.
  // -------------------------------------------------------------------------
  it('renders prompt when dateRange is set but comparisonRange is null', () => {
    useFilterStore.setState({
      dateRange: { from: '2024-01-01', to: '2024-03-31' },
      comparisonRange: { from: null, to: null },
    })

    expect(() => render(<PeriodComparison />)).not.toThrow()
    expect(
      screen.getByText(/select both date ranges to compare/i),
    ).toBeInTheDocument()
  })

  // -------------------------------------------------------------------------
  // Test 3: Both ranges set — mocked API returns data.
  // The early return is NOT taken, so React executes the useCallback hooks
  // that follow it. On first mount this is fine. On re-render after a null→set
  // transition (see Test 4) it will violate hooks rules.
  // This test verifies a successful first-mount render with both ranges set.
  // -------------------------------------------------------------------------
  it('renders without error when both ranges are set and API returns data (first mount)', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockComparisonData,
    })
    vi.stubGlobal('fetch', fetchMock)

    useFilterStore.setState({
      dateRange: { from: '2024-01-01', to: '2024-03-31' },
      comparisonRange: { from: '2023-01-01', to: '2023-03-31' },
    })

    await act(async () => {
      render(<PeriodComparison />)
    })

    // The empty-state prompt must NOT appear when both ranges are set
    expect(
      screen.queryByText(/select both date ranges to compare/i),
    ).not.toBeInTheDocument()

    // Fetch should have been called for the comparison endpoint
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/api/analytics/compare'),
    )
  })

  // -------------------------------------------------------------------------
  // Test 4: Transition — null → set dates — exposes the hooks mismatch.
  // This is the primary test for the Rules of Hooks violation.
  //
  // React renders PeriodComparison twice:
  //   Render 1 (null dates): early return after line 63 — useCallback hooks
  //     at lines 114 and 118 are NEVER called → 16 hooks total.
  //   Render 2 (set dates): no early return — useCallback hooks ARE called
  //     → 18 hooks total.
  //
  // React detects hook count mismatch and throws:
  //   "Rendered more hooks than during the previous render."
  //
  // After the fix (move useCallback above the early return), the count stays
  // constant at 18 across all renders and this test will pass.
  // -------------------------------------------------------------------------
  it('does not crash when transitioning from null dates to set dates', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockComparisonData,
    })
    vi.stubGlobal('fetch', fetchMock)

    // Initial render with null dates (takes the early return path)
    const { rerender } = render(<PeriodComparison />)
    expect(
      screen.getByText(/select both date ranges to compare/i),
    ).toBeInTheDocument()

    // Transition: set both ranges, triggering a re-render that skips the early
    // return and encounters the useCallback hooks for the first time.
    // This throws "Rendered more hooks than during the previous render." currently.
    await act(async () => {
      useFilterStore.setState({
        dateRange: { from: '2024-01-01', to: '2024-03-31' },
        comparisonRange: { from: '2023-01-01', to: '2023-03-31' },
      })
      rerender(<PeriodComparison />)
    })

    // After the fix, the prompt should be gone and no error should have thrown
    expect(
      screen.queryByText(/select both date ranges to compare/i),
    ).not.toBeInTheDocument()
  })

  // -------------------------------------------------------------------------
  // Test 5: Reverse transition — set → null — exposes the "fewer hooks" error.
  //
  // React renders PeriodComparison twice:
  //   Render 1 (set dates): 18 hooks (useCallback hooks are called).
  //   Render 2 (null dates): early return at line 55 — useCallback hooks at
  //     lines 114 and 118 are SKIPPED → 16 hooks.
  //
  // React detects hook count decrease and throws:
  //   "Rendered fewer hooks than expected."
  //
  // After the fix, hook count stays at 18 for all renders.
  // -------------------------------------------------------------------------
  it('does not crash when transitioning from set dates back to null', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockComparisonData,
    })
    vi.stubGlobal('fetch', fetchMock)

    // Start with both ranges set
    useFilterStore.setState({
      dateRange: { from: '2024-01-01', to: '2024-03-31' },
      comparisonRange: { from: '2023-01-01', to: '2023-03-31' },
    })

    const { rerender } = await act(async () => render(<PeriodComparison />))

    // Now clear the dates — the early return will now be taken, skipping useCallback
    await act(async () => {
      useFilterStore.setState({
        dateRange: { from: null, to: null },
        comparisonRange: { from: null, to: null },
      })
      rerender(<PeriodComparison />)
    })

    // After the fix, this should render the prompt without error
    expect(
      screen.getByText(/select both date ranges to compare/i),
    ).toBeInTheDocument()
  })
})
