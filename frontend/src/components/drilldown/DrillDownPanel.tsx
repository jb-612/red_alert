import { useEffect, useState } from 'react'
import { X, MapPin, ArrowRight } from 'lucide-react'
import { api } from '@/api/client'
import type { RegionData, GeoLocation, ZoneHierarchy } from '@/api/client'
import { useFilterStore } from '@/store/filters'

interface DrillDownPanelProps {
  location: GeoLocation
  onClose: () => void
}

function findZoneForLocation(
  location: GeoLocation,
  hierarchy: ZoneHierarchy[],
): ZoneHierarchy | undefined {
  return hierarchy.find((zone) =>
    zone.cities.some((c) => c.name === location.location_name),
  )
}

export function DrillDownPanel({ location, onClose }: DrillDownPanelProps) {
  const [regionData, setRegionData] = useState<RegionData | null>(null)
  const [zone, setZone] = useState<ZoneHierarchy | null>(null)
  const { pushDrill } = useFilterStore()

  useEffect(() => {
    let cancelled = false
    async function load() {
      const hierarchy = await api.getHierarchy()
      const found = findZoneForLocation(location, hierarchy)
      if (cancelled) return
      setZone(found ?? null)
      if (found) {
        const data = await api.getRegionAnalytics(found.zone_en)
        if (!cancelled) setRegionData(data)
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [location])

  const handleDrillIn = () => {
    if (zone) {
      pushDrill(zone.zone)
    }
    pushDrill(location.location_name)
  }

  const totalCategoryCount = regionData
    ? regionData.category_breakdown.reduce((s, c) => s + c.count, 0)
    : 0

  const CATEGORY_COLORS = ['#41b6c4', '#7fcdbb', '#ffaa00', '#f03b20']

  return (
    <div className="absolute bottom-3 left-3 z-10 w-72 rounded-lg bg-card/95 backdrop-blur-sm ring-1 ring-foreground/10 shadow-lg">
      {/* Header */}
      <div className="flex items-start justify-between px-3 pt-3 pb-2">
        <div className="flex items-start gap-2 min-w-0">
          <MapPin className="size-4 mt-0.5 shrink-0 text-muted-foreground" />
          <div className="min-w-0">
            <p className="text-sm font-semibold text-foreground truncate">
              {location.location_name}
            </p>
            {zone && (
              <p className="text-xs text-muted-foreground">
                {zone.zone} / {zone.zone_en}
              </p>
            )}
          </div>
        </div>
        <button
          className="text-muted-foreground hover:text-foreground transition-colors shrink-0"
          onClick={onClose}
        >
          <X className="size-4" />
        </button>
      </div>

      {/* Alert count */}
      <div className="px-3 pb-2">
        <p className="text-2xl font-bold text-foreground tabular-nums">
          {location.count.toLocaleString()}
        </p>
        <p className="text-xs text-muted-foreground">total alerts</p>
      </div>

      {/* Top sub-locations */}
      {regionData && regionData.top_locations.length > 0 && (
        <div className="px-3 pb-2 border-t border-border pt-2">
          <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider mb-1.5">
            Top locations in zone
          </p>
          <ul className="space-y-1">
            {regionData.top_locations.map((sub) => (
              <li key={sub.location_name} className="flex items-center justify-between text-xs">
                <span className="text-foreground truncate">{sub.location_name}</span>
                <span className="text-muted-foreground tabular-nums ml-2">
                  {sub.count.toLocaleString()}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Category breakdown bar */}
      {regionData && totalCategoryCount > 0 && (
        <div className="px-3 pb-2 border-t border-border pt-2">
          <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider mb-1.5">
            Category breakdown
          </p>
          <div className="flex h-3 rounded overflow-hidden gap-px">
            {regionData.category_breakdown.map((cat, i) => (
              <div
                key={cat.category}
                className="h-full transition-all"
                style={{
                  width: `${(cat.count / totalCategoryCount) * 100}%`,
                  backgroundColor: CATEGORY_COLORS[i % CATEGORY_COLORS.length],
                  minWidth: cat.count > 0 ? '4px' : '0',
                }}
              />
            ))}
          </div>
          <div className="flex flex-wrap gap-x-3 gap-y-0.5 mt-1">
            {regionData.category_breakdown.map((cat, i) => (
              <span key={cat.category} className="flex items-center gap-1 text-[10px]">
                <span
                  className="inline-block size-2 rounded-sm"
                  style={{ backgroundColor: CATEGORY_COLORS[i % CATEGORY_COLORS.length] }}
                />
                <span className="text-muted-foreground">{cat.category_desc}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Drill-in button */}
      <div className="px-3 pb-3 pt-1">
        <button
          className="flex items-center justify-center gap-1.5 w-full rounded-md bg-primary text-primary-foreground px-3 py-1.5 text-xs font-medium hover:bg-primary/90 transition-colors"
          onClick={handleDrillIn}
        >
          Drill into {location.location_name}
          <ArrowRight className="size-3.5" />
        </button>
      </div>
    </div>
  )
}
