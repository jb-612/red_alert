import { useState, useMemo, useCallback, useRef, useEffect } from 'react'
import { DeckGL } from '@deck.gl/react'
import { ScatterplotLayer } from '@deck.gl/layers'
import Map from 'react-map-gl/maplibre'
import type { MapViewState, PickingInfo } from '@deck.gl/core'
import 'maplibre-gl/dist/maplibre-gl.css'

import { useThemeStore } from '@/store/theme'
import { useLabels } from '@/lib/labels'
import type { AcledGeoPoint } from '@/api/acledClient'

function isWebGLAvailable(): boolean {
  try {
    const canvas = document.createElement('canvas')
    return !!(canvas.getContext('webgl2') || canvas.getContext('webgl'))
  } catch {
    return false
  }
}

const THEATER_COLORS: Record<string, [number, number, number]> = {
  core_me: [239, 68, 68],
  maritime: [59, 130, 246],
  extended_me: [245, 158, 11],
  global_terror: [168, 85, 247],
}

const THEATER_VIEWS: Record<string, { latitude: number; longitude: number; zoom: number }> = {
  core_me: { latitude: 30, longitude: 45, zoom: 5 },
  maritime: { latitude: 25, longitude: 55, zoom: 4 },
  extended_me: { latitude: 38, longitude: 35, zoom: 5 },
  global: { latitude: 30, longitude: 20, zoom: 2 },
}

const INITIAL_VIEW_STATE: MapViewState = {
  latitude: 30,
  longitude: 40,
  zoom: 4,
  pitch: 0,
  bearing: 0,
}

const MAP_STYLE_DARK = 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json'
const MAP_STYLE_LIGHT = 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json'

interface ConflictMapProps {
  data: AcledGeoPoint[]
}

export function ConflictMap({ data }: ConflictMapProps) {
  const [viewState, setViewState] = useState<MapViewState>(INITIAL_VIEW_STATE)
  const [selectedPoint, setSelectedPoint] = useState<AcledGeoPoint | null>(null)
  const [webglOk, setWebglOk] = useState(true)
  const checkedWebgl = useRef(false)

  const dark = useThemeStore((s) => s.dark)
  const labels = useLabels()

  useEffect(() => {
    if (!checkedWebgl.current) {
      checkedWebgl.current = true
      if (!isWebGLAvailable()) setWebglOk(false)
    }
  }, [])

  const handleResetView = useCallback(() => {
    setViewState(INITIAL_VIEW_STATE)
    setSelectedPoint(null)
  }, [])

  const handleClick = useCallback(
    (info: PickingInfo) => {
      if (info.object) {
        setSelectedPoint(info.object as AcledGeoPoint)
      } else {
        setSelectedPoint(null)
      }
    },
    [],
  )

  const handleTheaterView = useCallback((key: string) => {
    const view = THEATER_VIEWS[key]
    if (view) {
      setViewState((prev) => ({ ...prev, ...view }))
    }
  }, [])

  const layers = useMemo(() => {
    return [
      new ScatterplotLayer<AcledGeoPoint>({
        id: 'conflict-scatter',
        data,
        getPosition: (d) => [d.lng, d.lat],
        getRadius: (d) => Math.min(3000 + d.fatalities * 500, 20000),
        getFillColor: () => {
          // Default color for geo-aggregated points
          return [239, 68, 68, 180]
        },
        pickable: true,
        radiusUnits: 'meters',
        stroked: true,
        getLineColor: [255, 255, 255, 120],
        lineWidthMinPixels: 1,
      }),
    ]
  }, [data])

  const mapStyle = dark ? MAP_STYLE_DARK : MAP_STYLE_LIGHT

  if (!webglOk) {
    return (
      <div className="relative h-full w-full flex items-center justify-center bg-muted/50 rounded-lg">
        <p className="text-sm text-muted-foreground">
          WebGL is not available in this browser. Map visualization requires WebGL support.
        </p>
      </div>
    )
  }

  return (
    <div className="relative h-full w-full">
      <DeckGL
        viewState={viewState}
        onViewStateChange={({ viewState: vs }) => setViewState(vs as MapViewState)}
        controller={true}
        layers={layers}
        onClick={handleClick}
        getCursor={({ isHovering }) => (isHovering ? 'pointer' : 'grab')}
      >
        <Map mapStyle={mapStyle} />
      </DeckGL>

      {/* Theater navigation buttons */}
      <div className="absolute top-3 right-3 flex flex-col gap-2 z-10">
        <div className="rounded-lg bg-card/90 backdrop-blur-sm ring-1 ring-foreground/10 p-2">
          <p className="text-[10px] font-medium text-muted-foreground mb-1.5">{labels.theaters}</p>
          <div className="flex flex-col gap-1">
            {Object.entries(THEATER_COLORS).map(([key, color]) => {
              const theaterLabel = key === 'core_me' ? labels.coreME
                : key === 'maritime' ? labels.maritime
                : key === 'extended_me' ? labels.extendedME
                : labels.globalTerror
              return (
                <button
                  key={key}
                  className="flex items-center gap-1.5 px-2 py-0.5 text-[10px] rounded hover:bg-muted/50 transition-colors"
                  onClick={() => handleTheaterView(key === 'global_terror' ? 'global' : key)}
                >
                  <span
                    className="inline-block size-2 rounded-full"
                    style={{ backgroundColor: `rgb(${color[0]},${color[1]},${color[2]})` }}
                  />
                  <span className="text-foreground">{theaterLabel}</span>
                </button>
              )
            })}
          </div>
        </div>

        {/* Reset view */}
        <button
          className="flex items-center gap-1.5 rounded-lg bg-card/90 backdrop-blur-sm ring-1 ring-foreground/10 px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
          onClick={handleResetView}
        >
          {labels.resetView}
        </button>

        {/* Legend */}
        <div className="rounded-lg bg-card/90 backdrop-blur-sm ring-1 ring-foreground/10 p-2.5">
          <p className="text-[10px] font-medium text-muted-foreground mb-1.5">{labels.fatalities}</p>
          <div className="flex items-center gap-0.5">
            <div className="h-2.5 flex-1 rounded-l" style={{ backgroundColor: 'rgb(239,68,68)' }} />
            <div className="h-2.5 flex-1" style={{ backgroundColor: 'rgb(245,158,11)' }} />
            <div className="h-2.5 flex-1 rounded-r" style={{ backgroundColor: 'rgb(59,130,246)' }} />
          </div>
          <div className="flex justify-between mt-1">
            <span className="text-[9px] text-muted-foreground">{labels.low}</span>
            <span className="text-[9px] text-muted-foreground">{labels.high}</span>
          </div>
        </div>
      </div>

      {/* Selected point tooltip */}
      {selectedPoint && (
        <div className="absolute bottom-4 left-4 z-10 max-w-xs rounded-lg bg-card/95 backdrop-blur-sm ring-1 ring-foreground/10 p-3">
          <div className="flex items-start justify-between gap-2">
            <div>
              <p className="text-sm font-semibold text-foreground">{selectedPoint.location}</p>
              <p className="text-xs text-muted-foreground">{selectedPoint.country}</p>
            </div>
            <button
              onClick={() => setSelectedPoint(null)}
              className="text-muted-foreground hover:text-foreground"
            >
              <span className="text-xs">X</span>
            </button>
          </div>
          <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
            <div>
              <p className="text-muted-foreground">{labels.events}</p>
              <p className="font-bold text-foreground">{selectedPoint.count}</p>
            </div>
            <div>
              <p className="text-muted-foreground">{labels.fatalities}</p>
              <p className="font-bold text-red-500">{selectedPoint.fatalities}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
