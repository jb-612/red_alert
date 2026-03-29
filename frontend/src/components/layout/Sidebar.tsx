import { useFilterStore } from '@/store/filters'
import { useLabels } from '@/lib/labels'
import { Button } from '@/components/ui/button'

export function Sidebar() {
  const labels = useLabels()
  const {
    dateRange, categories, location, granularity,
    comparisonMode, comparisonRange,
    setDateRange, setCategories, setLocation, setGranularity,
    setComparisonMode, setComparisonRange,
  } = useFilterStore()

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
          <input
            type="date"
            value={dateRange.from ?? ''}
            onChange={(e) => setDateRange(e.target.value || null, dateRange.to)}
            className="w-full rounded-md border border-input bg-background px-3 py-1.5 text-sm text-foreground"
          />
          <input
            type="date"
            value={dateRange.to ?? ''}
            onChange={(e) => setDateRange(dateRange.from, e.target.value || null)}
            className="w-full rounded-md border border-input bg-background px-3 py-1.5 text-sm text-foreground"
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
            <input
              type="date"
              value={comparisonRange.from ?? ''}
              onChange={(e) => setComparisonRange(e.target.value || null, comparisonRange.to)}
              className="w-full rounded-md border border-input bg-background px-3 py-1.5 text-sm text-foreground"
            />
            <input
              type="date"
              value={comparisonRange.to ?? ''}
              onChange={(e) => setComparisonRange(comparisonRange.from, e.target.value || null)}
              className="w-full rounded-md border border-input bg-background px-3 py-1.5 text-sm text-foreground"
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
          {labels.locationSearch}
        </h3>
        <input
          type="text"
          placeholder={labels.searchPlaceholder}
          value={location ?? ''}
          onChange={(e) => setLocation(e.target.value || null)}
          className="w-full rounded-md border border-input bg-background px-3 py-1.5 text-sm text-foreground placeholder:text-muted-foreground"
        />
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
