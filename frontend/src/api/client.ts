import { useFilterStore } from '@/store/filters'

function buildFilterParams(): URLSearchParams {
  const { dateRange, categories, location } = useFilterStore.getState()
  const params = new URLSearchParams()

  if (dateRange.from) params.set('from_date', dateRange.from)
  if (dateRange.to) params.set('to_date', dateRange.to)
  if (categories.length > 0) {
    for (const c of categories) {
      params.append('categories', String(c))
    }
  }
  if (location) params.set('location', location)

  return params
}

async function request<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`API error: ${res.status} ${res.statusText}`)
  return res.json() as Promise<T>
}

// --- Response types matching backend schemas ---

export interface TimelineBucket {
  period: string
  count: number
}

export interface TimelineResponse {
  buckets: TimelineBucket[]
  granularity: string
}

export interface CategoryCount {
  category: number
  category_desc: string
  count: number
}

export interface HourlyHeatmapCell {
  hour: number
  weekday: number
  count: number
}

export interface LocationCount {
  location_name: string
  count: number
}

export interface TopLocation {
  location_name: string
  total: number
  sparkline: { day: string; count: number }[]
}

export interface KpiData {
  total_alerts: number
  unique_locations: number
  peak_day: { date: string; count: number }
  most_active_category: { category: number; name: string; name_en: string; percentage: number }
  date_range: { from: string; to: string }
  longest_quiet_days: number
}

// --- Geo & hierarchy types (matching backend response shapes) ---

export interface GeoLocation {
  location_name: string
  lat: number
  lng: number
  count: number
  categories?: number[]
}

export interface ZoneCity {
  name: string
  name_en: string
  lat: number
  lng: number
  alert_count: number
}

export interface ZoneHierarchy {
  zone: string
  zone_en: string
  total_alerts: number
  cities: ZoneCity[]
}

export interface RegionCategoryBreakdown {
  category: number
  category_desc: string
  count: number
}

export interface RegionTopLocation {
  location_name: string
  count: number
}

export interface RegionTimelineBucket {
  period: string
  count: number
}

export interface RegionData {
  zone_en: string
  total_alerts: number
  top_locations: RegionTopLocation[]
  category_breakdown: RegionCategoryBreakdown[]
  timeline: RegionTimelineBucket[]
}

// --- Phase 4: Lifestyle Analytics types ---

export interface NightScore {
  date: string
  peaceful: boolean
}

export interface SleepScoreData {
  score: number
  total_nights: number
  peaceful_nights: number
  trend: NightScore[]
}

export interface WeekdayRank {
  weekday: number
  weekday_name: string
  alert_count: number
  rank: number
}

export interface LocationHotHour {
  location_name: string
  peak_hour: number
  alert_count: number
}

export interface BestWeekdaysData {
  weekdays: WeekdayRank[]
  hot_hours: LocationHotHour[]
}

export interface QuietStreakEntry {
  start_date: string
  end_date: string
  days: number
}

export interface QuietStreaksData {
  current_streak: QuietStreakEntry | null
  longest_streak: QuietStreakEntry | null
  top_streaks: QuietStreakEntry[]
}

// --- Phase 5: Comparison + Prediction types ---

export interface AnomalyDay {
  date: string
  count: number
  z_score: number
  direction: 'high' | 'low'
}

export interface AnomalyData {
  mean_daily_count: number
  std_daily_count: number
  threshold: number
  total_days_analyzed: number
  anomalies: AnomalyDay[]
}

export interface PeriodSummary {
  from_date: string
  to_date: string
  total_alerts: number
  unique_locations: number
  top_categories: CategoryCount[]
  top_locations: LocationCount[]
  timeline: TimelineBucket[]
}

export interface ComparisonDelta {
  total_alerts_delta: number
  total_alerts_pct: number | null
  unique_locations_delta: number
}

export interface ComparisonData {
  period_a: PeriodSummary
  period_b: PeriodSummary
  delta: ComparisonDelta
}

export interface PrealertLocationStat {
  location_name: string
  total_prealerts: number
  followed_by_actual: number
  probability: number
}

export interface PrealertCorrelationData {
  window_minutes: number
  overall_total_prealerts: number
  overall_followed: number
  overall_probability: number
  locations: PrealertLocationStat[]
}

export const api = {
  getTimeline: () => {
    const params = buildFilterParams()
    const { granularity } = useFilterStore.getState()
    params.set('granularity', granularity)
    return request<TimelineResponse>(`/api/alerts/timeline?${params}`)
  },

  getCategories: () => {
    const params = buildFilterParams()
    return request<CategoryCount[]>(`/api/alerts/by-category?${params}`)
  },

  getHeatmap: () => {
    const params = buildFilterParams()
    return request<HourlyHeatmapCell[]>(`/api/analytics/hourly-heatmap?${params}`)
  },

  getLocationsByCount: (limit = 10) => {
    const params = buildFilterParams()
    params.set('limit', String(limit))
    return request<LocationCount[]>(`/api/alerts/by-location?${params}`)
  },

  getTopLocations: (limit = 10) => {
    const params = buildFilterParams()
    params.set('limit', String(limit))
    return request<TopLocation[]>(`/api/analytics/top-locations?${params}`)
  },

  getKpi: () => {
    const params = buildFilterParams()
    return request<KpiData>(`/api/analytics/kpi?${params}`)
  },

  getGeoData: () => {
    const params = buildFilterParams()
    return request<GeoLocation[]>(`/api/alerts/geo?${params}`)
  },

  getHierarchy: () => {
    return request<ZoneHierarchy[]>('/api/locations/hierarchy')
  },

  getRegionAnalytics: (zoneEn: string) => {
    return request<RegionData>(`/api/analytics/by-region/${encodeURIComponent(zoneEn)}`)
  },

  getSleepScore: () => {
    const params = buildFilterParams()
    return request<SleepScoreData>(`/api/analytics/sleep-score?${params}`)
  },

  getBestWeekdays: () => {
    const params = buildFilterParams()
    return request<BestWeekdaysData>(`/api/analytics/best-weekdays?${params}`)
  },

  getQuietStreaks: () => {
    const params = buildFilterParams()
    return request<QuietStreaksData>(`/api/analytics/quiet-streaks?${params}`)
  },

  getAnomalies: (threshold = 2.0) => {
    const params = buildFilterParams()
    params.set('threshold', String(threshold))
    return request<AnomalyData>(`/api/analytics/anomalies?${params}`)
  },

  getComparison: (aFrom: string, aTo: string, bFrom: string, bTo: string) => {
    const { categories, location } = useFilterStore.getState()
    const params = new URLSearchParams()
    params.set('period_a_from', aFrom)
    params.set('period_a_to', aTo)
    params.set('period_b_from', bFrom)
    params.set('period_b_to', bTo)
    if (categories.length) categories.forEach((c) => params.append('categories', String(c)))
    if (location) params.set('location', location)
    return request<ComparisonData>(`/api/analytics/compare?${params}`)
  },

  getPrealertCorrelation: (windowMinutes = 30) => {
    const params = buildFilterParams()
    params.set('window_minutes', String(windowMinutes))
    params.set('min_prealerts', '5')
    return request<PrealertCorrelationData>(`/api/analytics/prealert-correlation?${params}`)
  },

  getGeoDataForDate: (date: string) => {
    const { categories, location } = useFilterStore.getState()
    const params = new URLSearchParams()
    params.set('from_date', date)
    params.set('to_date', date)
    if (categories.length > 0) {
      for (const c of categories) {
        params.append('categories', String(c))
      }
    }
    if (location) params.set('location', location)
    return request<GeoLocation[]>(`/api/alerts/geo?${params}`)
  },
}
