/**
 * Client for the ACLED aggregate pulse endpoint.
 *
 * The pulse endpoint is independent of the conflict filter store — it takes
 * its own simple params (granularity, disorder_type, top_n) and returns a
 * global view assembled from ACLED's pre-computed Explorer overview files.
 */

export type PulseGranularity = 'day' | 'month'

export type PulseDisorderType =
  | 'all'
  | 'demonstrations'
  | 'politicalviolence'
  | 'insurgency'
  | 'atrocities'
  | 'repression'
  | 'terroristactivity'
  | 'foreignmilitary'

export interface PulseBucket {
  date: string
  events: number
  fatalities: number
  exposure: number
}

export interface PulseCountry {
  country_id: number
  country_name: string
  theater: string
  events: number
  fatalities: number
  exposure: number
}

export interface PulseTheater {
  theater: string
  countries: number
  events: number
  fatalities: number
  exposure: number
}

export interface ConflictPulseResponse {
  latest_update: string | null
  granularity: PulseGranularity
  disorder_type: PulseDisorderType
  window_start: string | null
  window_end: string | null
  total_events: number
  total_fatalities: number
  total_exposure: number
  timeline: PulseBucket[]
  top_countries: PulseCountry[]
  theater_rollup: PulseTheater[]
}

export interface PulseQuery {
  granularity?: PulseGranularity
  disorder_type?: PulseDisorderType
  top_n?: number
}

async function fetchJson<T>(url: string): Promise<T> {
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
    throw new Error(`Pulse API error: ${res.status} ${res.statusText}`)
  }
  return res.json() as Promise<T>
}

export function getConflictPulse(query: PulseQuery = {}): Promise<ConflictPulseResponse> {
  const params = new URLSearchParams()
  params.set('granularity', query.granularity ?? 'month')
  params.set('disorder_type', query.disorder_type ?? 'all')
  params.set('top_n', String(query.top_n ?? 20))
  return fetchJson<ConflictPulseResponse>(`/api/acled/aggregates/pulse?${params}`)
}
