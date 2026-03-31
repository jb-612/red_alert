import { useState, useMemo, useCallback, useRef, useEffect } from 'react'
import { DeckGL } from '@deck.gl/react'
import { HeatmapLayer } from '@deck.gl/aggregation-layers'
import { ScatterplotLayer } from '@deck.gl/layers'
import Map from 'react-map-gl/maplibre'
import type { MapViewState, PickingInfo } from '@deck.gl/core'
import 'maplibre-gl/dist/maplibre-gl.css'

import { MapControls } from './MapControls'
import PlaybackControls from './PlaybackControls'
import { DrillDownPanel } from '@/components/drilldown/DrillDownPanel'
import { usePlayback } from '@/hooks/usePlayback'
import { useThemeStore } from '@/store/theme'
import type { GeoLocation } from '@/api/client'

function isWebGLAvailable(): boolean {
  try {
    const canvas = document.createElement('canvas')
    return !!(canvas.getContext('webgl2') || canvas.getContext('webgl'))
  } catch {
    return false
  }
}

const INITIAL_VIEW_STATE: MapViewState = {
  latitude: 31.5,
  longitude: 34.8,
  zoom: 7.5,
  pitch: 0,
  bearing: 0,
}

const HEATMAP_COLOR_RANGE: [number, number, number][] = [
  [65, 182, 196],
  [127, 205, 187],
  [199, 233, 180],
  [255, 255, 204],
  [255, 170, 0],
  [240, 59, 32],
]

const MAP_STYLE_DARK = 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json'
const MAP_STYLE_LIGHT = 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json'

interface AlertMapProps {
  data: GeoLocation[]
}

export function AlertMap({ data }: AlertMapProps) {
  const [viewState, setViewState] = useState<MapViewState>(INITIAL_VIEW_STATE)
  const [mode, setMode] = useState<'heatmap' | 'scatter'>('heatmap')
  const [selectedLocation, setSelectedLocation] = useState<GeoLocation | null>(null)
  const [webglOk, setWebglOk] = useState(true)
  const [mapCategories, setMapCategories] = useState<Set<number>>(new Set())
  const checkedWebgl = useRef(false)

  const dark = useThemeStore((s) => s.dark)
  const playback = usePlayback()

  useEffect(() => {
    if (!checkedWebgl.current) {
      checkedWebgl.current = true
      if (!isWebGLAvailable()) setWebglOk(false)
    }
  }, [])

  const handleResetView = useCallback(() => {
    setViewState(INITIAL_VIEW_STATE)
    setSelectedLocation(null)
  }, [])

  const handleClick = useCallback(
    (info: PickingInfo) => {
      if (info.object && mode === 'scatter') {
        setSelectedLocation(info.object as GeoLocation)
      } else {
        setSelectedLocation(null)
      }
    },
    [mode],
  )

  const handleToggleMapCategory = useCallback((id: number) => {
    setMapCategories((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }, [])

  // Use playback geo data when playback has frames, otherwise use the data prop
  const rawLayerData = playback.totalFrames > 0 ? playback.currentGeoData : data
  // Filter by map category selection (scatter mode only)
  const layerData = mode === 'scatter' && mapCategories.size > 0
    ? rawLayerData.filter((d) => d.categories?.some((c) => mapCategories.has(c)) ?? true)
    : rawLayerData

  const layers = useMemo(() => {
    if (mode === 'heatmap') {
      return [
        new HeatmapLayer<GeoLocation>({
          id: 'alert-heatmap',
          data: layerData,
          getPosition: (d) => [d.lng, d.lat],
          getWeight: (d) => d.count,
          radiusPixels: 60,
          intensity: 1,
          threshold: 0.03,
          colorRange: HEATMAP_COLOR_RANGE,
          pickable: false,
        }),
      ]
    }
    const maxCount = Math.max(...layerData.map((d) => d.count), 1)
    return [
      new ScatterplotLayer<GeoLocation>({
        id: 'alert-scatter',
        data: layerData,
        getPosition: (d) => [d.lng, d.lat],
        getRadius: (d) => 2000 + (d.count / maxCount) * 15000,
        getFillColor: (d) => {
          const ratio = d.count / maxCount
          if (ratio > 0.7) return [240, 59, 32, 200]
          if (ratio > 0.4) return [255, 170, 0, 200]
          return [65, 182, 196, 200]
        },
        pickable: true,
        radiusUnits: 'meters',
        stroked: true,
        getLineColor: [255, 255, 255, 120],
        lineWidthMinPixels: 1,
      }),
    ]
  }, [layerData, mode])

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

      <MapControls mode={mode} onModeChange={setMode} onResetView={handleResetView} onStartPlayback={playback.initPlayback} mapCategories={mapCategories} onToggleMapCategory={handleToggleMapCategory} />

      <PlaybackControls
        isPlaying={playback.isPlaying}
        isLoading={playback.isLoading}
        progress={playback.progress}
        currentDate={playback.currentDate}
        currentIndex={playback.currentIndex}
        totalFrames={playback.totalFrames}
        speed={playback.speed}
        onPlay={playback.play}
        onPause={playback.pause}
        onSetSpeed={playback.setSpeed}
        onSeek={playback.seekTo}
      />

      {selectedLocation && (
        <DrillDownPanel location={selectedLocation} onClose={() => setSelectedLocation(null)} />
      )}
    </div>
  )
}
