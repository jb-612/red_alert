import { useEffect, useState } from 'react'
import {
  getConflictPulse,
  type ConflictPulseResponse,
  type PulseDisorderType,
  type PulseGranularity,
} from '@/api/acledPulseClient'
import { FreshnessBanner } from '@/components/pulse/FreshnessBanner'
import { GlobalTimelineChart } from '@/components/pulse/GlobalTimelineChart'
import { TheaterRollup } from '@/components/pulse/TheaterRollup'
import { TopCountriesTable } from '@/components/pulse/TopCountriesTable'

const DISORDER_OPTIONS: { value: PulseDisorderType; label: string }[] = [
  { value: 'all', label: 'All disorder' },
  { value: 'politicalviolence', label: 'Political violence' },
  { value: 'demonstrations', label: 'Demonstrations' },
  { value: 'terroristactivity', label: 'Terrorist activity' },
  { value: 'insurgency', label: 'Insurgency' },
  { value: 'atrocities', label: 'Atrocities' },
  { value: 'repression', label: 'Repression' },
  { value: 'foreignmilitary', label: 'Foreign military' },
]

const GRANULARITY_OPTIONS: { value: PulseGranularity; label: string; description: string }[] = [
  { value: 'month', label: '12 months', description: 'Monthly buckets' },
  { value: 'day', label: '29 days', description: 'Daily buckets' },
]

interface ControlsProps {
  granularity: PulseGranularity
  disorderType: PulseDisorderType
  onGranularityChange: (g: PulseGranularity) => void
  onDisorderChange: (d: PulseDisorderType) => void
}

function PulseControls({
  granularity,
  disorderType,
  onGranularityChange,
  onDisorderChange,
}: ControlsProps) {
  return (
    <div className="flex flex-wrap items-center gap-3 rounded-lg border border-border bg-card p-3">
      <div className="flex items-center gap-2">
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
          Window
        </span>
        <div className="flex rounded-md border border-border overflow-hidden">
          {GRANULARITY_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => onGranularityChange(opt.value)}
              className={`px-3 py-1.5 text-xs font-medium transition ${
                granularity === opt.value
                  ? 'bg-orange-500 text-white'
                  : 'bg-transparent text-muted-foreground hover:bg-muted/30'
              }`}
              title={opt.description}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
          Filter
        </span>
        <select
          value={disorderType}
          onChange={(e) => onDisorderChange(e.target.value as PulseDisorderType)}
          className="rounded-md border border-border bg-background px-3 py-1.5 text-xs text-foreground focus:outline-none focus:ring-2 focus:ring-orange-500/50"
        >
          {DISORDER_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>
    </div>
  )
}

function LoadingSkeleton() {
  return (
    <div className="rounded-lg border border-border bg-card p-8 flex items-center justify-center">
      <div className="animate-spin h-6 w-6 border-2 border-orange-500 border-t-transparent rounded-full" />
    </div>
  )
}

function ErrorBanner({ error }: { error: string }) {
  return (
    <div className="rounded-lg border border-red-500/40 bg-red-500/10 p-4 text-sm text-red-400">
      {error}
    </div>
  )
}

export function ConflictPulsePage() {
  const [granularity, setGranularity] = useState<PulseGranularity>('month')
  const [disorderType, setDisorderType] = useState<PulseDisorderType>('all')
  const [pulse, setPulse] = useState<ConflictPulseResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    getConflictPulse({ granularity, disorder_type: disorderType, top_n: 20 })
      .then((data) => {
        if (!cancelled) setPulse(data)
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          const msg = err instanceof Error ? err.message : String(err)
          setError(msg)
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [granularity, disorderType])

  return (
    <div className="flex flex-1 overflow-hidden">
      <main className="flex-1 overflow-y-auto p-6 space-y-4">
        <PulseControls
          granularity={granularity}
          disorderType={disorderType}
          onGranularityChange={setGranularity}
          onDisorderChange={setDisorderType}
        />
        {error && <ErrorBanner error={error} />}
        {loading && !pulse && <LoadingSkeleton />}
        {pulse && (
          <>
            <FreshnessBanner pulse={pulse} />
            <GlobalTimelineChart timeline={pulse.timeline} granularity={pulse.granularity} />
            <TheaterRollup rollup={pulse.theater_rollup} />
            <TopCountriesTable countries={pulse.top_countries} />
          </>
        )}
      </main>
    </div>
  )
}
