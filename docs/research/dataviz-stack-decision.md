# Data Visualization Stack Decision

Research date: 2026-03-28

## Chosen Stack

| Role | Library | Why |
|------|---------|-----|
| **Charts** | Apache ECharts 6 (echarts-for-react) | Canvas/WebGL rendering for 500k+ points, built-in dataZoom + brush + drill-down, 20+ chart types |
| **Geographic map** | Deck.gl 9 + MapLibre GL JS + react-map-gl | Only stack handling 500k+ geo points at 60 FPS. GPU-accelerated layers. Free, no API key. |
| **Data tables** | AG Grid (Community) | Virtual scrolling for 100k+ rows, built-in sort/filter/search |
| **UI shell** | shadcn/ui + Tailwind CSS v4 + Radix UI | Industry standard. Buttons, dialogs, date pickers, sidebar, navigation |
| **Dashboard widgets** | Tremor | KPI cards, sparklines, metric summaries |
| **Build** | Vite + React 19 + TypeScript 5 | Instant HMR, no SSR overhead needed for analytics dashboard |
| **State** | Zustand | Lightweight shared filter state across charts/map/tables |

## Why NOT These Alternatives

| Library | Rejected Because |
|---------|-----------------|
| **Plotly.js** | 3MB+ bundle, "scientific paper" aesthetics, inferior performance to ECharts |
| **D3.js (raw)** | Too much effort. SVG chokes above 10k DOM elements. |
| **Nivo** | Good aesthetics but insufficient 500k+ performance ceiling |
| **Recharts** | SVG-only, degrades above 5-10k points. No brush/drill-down. |
| **Observable Plot** | Not React-native. Better for notebooks than dashboards. |
| **Leaflet** | SVG-based, no WebGL. Dies above 10k markers. |
| **Mapbox GL JS** | Proprietary license since v2.0, usage-based pricing. MapLibre does the same for free. |
| **Next.js** | No SSR needed. Vite has faster HMR. WebGL libraries work better without hydration. |
| **Kepler.gl** | Too opinionated (Redux-based). Can't compose into custom dashboard. |

## Key Performance Numbers

- **ECharts 6**: Renders millions of points in <1s. Real-time updates at <30ms for millions of points.
- **Deck.gl HeatmapLayer**: 500k points render in 5-100ms (GPU-accelerated)
- **Deck.gl ScatterplotLayer**: 1M+ points at 60 FPS
- **AG Grid**: 100k+ rows with virtual scrolling
- **Total bundle**: ~2MB (ECharts 800KB + deck.gl 300KB + MapLibre 200KB + AG Grid 500KB + UI 150KB)

## ECharts Key Features for This Project

- **dataZoom**: Slider zoom, inside zoom (mouse wheel/pinch), brush-select zoom
- **Universal Transition** (v5.2+): Click a bar → animated drill-down into sub-categories
- **brush component**: Rectangular/lasso selection on any chart
- **progressive rendering**: Incremental display of large datasets
- **TypedArray support**: Memory-efficient for 500k+ data points
- **i18n**: Hebrew/English bilingual support
- **v6.0**: Dark mode theme tokens, matrix coordinate system

## Deck.gl Key Features for This Project

- **HeatmapLayer**: GPU-accelerated density distribution for alert heatmap
- **ScatterplotLayer**: Individual alert dots with category-based coloring
- **DataFilterExtension** (v9): Filter by categories on GPU — no data re-upload
- **TripsLayer**: Animated temporal paths for time-lapse playback
- Custom time controller: `requestAnimationFrame` + `currentTime` state for playback

## Architecture Pattern

```
Zustand store: { dateRange, categories[], location, region, granularity }
    ↓ (subscribed by all components)
    ├── ECharts (re-fetches API for timeline, category, heatmap data)
    ├── Deck.gl (DataFilterExtension filters on GPU — no re-fetch)
    ├── AG Grid (re-fetches API for alert list)
    └── Tremor KPIs (re-fetches API for summary metrics)
```
