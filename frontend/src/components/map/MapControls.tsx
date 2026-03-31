import { Flame, Circle, RotateCcw, Timer } from 'lucide-react'
import { useLabels } from '@/lib/labels'

const CATEGORY_CHIPS: { id: number; label: string; color: string }[] = [
  { id: 1, label: 'Rockets', color: '#ef4444' },
  { id: 2, label: 'UAV', color: '#f97316' },
  { id: 3, label: 'Infiltration', color: '#eab308' },
  { id: 4, label: 'All Clear', color: '#22c55e' },
  { id: 5, label: 'Earthquake', color: '#6b7280' },
]

interface MapControlsProps {
  mode: 'heatmap' | 'scatter'
  onModeChange: (mode: 'heatmap' | 'scatter') => void
  onResetView: () => void
  onStartPlayback?: () => void
  mapCategories?: Set<number>
  onToggleMapCategory?: (id: number) => void
}

const LEGEND_COLORS = [
  { color: 'rgb(65, 182, 196)' },
  { color: 'rgb(199, 233, 180)' },
  { color: 'rgb(255, 255, 204)' },
  { color: 'rgb(255, 170, 0)' },
  { color: 'rgb(240, 59, 32)' },
]

export function MapControls({ mode, onModeChange, onResetView, onStartPlayback, mapCategories, onToggleMapCategory }: MapControlsProps) {
  const labels = useLabels()

  return (
    <div className="absolute top-3 right-3 flex flex-col gap-2 z-10">
      {/* View mode toggle */}
      <div className="flex rounded-lg bg-card/90 backdrop-blur-sm ring-1 ring-foreground/10 overflow-hidden">
        <button
          className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium transition-colors ${
            mode === 'heatmap'
              ? 'bg-primary text-primary-foreground'
              : 'text-muted-foreground hover:text-foreground'
          }`}
          onClick={() => onModeChange('heatmap')}
        >
          <Flame className="size-3.5" />
          {labels.heatmap}
        </button>
        <button
          className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium transition-colors ${
            mode === 'scatter'
              ? 'bg-primary text-primary-foreground'
              : 'text-muted-foreground hover:text-foreground'
          }`}
          onClick={() => onModeChange('scatter')}
        >
          <Circle className="size-3.5" />
          {labels.scatter}
        </button>
      </div>

      {/* Reset view button */}
      <button
        className="flex items-center gap-1.5 rounded-lg bg-card/90 backdrop-blur-sm ring-1 ring-foreground/10 px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
        onClick={onResetView}
      >
        <RotateCcw className="size-3.5" />
        {labels.resetView}
      </button>

      {/* Time-lapse button */}
      {onStartPlayback && (
        <button
          className="flex items-center gap-1.5 rounded-lg bg-card/90 backdrop-blur-sm ring-1 ring-foreground/10 px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
          onClick={onStartPlayback}
        >
          <Timer className="size-3.5" />
          {labels.timelapse}
        </button>
      )}

      {/* Category filter (scatter mode only) */}
      {mode === 'scatter' && mapCategories && onToggleMapCategory && (
        <div className="rounded-lg bg-card/90 backdrop-blur-sm ring-1 ring-foreground/10 p-2">
          <p className="text-[10px] font-medium text-muted-foreground mb-1.5">Filter by type</p>
          <div className="flex flex-col gap-1">
            {CATEGORY_CHIPS.map((cat) => {
              const active = mapCategories.size === 0 || mapCategories.has(cat.id)
              return (
                <button
                  key={cat.id}
                  className="flex items-center gap-1.5 px-2 py-0.5 text-[10px] rounded transition-opacity"
                  style={{ opacity: active ? 1 : 0.35 }}
                  onClick={() => onToggleMapCategory(cat.id)}
                >
                  <span className="inline-block size-2 rounded-full" style={{ backgroundColor: cat.color }} />
                  <span className="text-foreground">{cat.label}</span>
                </button>
              )
            })}
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="rounded-lg bg-card/90 backdrop-blur-sm ring-1 ring-foreground/10 p-2.5">
        <p className="text-[10px] font-medium text-muted-foreground mb-1.5">{labels.alertDensity}</p>
        <div className="flex items-center gap-0.5">
          {LEGEND_COLORS.map((entry, i) => (
            <div
              key={i}
              className="h-2.5 flex-1 first:rounded-l last:rounded-r"
              style={{ backgroundColor: entry.color }}
            />
          ))}
        </div>
        <div className="flex justify-between mt-1">
          <span className="text-[9px] text-muted-foreground">{labels.low}</span>
          <span className="text-[9px] text-muted-foreground">{labels.high}</span>
        </div>
      </div>
    </div>
  )
}
