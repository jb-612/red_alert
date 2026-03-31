import { useAcledFilterStore } from '@/store/acledFilters'

function buildAcledFilterParams(): URLSearchParams {
  const { dateRange, countries, eventTypes, theaters, actor } = useAcledFilterStore.getState()
  const params = new URLSearchParams()

  if (dateRange.from) params.set('from_date', dateRange.from)
  if (dateRange.to) params.set('to_date', dateRange.to)
  if (countries.length > 0) {
    for (const c of countries) {
      params.append('countries', c)
    }
  }
  if (eventTypes.length > 0) {
    for (const t of eventTypes) {
      params.append('event_types', t)
    }
  }
  if (theaters.length > 0) {
    for (const t of theaters) {
      params.append('theaters', t)
    }
  }
  if (actor) params.set('actor', actor)

  return params
}

async function request<T>(url: string): Promise<T> {
  let res: Response
  try {
    res = await fetch(url)
  } catch (err: unknown) {
    if (err instanceof TypeError) {
      throw new Error('Cannot connect to server. Is the backend running?')
    }
    throw err instanceof Error ? err : new Error(String(err))
  }
  if (!res.ok) {
    if (res.status >= 500) throw new Error(`Server error (${res.status})`)
    if (res.status === 404) throw new Error(`Not found (404)`)
    throw new Error(`API error: ${res.status} ${res.statusText}`)
  }
  return res.json() as Promise<T>
}

// --- Response types matching backend ACLED schemas ---

export interface AcledGeoPoint {
  location: string
  country: string
  lat: number
  lng: number
  count: number
  fatalities: number
  event_types: string[]
}

export interface AcledTimelineBucket {
  period: string
  count: number
  fatalities: number
}

export interface AcledTimelineResponse {
  buckets: AcledTimelineBucket[]
  granularity: string
}

export interface AcledCountryCount {
  country: string
  count: number
  fatalities: number
}

export interface AcledEventTypeCount {
  event_type: string
  sub_event_type: string | null
  count: number
  fatalities: number
}

export interface AcledActorCount {
  actor: string
  count: number
  fatalities: number
}

export interface AcledTheaterCount {
  theater: string
  count: number
  fatalities: number
}

export interface AcledAnomalyDay {
  date: string
  count: number
  fatalities: number
  z_score: number
  direction: string
}

export interface AcledAnomalyResponse {
  mean_daily_count: number
  std_daily_count: number
  threshold: number
  total_days_analyzed: number
  anomalies: AcledAnomalyDay[]
}

export interface AcledEscalationEntry {
  theater: string
  current_week_count: number
  previous_week_count: number
  change_pct: number | null
  fatalities_current: number
}

export interface AcledEscalationResponse {
  theaters: AcledEscalationEntry[]
  period_end: string
}

export interface AcledActorProfile {
  actor: string
  total_events: number
  total_fatalities: number
  countries: string[]
  event_types: string[]
  theaters: string[]
}

export interface AcledTheaterSeries {
  theater: string
  buckets: AcledTimelineBucket[]
}

export interface AcledTheaterTimelineResponse {
  series: AcledTheaterSeries[]
  granularity: string
}

export interface AcledCivilianCountryImpact {
  country: string
  civilian_events: number
  civilian_fatalities: number
}

export interface AcledCivilianImpactResponse {
  total_civilian_events: number
  total_civilian_fatalities: number
  by_country: AcledCivilianCountryImpact[]
}

export interface AcledSyncStatus {
  last_sync_date: string | null
  last_sync_at: string | null
  total_events: number
}

export const acledApi = {
  getAcledGeo: () => {
    const params = buildAcledFilterParams()
    return request<AcledGeoPoint[]>(`/api/acled/geo?${params}`)
  },

  getAcledTimeline: () => {
    const params = buildAcledFilterParams()
    const { granularity } = useAcledFilterStore.getState()
    params.set('granularity', granularity)
    return request<AcledTimelineResponse>(`/api/acled/timeline?${params}`)
  },

  getAcledByCountry: () => {
    const params = buildAcledFilterParams()
    return request<AcledCountryCount[]>(`/api/acled/by-country?${params}`)
  },

  getAcledByType: () => {
    const params = buildAcledFilterParams()
    return request<AcledEventTypeCount[]>(`/api/acled/by-type?${params}`)
  },

  getAcledByActor: (limit = 20) => {
    const params = buildAcledFilterParams()
    params.set('limit', String(limit))
    return request<AcledActorCount[]>(`/api/acled/by-actor?${params}`)
  },

  getAcledByTheater: () => {
    const params = buildAcledFilterParams()
    return request<AcledTheaterCount[]>(`/api/acled/by-theater?${params}`)
  },

  getAcledAnomalies: (threshold = 2.0) => {
    const params = buildAcledFilterParams()
    params.set('threshold', String(threshold))
    return request<AcledAnomalyResponse>(`/api/acled/anomalies?${params}`)
  },

  getAcledEscalation: () => {
    return request<AcledEscalationResponse>('/api/acled/escalation')
  },

  getAcledActorProfile: (actor: string) => {
    const params = buildAcledFilterParams()
    params.set('actor', actor)
    return request<AcledActorProfile>(`/api/acled/actor-profile?${params}`)
  },

  getAcledTheaterTimeline: () => {
    const params = buildAcledFilterParams()
    const { granularity } = useAcledFilterStore.getState()
    params.set('granularity', granularity)
    return request<AcledTheaterTimelineResponse>(`/api/acled/theater-timeline?${params}`)
  },

  getAcledCivilianImpact: () => {
    const params = buildAcledFilterParams()
    return request<AcledCivilianImpactResponse>(`/api/acled/civilian-impact?${params}`)
  },

  getAcledSyncStatus: () => {
    return request<AcledSyncStatus>('/api/acled/sync-status')
  },
}
