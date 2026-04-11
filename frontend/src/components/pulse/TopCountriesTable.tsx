import type { PulseCountry } from '@/api/acledPulseClient'

interface Props {
  countries: PulseCountry[]
}

const THEATER_COLORS: Record<string, string> = {
  core_me: 'bg-red-500/15 text-red-400 border-red-500/30',
  extended_me: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
  maritime: 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30',
  global_terror: 'bg-purple-500/15 text-purple-400 border-purple-500/30',
  other: 'bg-slate-500/15 text-slate-400 border-slate-500/30',
}

function theaterChip(theater: string): string {
  return THEATER_COLORS[theater] ?? THEATER_COLORS.other
}

function formatNumber(n: number): string {
  return n.toLocaleString('en-US')
}

function formatExposure(n: number): string {
  if (n >= 1_000_000_000) return `${(n / 1_000_000_000).toFixed(1)}B`
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`
  return formatNumber(n)
}

function maxEvents(countries: PulseCountry[]): number {
  return countries.reduce((max, c) => (c.events > max ? c.events : max), 0)
}

export function TopCountriesTable({ countries }: Props) {
  const peak = maxEvents(countries)

  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <h3 className="text-sm font-semibold text-foreground mb-3">
        Top {countries.length} countries by event count
      </h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs text-muted-foreground border-b border-border">
              <th className="text-left font-medium py-2 pr-2">#</th>
              <th className="text-left font-medium py-2 pr-2">Country</th>
              <th className="text-left font-medium py-2 pr-2">Theater</th>
              <th className="text-right font-medium py-2 pr-2">Events</th>
              <th className="text-right font-medium py-2 pr-2">Fatalities</th>
              <th className="text-right font-medium py-2 pl-2">Exposure</th>
            </tr>
          </thead>
          <tbody>
            {countries.map((c, idx) => {
              const barPct = peak > 0 ? (c.events / peak) * 100 : 0
              return (
                <tr
                  key={c.country_id}
                  className="border-b border-border/40 hover:bg-muted/20"
                >
                  <td className="py-2 pr-2 text-muted-foreground font-mono">{idx + 1}</td>
                  <td className="py-2 pr-2 font-medium text-foreground">
                    {c.country_name}
                  </td>
                  <td className="py-2 pr-2">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-[10px] font-medium border ${theaterChip(
                        c.theater,
                      )}`}
                    >
                      {c.theater}
                    </span>
                  </td>
                  <td className="py-2 pr-2 text-right font-mono">
                    <div className="relative inline-block min-w-[80px]">
                      <div
                        className="absolute inset-y-0 right-0 bg-orange-500/20 rounded"
                        style={{ width: `${barPct}%` }}
                      />
                      <span className="relative">{formatNumber(c.events)}</span>
                    </div>
                  </td>
                  <td className="py-2 pr-2 text-right font-mono text-red-400">
                    {formatNumber(c.fatalities)}
                  </td>
                  <td className="py-2 pl-2 text-right font-mono text-amber-400">
                    {formatExposure(c.exposure)}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
