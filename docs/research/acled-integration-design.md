# ACLED Integration — Research & High-Level Design

Research date: 2026-03-29

## 1. Problem Statement

The Red Alert Analytics Dashboard currently tracks Israeli OREF alerts only. The 2026 Iran
war (started Feb 28) has created a multi-country conflict across the Middle East — Iran,
Israel, Jordan, Lebanon, Syria, Iraq, UAE, Saudi Arabia, Bahrain, Yemen, Oman, Qatar, Kuwait.

No Gulf state has a public alert API comparable to Israel's OREF. However, **ACLED** (Armed
Conflict Location & Event Data Project) provides structured, geocoded, daily-updated conflict
event data covering all these countries via a REST API.

This document designs the integration of ACLED data into the existing Red Alert pipeline.

---

## 2. ACLED API Technical Specification

### 2.1 Authentication (OAuth 2.0)

The legacy API key system was retired on 15 September 2025. Current auth uses OAuth tokens.

**Account:** bellisha@mail.tau.ac.il (Google Auth via myACLED)

```
POST https://acleddata.com/oauth/token
Content-Type: application/x-www-form-urlencoded

username=<email>&password=<password>&grant_type=password&client_id=acled
```

**Response:**
```json
{
  "token_type": "Bearer",
  "expires_in": 86400,
  "access_token": "...",
  "refresh_token": "..."
}
```

| Token | Lifetime | Renewal |
|-------|----------|---------|
| Access token | 24 hours | Via refresh token |
| Refresh token | 14 days | Re-authenticate |

**Refresh flow:** Same endpoint with `grant_type=refresh_token&refresh_token=<token>&client_id=acled`

### 2.2 Data Endpoint

```
GET https://acleddata.com/api/acled/read
Authorization: Bearer <access_token>
```

**Key query parameters:**

| Parameter | Description | Example |
|-----------|-------------|---------|
| `_format` | Response format | `csv`, `json` (default) |
| `country` | Pipe-delimited country names | `Iran\|Israel\|Lebanon` |
| `region` | ACLED region code | `11` (Middle East) |
| `event_date` | Date filter | `2026-02-28` |
| `event_date_where` | Date operator | `=`, `>`, `<`, `>=`, `BETWEEN` |
| `event_type` | Event type filter | `Explosions/Remote violence` |
| `sub_event_type` | Sub-event type filter | `Air/drone strike` |
| `fields` | Column selection | `event_date\|country\|latitude\|longitude` |
| `limit` | Rows per page (default 5000, 0=all) | `5000` |
| `page` | Pagination (starts at 1) | `1` |
| `inter_num` | Use numeric interaction codes | `1` |
| `iso` | ISO 3166 numeric country code | `364` (Iran) |

**Multiple values:** `country=Iran|Israel|Jordan|Lebanon|Syria|Iraq`
**Date range:** `event_date=2026-02-28|2026-03-29&event_date_where=BETWEEN`
**Modify operator:** Append `_where` to any filter: `fatalities_where=>`

### 2.3 Data Schema (31 columns)

| Column | Type | Description |
|--------|------|-------------|
| `event_id_cnty` | string | Unique event ID (stable across updates) |
| `event_date` | date (YYYY-MM-DD) | Date of event |
| `year` | integer | Year |
| `time_precision` | int (1-3) | 1=exact day, 2=week, 3=month |
| `disorder_type` | string | Political violence / Demonstrations / Strategic developments |
| `event_type` | string | One of 6 types |
| `sub_event_type` | string | One of 25 sub-types |
| `actor1` | string | Primary actor |
| `assoc_actor_1` | string | Associated actors |
| `inter1` | string/int | Actor 1 type code |
| `actor2` | string | Secondary actor |
| `assoc_actor_2` | string | Associated actors |
| `inter2` | string/int | Actor 2 type code |
| `interaction` | string/int | Combined interaction code |
| `civilian_targeting` | string | Whether civilians targeted |
| `iso` | integer | ISO country code |
| `region` | string | Region name |
| `country` | string | Country name |
| `admin1` | string | Province/state |
| `admin2` | string | District |
| `admin3` | string | Sub-district |
| `location` | string | Specific location name |
| `latitude` | float | Latitude |
| `longitude` | float | Longitude |
| `geo_precision` | int (1-3) | 1=exact, 2=near, 3=region |
| `source` | string | Source(s) |
| `source_scale` | string | Local/national/international |
| `notes` | string | Event description |
| `fatalities` | integer | Reported fatalities |
| `tags` | string | Semicolon-separated metadata |
| `timestamp` | integer | Record add/update Unix timestamp |

### 2.4 Event Types & Sub-Event Types

**6 Event Types → 25 Sub-Event Types:**

| Event Type | Disorder Type | Sub-Event Types |
|------------|--------------|-----------------|
| **Battles** | Political violence | Armed clash, Government regains territory, Non-state actor overtakes territory |
| **Explosions/Remote violence** | Political violence | Air/drone strike, Shelling/artillery/missile attack, Remote explosive/landmine/IED, Suicide bomb, Chemical weapon, Grenade |
| **Violence against civilians** | Political violence | Attack, Abduction/forced disappearance, Sexual violence |
| **Riots** | Demonstrations | Violent demonstration, Mob violence |
| **Protests** | Demonstrations | Peaceful protest, Protest with intervention, Excessive force against protesters |
| **Strategic developments** | Strategic developments | Agreement, Arrests, Change to group/activity, Disrupted weapons use, HQ/base established, Looting/property destruction, Non-violent transfer of territory, Other |

### 2.5 Actor Type Codes (inter1/inter2)

| Code | Actor Type |
|------|-----------|
| 1 | State Forces |
| 2 | Rebel Groups |
| 3 | Political Militias |
| 4 | Identity Militias |
| 5 | Rioters |
| 6 | Protesters |
| 7 | Civilians |
| 8 | External/Other Forces |

**Interaction** = smallest two-digit combo (e.g., State(1) vs Rebel(2) = 12).
Use `&inter_num=1` to get numeric values (default changed to text Sept 2024).

### 2.6 Country Names & ISO Codes (Target Countries)

| ACLED Country Name | ISO Code | ACLED Coverage Start |
|--------------------|----------|---------------------|
| Iran | 364 | Jan 2016 |
| Israel | 376 | Jan 2016 |
| Jordan | 400 | Jan 2016 |
| Lebanon | 422 | Jan 2016 |
| Syria | 760 | Jan 2017 |
| Iraq | 368 | Jan 2016 |
| United Arab Emirates | 784 | Jan 2016 |
| Saudi Arabia | 682 | Jan 2015 |
| Bahrain | 048 | Jan 2016 |
| Yemen | 887 | Jan 2015 |
| Oman | 512 | Jan 2016 |
| Qatar | 634 | Jan 2016 |
| Kuwait | 414 | Jan 2016 |
| Palestine | 275 | Jan 2016 |

**Middle East region code:** `11`

### 2.7 Rate Limits & Update Schedule

- **No documented numeric rate limits** (no requests/minute cap)
- **Default row limit:** 5000 per request
- **Standard data:** Updated weekly (Monday/Tuesday)
- **Iran crisis data:** Updated **daily at 3:30 PM CET**
- **Living dataset:** Existing events may be retroactively updated (fatalities, actor names)
- **No existing Python SDK** works with the current OAuth system (all PyPI packages use deprecated API keys)

---

## 3. Current Red Alert Architecture (Relevant Parts)

### 3.1 Ingestion Pattern (All Sources Follow This)

```
fetch_[source]_alerts(url) -> list[dict]      # HTTP GET + parse
    ↓
_parse_[source]_response(text) -> list[dict]   # Normalize to standard schema
    ↓
ingest_[source]_alerts(db, url) -> int          # Dedup + INSERT
    ↓
Each dict contains: alert_datetime, location_name, category, category_desc, source
```

### 3.2 Alert Model (Current Schema)

```python
class Alert(Base):
    __tablename__ = "alerts"
    id: int                    # PK
    alert_datetime: datetime   # DateTime(timezone=True), NOT NULL
    location_name: str         # Text, NOT NULL
    category: int              # Integer, NOT NULL
    category_desc: str | None  # Text
    rid: str | None            # String(64), unique
    matrix_id: int | None      # Integer
    source: str                # String(20), NOT NULL, default="csv_backfill"

    # UNIQUE index: (alert_datetime, location_name, category)
```

### 3.3 Deduplication

```python
def alert_exists(db, alert_datetime, location_name, category) -> bool:
    # SELECT on unique index: idx_alerts_dedup
```

### 3.4 Configuration

```python
class Settings(BaseSettings):
    database_url: str = "sqlite:///data/alerts.db"
    tzofar_api_url: str = "https://api.tzevaadom.co.il/alerts-history"
    oref_history_url: str = "..."
    csv_url: str = "..."
    model_config = {"env_prefix": "RED_ALERT_"}
```

### 3.5 CLI

Commands: `backfill`, `seed-categories`, `load-locations`, `serve`

---

## 4. Design Challenges

### 4.1 Schema Mismatch

ACLED data is fundamentally different from OREF alerts:

| Dimension | OREF/Tzofar Alerts | ACLED Events |
|-----------|--------------------|--------------|
| **What** | Civilian warning sirens | Military/political events |
| **Granularity** | Per-siren per-location | Per-event (may cover area) |
| **Location** | Hebrew city name | English location name |
| **Category** | Integer 1-14 (OREF codes) | 6 event types / 25 sub-types (strings) |
| **Datetime** | Exact to the second | Date only (YYYY-MM-DD), precision 1-3 |
| **Coordinates** | Via locations table JOIN | Inline lat/lng per event |
| **Actors** | N/A | actor1, actor2 with type codes |
| **Fatalities** | N/A | Per-event fatality count |
| **Countries** | Israel only | 13+ Middle East countries |
| **Source** | OREF / Tzofar / CSV | Multiple news/OSINT sources |

### 4.2 Category Mapping Problem

Current `category` is an integer (OREF codes 1-14). ACLED uses string event types.
We cannot squeeze ACLED's 25 sub-event types into OREF's 14 categories meaningfully.

**Options:**
- A) Assign ACLED events synthetic category IDs (100+) → breaks existing analytics
- B) Create a new `acled_events` table → clean separation, requires new API endpoints
- C) Map ACLED sub-types to closest OREF categories → lossy, misleading

### 4.3 Location Name Problem

Current locations table has Hebrew names. ACLED uses English location names (e.g., "Tehran"
not "טהרן"). Cross-country locations won't exist in the Israeli locations table.

### 4.4 Deduplication Across Sources

OREF dedup key: `(alert_datetime, location_name, category)` with exact datetime.
ACLED has date-only precision — an ACLED event for "Tehran, 2026-03-01" could correlate
with multiple OREF alerts on that day, but they're fundamentally different records.

### 4.5 OAuth Token Management

Tokens expire in 24h. Need automated refresh, secure credential storage, and graceful
handling of auth failures during ingestion runs.

---

## 5. High-Level Design

### 5.1 Approach: Separate Table with Unified API

**Decision: Option B — new `acled_events` table + new API endpoints.**

Rationale:
- ACLED events are structurally different from civil defense alerts
- Forcing them into the `alerts` table distorts both datasets
- Separate table preserves data fidelity and allows ACLED-specific queries
- Unified API layer can combine both for cross-source analytics
- The existing alerts pipeline remains untouched (zero regression risk)

### 5.2 New Database Model: `AcledEvent`

```python
class AcledEvent(Base):
    __tablename__ = "acled_events"

    id: int                         # PK
    event_id_cnty: str              # ACLED unique ID (e.g., "IRN12345"), UNIQUE
    event_date: date                # Date only (not datetime)
    year: int
    time_precision: int             # 1=exact, 2=week, 3=month
    disorder_type: str              # Political violence / Demonstrations / Strategic developments
    event_type: str                 # 6 types
    sub_event_type: str             # 25 sub-types
    actor1: str | None
    actor2: str | None
    inter1: int | None              # Actor type code 1-8
    inter2: int | None              # Actor type code 1-8
    interaction: int | None         # Combined code
    civilian_targeting: str | None
    country: str                    # Country name (English)
    iso: int                        # ISO 3166 numeric
    region: str
    admin1: str | None              # Province/state
    admin2: str | None              # District
    admin3: str | None
    location: str                   # Location name (English)
    latitude: float | None
    longitude: float | None
    geo_precision: int | None       # 1=exact, 2=near, 3=region
    fatalities: int                 # 0 if unreported
    source: str | None              # ACLED source(s)
    notes: str | None               # Event description
    tags: str | None
    acled_timestamp: int | None     # When ACLED added/updated this record

    # Indexes
    idx_acled_event_id (event_id_cnty) UNIQUE  -- ACLED dedup key
    idx_acled_date (event_date)
    idx_acled_country (country)
    idx_acled_country_date (country, event_date)
    idx_acled_event_type (event_type)
    idx_acled_geo (latitude, longitude)
    idx_acled_sub_event (sub_event_type)
```

**Deduplication:** By `event_id_cnty` (ACLED's own unique ID) — NOT by the OREF
tuple `(datetime, location, category)`. ACLED events are identified differently.

### 5.3 New Configuration

```python
class Settings(BaseSettings):
    # ... existing fields ...

    # ACLED settings
    acled_api_url: str = "https://acleddata.com/api/acled/read"
    acled_token_url: str = "https://acleddata.com/oauth/token"
    acled_username: str = ""    # RED_ALERT_ACLED_USERNAME
    acled_password: str = ""    # RED_ALERT_ACLED_PASSWORD
    acled_client_id: str = "acled"
    acled_countries: str = (
        "Iran|Israel|Jordan|Lebanon|Syria|Iraq"
        "|United Arab Emirates|Saudi Arabia|Bahrain"
        "|Yemen|Oman|Qatar|Kuwait|Palestine"
    )
    acled_region: int = 11      # Middle East
```

**Environment variables:**
```bash
export RED_ALERT_ACLED_USERNAME="bellisha@mail.tau.ac.il"
export RED_ALERT_ACLED_PASSWORD="..."
```

### 5.4 Ingestion Module: `backend/ingestion/acled_client.py`

```
┌─────────────────────────────────────────────────┐
│             AcledTokenManager                    │
│  - authenticate() -> access_token               │
│  - refresh() -> new access_token                │
│  - Caches token, auto-refreshes on 401          │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────┐
│           fetch_acled_events()                    │
│  - Paginated GET to /api/acled/read              │
│  - Filters: region=11, event_date>=start_date    │
│  - Returns list[dict] (all pages)                │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────┐
│          _parse_acled_response()                  │
│  - JSON → list[dict] with typed fields           │
│  - Validates required fields                     │
│  - Converts date strings to date objects         │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────┐
│          ingest_acled_events()                    │
│  - Bulk UPSERT by event_id_cnty                  │
│  - INSERT new events, UPDATE changed events      │
│  - Returns (inserted, updated) counts            │
└─────────────────────────────────────────────────┘
```

**Key differences from OREF/Tzofar pattern:**
1. **OAuth authentication** — Token manager class with refresh logic
2. **Pagination** — ACLED returns max 5000 per request; must loop pages
3. **UPSERT not INSERT** — ACLED retroactively updates events (fatalities, notes)
4. **Dedup by `event_id_cnty`** — Not by `(datetime, location, category)` tuple
5. **Date not datetime** — ACLED events have date-only precision

### 5.5 CLI Command

```
python -m backend ingest-acled [--from-date 2026-02-28] [--to-date 2026-03-29]
```

Default: fetch last 7 days if no dates specified.

### 5.6 New API Endpoints

```
GET /api/acled/events            — List events (filtered, paginated)
GET /api/acled/events/timeline   — Event counts over time (day/week/month)
GET /api/acled/events/by-country — Event counts grouped by country
GET /api/acled/events/by-type    — Event counts grouped by event_type/sub_event_type
GET /api/acled/events/geo        — Geocoded events for map display
GET /api/acled/events/actors     — Top actors with event counts
GET /api/acled/events/fatalities — Fatality aggregations by country/date/type
```

**Shared filter parameters (same pattern as existing `apply_filters()`):**
```
?from_date=2026-02-28
&to_date=2026-03-29
&countries=Iran,Israel,Lebanon
&event_types=Explosions/Remote violence,Battles
&sub_event_types=Air/drone strike
&min_fatalities=1
```

### 5.7 Cross-Source Correlation Endpoint

```
GET /api/analytics/correlation
    ?date=2026-03-01
    &window_hours=24
```

Returns: OREF alerts and ACLED events on the same date, enabling analysis like
"Iranian missile attack (ACLED) → rocket alerts in Israel (OREF)" correlation.

---

## 6. Data Flow Diagram

```
                        ACLED API
                   (OAuth + paginated GET)
                            │
                            ▼
              ┌─────────────────────────┐
              │   AcledTokenManager     │
              │  (token cache + refresh)│
              └────────────┬────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │   fetch_acled_events()  │
              │  (paginate all pages)   │
              └────────────┬────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │  _parse_acled_response()│
              │  (validate + type)      │
              └────────────┬────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │  ingest_acled_events()  │
              │  (UPSERT by event_id)  │
              └────────────┬────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │    acled_events table   │
              └────────────┬────────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
    /api/acled/* endpoints    /api/analytics/correlation
              │                    (JOIN with alerts)
              ▼                         │
         Frontend                       ▼
    (new ACLED dashboard        Unified analytics
     panels + map layers)        (cross-source)
```

---

## 7. File Changes Summary

### New Files

| File | Purpose |
|------|---------|
| `backend/models/acled_event.py` | AcledEvent SQLAlchemy model |
| `backend/ingestion/acled_client.py` | Token manager, fetch, parse, ingest |
| `backend/api/acled.py` | ACLED-specific API endpoints |
| `tests/test_acled_client.py` | Ingestion tests (parse, auth, dedup, pagination) |
| `tests/test_acled_api.py` | API endpoint tests |

### Modified Files

| File | Change |
|------|--------|
| `backend/config.py` | Add ACLED settings (url, credentials, countries, region) |
| `backend/cli.py` | Add `ingest-acled` command |
| `backend/main.py` | Register ACLED API router |
| `backend/database.py` | No change needed (Base.metadata.create_all handles new tables) |
| `backend/api/analytics.py` | Add correlation endpoint |

### Not Modified

| File | Reason |
|------|--------|
| `backend/models/alert.py` | ACLED data goes in separate table |
| `backend/ingestion/tzofar_client.py` | Existing pipeline untouched |
| `backend/ingestion/oref_client.py` | Existing pipeline untouched |
| `backend/ingestion/deduplication.py` | ACLED uses event_id_cnty dedup, not alert_exists() |
| `backend/api/alerts.py` | Existing endpoints serve OREF data only |

---

## 8. Implementation Phases

### Phase 1: Model + Ingestion (Backend Core)
1. Create `AcledEvent` model with indexes
2. Add ACLED settings to `Settings` class
3. Implement `AcledTokenManager` (auth + refresh)
4. Implement `fetch_acled_events()` (paginated fetch)
5. Implement `_parse_acled_response()` (JSON → typed dicts)
6. Implement `ingest_acled_events()` (UPSERT by event_id_cnty)
7. Add `ingest-acled` CLI command
8. Write tests (parse, auth mock, dedup, pagination, error handling)

### Phase 2: API Endpoints
1. Create ACLED router with list/filter/paginate endpoint
2. Add timeline, by-country, by-type, geo endpoints
3. Add actors and fatalities aggregation endpoints
4. Register router in main.py
5. Write API tests

### Phase 3: Cross-Source Analytics
1. Add correlation endpoint (OREF alerts ↔ ACLED events by date)
2. Add combined timeline (both sources on same chart)
3. Add regional heatmap (ACLED events across Middle East)

### Phase 4: Frontend (Separate Effort)
1. ACLED event map (all Middle East countries)
2. Country comparison charts
3. Event type breakdown panels
4. Fatality tracking dashboard
5. Cross-source correlation view

---

## 9. Security Considerations

1. **Credentials:** ACLED username/password stored as env vars (`RED_ALERT_ACLED_USERNAME`,
   `RED_ALERT_ACLED_PASSWORD`), never in code or git
2. **Token caching:** Access tokens cached in memory only, never persisted to disk
3. **Rate limiting:** Implement exponential backoff on 429 responses (even though ACLED
   doesn't document rate limits, they may enforce them)
4. **Input validation:** ACLED data is external — validate all fields before DB insert
5. **SQL injection:** Use parameterized queries (SQLAlchemy ORM handles this)

---

## 10. Open Questions

1. **Google Auth:** bellisha@mail.tau.ac.il uses Google Auth — does ACLED's OAuth endpoint
   accept Google-authenticated accounts for programmatic token requests, or do we need
   to set a separate ACLED password? → **Needs manual testing**
2. **Access tier:** Free myACLED may only provide aggregated data. Do we need a
   Research tier for full disaggregated daily crisis data? → **Check after first API call**
3. **Historical backfill:** Should we ingest all Middle East events from Jan 2024, or
   only from Feb 28, 2026? → **Recommend: from Jan 2024 for context on pre-war baseline**
4. **Update strategy:** ACLED retroactively updates events. Should we re-ingest
   the full date range daily, or only fetch new events? → **Recommend: UPSERT last 30 days
   daily to catch updates, plus incremental new events**
