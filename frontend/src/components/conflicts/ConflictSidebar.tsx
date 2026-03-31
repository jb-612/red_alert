import { useState } from 'react'
import { CalendarIcon, Search, X } from 'lucide-react'
import { format, parse } from 'date-fns'
import { useAcledFilterStore } from '@/store/acledFilters'
import { useLabels } from '@/lib/labels'
import { Button } from '@/components/ui/button'
import { Popover, PopoverTrigger, PopoverContent } from '@/components/ui/popover'
import { Calendar } from '@/components/ui/calendar'

function DatePickerField({ value, onChange, label }: { value: string | null; onChange: (v: string | null) => void; label: string }) {
  const [open, setOpen] = useState(false)
  const selected = value ? parse(value, 'yyyy-MM-dd', new Date()) : undefined

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger
        className="flex w-full items-center gap-2 rounded-md border border-input bg-background px-3 py-1.5 text-sm text-foreground hover:bg-muted/50 transition-colors"
      >
        <CalendarIcon className="size-3.5 text-muted-foreground" />
        <span className={value ? 'text-foreground' : 'text-muted-foreground'}>
          {value ? format(parse(value, 'yyyy-MM-dd', new Date()), 'MMM d, yyyy') : label}
        </span>
      </PopoverTrigger>
      <PopoverContent align="start" side="bottom" sideOffset={4}>
        <Calendar
          mode="single"
          selected={selected}
          onSelect={(date) => {
            if (date) {
              const y = date.getFullYear()
              const m = String(date.getMonth() + 1).padStart(2, '0')
              const d = String(date.getDate()).padStart(2, '0')
              onChange(`${y}-${m}-${d}`)
            } else {
              onChange(null)
            }
            setOpen(false)
          }}
          captionLayout="dropdown"
        />
      </PopoverContent>
    </Popover>
  )
}

const THEATERS = [
  { id: 'core_me', labelKey: 'coreME' as const },
  { id: 'maritime', labelKey: 'maritime' as const },
  { id: 'extended_me', labelKey: 'extendedME' as const },
  { id: 'global_terror', labelKey: 'globalTerror' as const },
]

const EVENT_TYPES = [
  'Battles',
  'Explosions/Remote violence',
  'Violence against civilians',
]

export function ConflictSidebar() {
  const labels = useLabels()
  const {
    dateRange, theaters, eventTypes, actor, granularity,
    setDateRange, setTheaters, setEventTypes, setActor, setGranularity,
    countries, setCountries,
  } = useAcledFilterStore()

  const [countryInput, setCountryInput] = useState('')

  function toggleTheater(id: string) {
    if (theaters.includes(id)) {
      setTheaters(theaters.filter((t) => t !== id))
    } else {
      setTheaters([...theaters, id])
    }
  }

  function toggleEventType(type: string) {
    if (eventTypes.includes(type)) {
      setEventTypes(eventTypes.filter((t) => t !== type))
    } else {
      setEventTypes([...eventTypes, type])
    }
  }

  function handleCountryKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter' && countryInput.trim()) {
      const trimmed = countryInput.trim()
      if (!countries.includes(trimmed)) {
        setCountries([...countries, trimmed])
      }
      setCountryInput('')
    }
  }

  function removeCountry(c: string) {
    setCountries(countries.filter((x) => x !== c))
  }

  return (
    <aside className="w-64 shrink-0 border-e border-border p-4 space-y-6 overflow-y-auto">
      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
          {labels.dateRange}
        </h3>
        <div className="space-y-2">
          <DatePickerField
            value={dateRange.from}
            onChange={(v) => setDateRange(v, dateRange.to)}
            label="From date"
          />
          <DatePickerField
            value={dateRange.to}
            onChange={(v) => setDateRange(dateRange.from, v)}
            label="To date"
          />
        </div>
      </div>

      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
          {labels.theaters}
        </h3>
        <div className="space-y-1">
          {THEATERS.map((t) => (
            <label key={t.id} className="flex items-center gap-2 cursor-pointer text-sm text-foreground">
              <input
                type="checkbox"
                checked={theaters.includes(t.id)}
                onChange={() => toggleTheater(t.id)}
                className="rounded border-input accent-red-600"
              />
              {labels[t.labelKey]}
            </label>
          ))}
        </div>
      </div>

      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
          {labels.countries}
        </h3>
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 size-3.5 text-muted-foreground" />
          <input
            type="text"
            placeholder="Add country..."
            value={countryInput}
            onChange={(e) => setCountryInput(e.target.value)}
            onKeyDown={handleCountryKeyDown}
            className="w-full rounded-md border border-input bg-background pl-8 pr-3 py-1.5 text-sm text-foreground placeholder:text-muted-foreground"
          />
        </div>
        {countries.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {countries.map((c) => (
              <span key={c} className="inline-flex items-center gap-1 rounded-full bg-muted px-2 py-0.5 text-xs text-foreground">
                {c}
                <button onClick={() => removeCountry(c)} className="text-muted-foreground hover:text-foreground">
                  <X className="size-3" />
                </button>
              </span>
            ))}
          </div>
        )}
      </div>

      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
          {labels.events}
        </h3>
        <div className="space-y-1">
          {EVENT_TYPES.map((type) => (
            <label key={type} className="flex items-center gap-2 cursor-pointer text-sm text-foreground">
              <input
                type="checkbox"
                checked={eventTypes.includes(type)}
                onChange={() => toggleEventType(type)}
                className="rounded border-input accent-red-600"
              />
              {type}
            </label>
          ))}
        </div>
      </div>

      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
          {labels.actors}
        </h3>
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 size-3.5 text-muted-foreground" />
          <input
            type="text"
            placeholder={labels.searchActor}
            value={actor ?? ''}
            onChange={(e) => setActor(e.target.value || null)}
            className="w-full rounded-md border border-input bg-background pl-8 pr-7 py-1.5 text-sm text-foreground placeholder:text-muted-foreground"
          />
          {actor && (
            <button
              className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              onClick={() => setActor(null)}
            >
              <X className="size-3.5" />
            </button>
          )}
        </div>
      </div>

      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
          {labels.granularity}
        </h3>
        <div className="flex gap-1">
          {(['day', 'week', 'month'] as const).map((g) => (
            <Button
              key={g}
              size="sm"
              variant={granularity === g ? 'default' : 'outline'}
              onClick={() => setGranularity(g)}
              className="flex-1 capitalize text-xs"
            >
              {g === 'day' ? labels.day : g === 'week' ? labels.week : labels.month}
            </Button>
          ))}
        </div>
      </div>
    </aside>
  )
}
