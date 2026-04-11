/**
 * Client for the cross-source refresh endpoint.
 *
 * POST /api/sync triggers a refresh run and returns per-source results.
 * With no body, the default fast sources are used (Tzofar, OREF, ACLED
 * aggregates). ACLED events is marked slow and not included by default.
 */

export interface SyncSourceResult {
  source: string
  label: string
  status: 'ok' | 'error'
  rows_synced: number
  elapsed_seconds: number
  error: string | null
}

export interface SyncResponse {
  results: SyncSourceResult[]
  total_rows: number
  total_elapsed_seconds: number
  ok_count: number
  error_count: number
}

export interface SyncSource {
  name: string
  label: string
  slow: boolean
}

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  let res: Response
  try {
    res = await fetch(url, init)
  } catch (err: unknown) {
    if (err instanceof TypeError) {
      throw new Error('Cannot connect to server. Is the backend running?')
    }
    throw err instanceof Error ? err : new Error(String(err))
  }
  if (!res.ok) {
    throw new Error(`Sync API error: ${res.status} ${res.statusText}`)
  }
  return res.json() as Promise<T>
}

export function listSyncSources(): Promise<SyncSource[]> {
  return fetchJson<SyncSource[]>('/api/sync/sources')
}

export interface RefreshOptions {
  sources?: string[]
}

export function refreshAll(options: RefreshOptions = {}): Promise<SyncResponse> {
  const body = options.sources ? JSON.stringify({ sources: options.sources }) : '{}'
  return fetchJson<SyncResponse>('/api/sync', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body,
  })
}
