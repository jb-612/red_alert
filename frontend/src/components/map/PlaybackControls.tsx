import { Pause, Play } from 'lucide-react'
import { format, parseISO } from 'date-fns'
import { useLabels } from '@/lib/labels'

interface PlaybackControlsProps {
  isPlaying: boolean
  isLoading: boolean
  progress: number
  currentDate: string | null
  currentIndex: number
  totalFrames: number
  speed: 1 | 2 | 5
  onPlay: () => void
  onPause: () => void
  onSetSpeed: (s: 1 | 2 | 5) => void
  onSeek: (index: number) => void
}

export default function PlaybackControls({
  isPlaying,
  isLoading,
  progress,
  currentDate,
  currentIndex,
  totalFrames,
  speed,
  onPlay,
  onPause,
  onSetSpeed,
  onSeek,
}: PlaybackControlsProps) {
  const labels = useLabels()

  if (isLoading) {
    return (
      <div className="absolute bottom-3 left-3 right-3 flex items-center gap-3 rounded-lg bg-card/90 px-4 py-3 ring-1 ring-foreground/10 backdrop-blur-sm">
        <div className="flex-1">
          <div className="mb-1 text-xs text-muted-foreground">{labels.loading}... {progress}%</div>
          <div className="h-1.5 overflow-hidden rounded-full bg-muted">
            <div className="h-full rounded-full bg-primary transition-all" style={{ width: `${progress}%` }} />
          </div>
        </div>
      </div>
    )
  }

  if (totalFrames === 0) return null

  return (
    <>
      {/* Date overlay */}
      {currentDate && (
        <div className="absolute top-14 left-1/2 -translate-x-1/2 rounded-lg bg-card/80 px-4 py-2 text-lg font-semibold text-foreground backdrop-blur-sm">
          {format(parseISO(currentDate), 'MMM d, yyyy')}
        </div>
      )}

      {/* Progress bar */}
      <div className="absolute bottom-0 left-0 right-0 h-1 bg-muted/50">
        <div
          className="h-full bg-primary transition-all"
          style={{ width: `${totalFrames > 1 ? (currentIndex / (totalFrames - 1)) * 100 : 0}%` }}
        />
      </div>

      {/* Controls */}
      <div className="absolute bottom-3 left-3 right-3 flex items-center gap-3 rounded-lg bg-card/90 px-4 py-2 ring-1 ring-foreground/10 backdrop-blur-sm">
        <button
          onClick={isPlaying ? onPause : onPlay}
          className="rounded-md p-1.5 text-foreground hover:bg-muted"
        >
          {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
        </button>

        <input
          type="range"
          min={0}
          max={totalFrames - 1}
          value={currentIndex}
          onChange={(e) => onSeek(Number(e.target.value))}
          className="h-1.5 flex-1 cursor-pointer accent-primary"
        />

        <div className="flex gap-1">
          {([1, 2, 5] as const).map((s) => (
            <button
              key={s}
              onClick={() => onSetSpeed(s)}
              className={`rounded px-1.5 py-0.5 text-xs font-medium ${
                speed === s ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              {s}x
            </button>
          ))}
        </div>

        <span className="min-w-[3rem] text-end text-xs text-muted-foreground">
          {currentIndex + 1}/{totalFrames}
        </span>
      </div>
    </>
  )
}
