import { ChevronRight } from 'lucide-react'
import { useFilterStore } from '@/store/filters'
import { useLabels } from '@/lib/labels'

export function RegionBreadcrumb() {
  const { drillPath, popDrill, resetDrill } = useFilterStore()
  const labels = useLabels()

  if (drillPath.length === 0) return null

  return (
    <nav className="flex items-center gap-1 text-sm px-1 py-2">
      <button
        className="text-muted-foreground hover:text-foreground transition-colors font-medium"
        onClick={resetDrill}
      >
        {labels.israel}
      </button>
      {drillPath.map((segment, index) => (
        <span key={index} className="flex items-center gap-1">
          <ChevronRight className="size-3.5 text-muted-foreground" />
          {index < drillPath.length - 1 ? (
            <button
              className="text-muted-foreground hover:text-foreground transition-colors font-medium"
              onClick={() => popDrill(index)}
            >
              {segment}
            </button>
          ) : (
            <span className="text-foreground font-medium">{segment}</span>
          )}
        </span>
      ))}
    </nav>
  )
}
