# Red Alert Analytics Dashboard — Architecture Design

## Overview

An analytics dashboard providing insights into Israel's Home Front Command (OREF) alert history. Visualizes alert patterns by time, geography, category, and frequency.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Analytics Dashboard (Web UI)              │
│         Charts · Maps · Filters · Aggregations              │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────┐
│                      API Layer                               │
│           REST endpoints for dashboard queries               │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────┐
│                    Storage Layer                             │
│              PostgreSQL / TimescaleDB                        │
│         alerts · locations · categories                      │
└──────────────┬───────────────────────────┬──────────────────┘
               │                           │
┌──────────────┴──────────┐  ┌─────────────┴──────────────────┐
│   Historical Backfill   │  │     Ongoing Ingestion          │
│                         │  │                                 │
│ dleshem/israel-alerts-  │  │ Tzofar REST API (no geo-block) │
│ data CSV download       │  │ + OREF GetAlarmsHistory.aspx   │
│                         │  │   (from Israeli IP if avail)   │
└─────────────────────────┘  │ + Tzofar WebSocket (real-time) │
                             └─────────────────────────────────┘
```

## Data Flow

### Phase 1: Historical Backfill
1. Download `dleshem/israel-alerts-data` CSV (comprehensive, 52.7 MB)
2. Parse and normalize into database schema
3. Enrich with geo-coordinates from `pikud-haoref-api/cities.json`

### Phase 2: Ongoing Ingestion
1. **Primary:** Poll Tzofar API `https://api.tzevaadom.co.il/alerts-history` every 2 minutes
2. **Secondary (if Israeli IP available):** Query OREF `GetAlarmsHistory.aspx` with date ranges for validation
3. **Real-time (optional):** Connect to Tzofar WebSocket for live updates
4. Deduplicate incoming alerts against existing data by timestamp + location + category

### Phase 3: Analytics & Visualization
1. Pre-compute daily/weekly/monthly aggregations
2. Serve via REST API to frontend dashboard
3. Dashboard renders charts, heatmaps, timelines, geographic maps

## Database Schema

```sql
CREATE TABLE alerts (
    id              SERIAL PRIMARY KEY,
    external_id     VARCHAR(64) UNIQUE,
    alert_datetime  TIMESTAMPTZ NOT NULL,
    location_name   TEXT NOT NULL,
    location_name_en TEXT,
    category        INTEGER NOT NULL,
    category_desc   TEXT,
    latitude        DECIMAL(10, 6),
    longitude       DECIMAL(10, 6),
    source          VARCHAR(20) NOT NULL,  -- 'oref', 'tzofar', 'csv_backfill'
    raw_data        JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_alerts_datetime ON alerts (alert_datetime);
CREATE INDEX idx_alerts_category ON alerts (category);
CREATE INDEX idx_alerts_location ON alerts (location_name);
CREATE INDEX idx_alerts_geo ON alerts (latitude, longitude);

CREATE TABLE locations (
    id              SERIAL PRIMARY KEY,
    name            TEXT UNIQUE NOT NULL,
    name_en         TEXT,
    name_ru         TEXT,
    name_ar         TEXT,
    zone            TEXT,
    zone_en         TEXT,
    latitude        DECIMAL(10, 6),
    longitude       DECIMAL(10, 6),
    countdown_sec   INTEGER,
    shelter_count   INTEGER
);

CREATE TABLE alert_categories (
    id              INTEGER PRIMARY KEY,
    name_he         TEXT NOT NULL,
    name_en         TEXT NOT NULL
);
```

## Dashboard Features

### Core Views
1. **Timeline** — Alert frequency over time (daily/weekly/monthly), filterable by category and region
2. **Geographic Heatmap** — Map of Israel with alert density overlay
3. **Category Breakdown** — Distribution of alert types (rockets, UAVs, infiltration, etc.)
4. **Location Rankings** — Most alerted cities/zones with drill-down
5. **Comparison** — Side-by-side period comparison (e.g., Oct 2023 vs. Oct 2024)

### Filters
- Date range picker
- Alert category multi-select
- Region/zone selector
- Location search

## Technology Stack (TBD)

Options to evaluate:
- **Backend:** Python (FastAPI) or Node.js (Express)
- **Frontend:** React with chart library (Recharts, Victory, or D3)
- **Database:** PostgreSQL with TimescaleDB extension for time-series
- **Maps:** Leaflet or Mapbox GL JS
- **Deployment:** Docker Compose for local dev, GCP for production (me-west1 for OREF API access)

## Key Technical Considerations

1. **UTF-8 BOM:** All OREF responses include BOM bytes — must strip before JSON parsing
2. **Geo-blocking:** OREF API requires Israeli IP. Tzofar API does not. Design ingestion to work with Tzofar alone.
3. **Deduplication:** Same alert may appear in multiple sources. Deduplicate by (datetime, location, category) tuple.
4. **Hebrew text:** Primary data is in Hebrew. Store original Hebrew + English translations where available.
5. **Rate limiting:** No documented OREF rate limits, but poll conservatively (every 60-120s for history).
