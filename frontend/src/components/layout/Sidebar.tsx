import { useState, useEffect, useCallback, useRef } from 'react'
import { CalendarIcon, Search, X } from 'lucide-react'
import { format, parse } from 'date-fns'
import { useFilterStore } from '@/store/filters'
import { useLabels } from '@/lib/labels'
import { Button } from '@/components/ui/button'
import { Popover, PopoverTrigger, PopoverContent } from '@/components/ui/popover'
import { Calendar } from '@/components/ui/calendar'
import { api } from '@/api/client'
import type { LocationSearchResult, ZoneInfo } from '@/api/client'

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

function LocationAutocomplete({ value, onChange }: { value: string | null; onChange: (v: string | null) => void }) {
  const labels = useLabels()
  const [query, setQuery] = useState(value ?? '')
  const [results, setResults] = useState<LocationSearchResult[]>([])
  const [showDropdown, setShowDropdown] = useState(false)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    setQuery(value ?? '')
  }, [value])

  const doSearch = useCallback((q: string) => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    if (q.length === 0) {
      setResults([])
      setShowDropdown(false)
      return
    }
    debounceRef.current = setTimeout(() => {
      api.searchLocations(q, 15).then((res) => {
        setResults(res)
        setShowDropdown(res.length > 0)
      }).catch(() => {
        setResults([])
      })
    }, 200)
  }, [])

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setShowDropdown(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  return (
    <div ref={containerRef} className="relative">
      <div className="relative">
        <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 size-3.5 text-muted-foreground" />
        <input
          type="text"
          placeholder={labels.searchPlaceholder}
          value={query}
          onChange={(e) => {
            const v = e.target.value
            setQuery(v)
            doSearch(v)
            if (v === '') onChange(null)
          }}
          onFocus={() => { if (results.length > 0) setShowDropdown(true) }}
          className="w-full rounded-md border border-input bg-background pl-8 pr-7 py-1.5 text-sm text-foreground placeholder:text-muted-foreground"
        />
        {query && (
          <button
            className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
            onClick={() => { setQuery(''); onChange(null); setResults([]); setShowDropdown(false) }}
          >
            <X className="size-3.5" />
          </button>
        )}
      </div>
      {showDropdown && (
        <div className="absolute z-50 mt-1 w-full max-h-48 overflow-y-auto rounded-md border border-border bg-popover shadow-md">
          {results.map((loc) => (
            <button
              key={loc.name}
              className="w-full text-start px-3 py-1.5 text-sm text-foreground hover:bg-muted/50 transition-colors"
              onClick={() => {
                setQuery(loc.name)
                onChange(loc.name)
                setShowDropdown(false)
              }}
            >
              <span>{loc.name}</span>
              {loc.name_en && (
                <span className="text-muted-foreground text-xs ml-2">{loc.name_en}</span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

export function Sidebar() {
  const labels = useLabels()
  const {
    dateRange, categories, location, granularity,
    comparisonMode, comparisonRange, region,
    setDateRange, setCategories, setLocation, setGranularity,
    setComparisonMode, setComparisonRange, setRegion,
  } = useFilterStore()

  const [zones, setZones] = useState<ZoneInfo[]>([])

  useEffect(() => {
    api.getZones().then(setZones).catch(() => {})
  }, [])

  const CATEGORIES = [
    { id: 1, name: labels.rockets },
    { id: 2, name: labels.uav },
    { id: 3, name: labels.infiltration },
    { id: 4, name: labels.allClear },
    { id: 5, name: labels.earthquake },
  ]

  function toggleCategory(id: number) {
    if (categories.includes(id)) {
      setCategories(categories.filter((c) => c !== id))
    } else {
      setCategories([...categories, id])
    }
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
          {labels.comparePeriods}
        </h3>
        <Button
          size="sm"
          variant={comparisonMode ? 'default' : 'outline'}
          onClick={() => setComparisonMode(!comparisonMode)}
          className="w-full text-xs"
        >
          {comparisonMode ? labels.comparisonOn : labels.compare}
        </Button>
        {comparisonMode && (
          <div className="mt-2 space-y-2">
            <p className="text-xs text-muted-foreground">{labels.periodB}</p>
            <DatePickerField
              value={comparisonRange.from}
              onChange={(v) => setComparisonRange(v, comparisonRange.to)}
              label="Period B from"
            />
            <DatePickerField
              value={comparisonRange.to}
              onChange={(v) => setComparisonRange(comparisonRange.from, v)}
              label="Period B to"
            />
          </div>
        )}
      </div>

      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
          {labels.categories}
        </h3>
        <div className="space-y-1">
          {CATEGORIES.map((cat) => (
            <label key={cat.id} className="flex items-center gap-2 cursor-pointer text-sm text-foreground">
              <input
                type="checkbox"
                checked={categories.includes(cat.id)}
                onChange={() => toggleCategory(cat.id)}
                className="rounded border-input accent-red-600"
              />
              {cat.name}
            </label>
          ))}
        </div>
      </div>

      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
          Region
        </h3>
        <select
          value={region ?? ''}
          onChange={(e) => setRegion(e.target.value || null)}
          className="w-full rounded-md border border-input bg-background px-3 py-1.5 text-sm text-foreground"
        >
          <option value="">All regions</option>
          {zones.map((z) => (
            <option key={z.zone_en} value={z.zone_en}>
              {z.zone_en} ({z.city_count})
            </option>
          ))}
        </select>
      </div>

      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
          {labels.locationSearch}
        </h3>
        <LocationAutocomplete value={location} onChange={setLocation} />
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
