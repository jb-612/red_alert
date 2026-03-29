import { Flame, Circle, RotateCcw, Timer } from 'lucide-react'
import { useLabels } from '@/lib/labels'

interface MapControlsProps {
  mode: 'heatmap' | 'scatter'
  onModeChange: (mode: 'heatmap' | 'scatter') => void
  onResetView: () => void
  onStartPlayback?: () => void
}

const LEGEND_COLORS = [
  { color: 'rgb(65, 182, 196)' },
  { color: 'rgb(199, 233, 180)' },
  { color: 'rgb(255, 255, 204)' },
  { color: 'rgb(255, 170, 0)' },
  { color: 'rgb(240, 59, 32)' },
]

export function MapControls({ mode, onModeChange, onResetView, onStartPlayback }: MapControlsProps) {
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
