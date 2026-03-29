# Middle East Alert & Conflict Datasets — 2026 Iran War Focus

Research date: 2026-03-29

## Overview

This document catalogs publicly available datasets and data sources for military alerts,
airstrikes, and conflict events across the Middle East, with focus on the 2026 Iran war
(started February 28, 2026) and surrounding countries: Jordan, Lebanon, Syria, Iraq, UAE,
Saudi Arabia, Bahrain, Yemen, Oman, Qatar, Kuwait, and Iran.

The goal is to identify datasets that can complement the existing Israeli OREF/Tzofar alert
data in the Red Alert Analytics Dashboard, enabling a regional view of the conflict.

---

## Tier 1: Structured Conflict Event Data (APIs / Downloads)

### 1.1 ACLED — Daily Iran & Regional Conflict Data (RECOMMENDED)

- **URL:** https://acleddata.com/curated/data-us-iran-regional-conflict-daily
- **Crisis Hub:** https://acleddata.com/iran-crisis-live
- **Country Page:** https://acleddata.com/country/iran
- **Data Export Tool:** https://acleddata.com/conflict-data (interactive, filter by country/date/event)
- **Format:** CSV download, JSON via REST API
- **Update Frequency:** Daily at 3:30pm CET (crisis data); weekly (standard)
- **Geo-Blocked:** No
- **Access:** myACLED account (Google Auth via bellisha@mail.tau.ac.il)
- **Coverage:** Feb 28, 2026 to present; all countries in the conflict theater
- **Scale:** 2,800+ distinct events across 29 of Iran's 31 provinces as of late March 2026
- **Key Stats (via Bloomberg/ACLED analysis through March 13):**
  - 823 documented Iranian airstrikes (483 intercepted)
  - 1,879 US/Israeli strikes (1,661 Israeli, 218 US; 73 intercepted)

#### ACLED API Details

**Authentication (OAuth):**
```bash
# Step 1: Get access token (valid 24h)
curl -X POST https://acleddata.com/oauth/token \
  -d "username=bellisha@mail.tau.ac.il" \
  -d "password=<PASSWORD>" \
  -d "grant_type=password" \
  -d "client_id=acled"

# Returns: { "access_token": "...", "refresh_token": "..." (valid 14 days) }
```

**Data Endpoint:**
```bash
# Step 2: Query data with Bearer token
curl -H "Authorization: Bearer <ACCESS_TOKEN>" \
  "https://acleddata.com/api/acled/read?event_date=2026-02-28&event_date_where=%3E%3D&country=Iran|Israel|Jordan|Lebanon|Syria|Iraq|United%20Arab%20Emirates|Saudi%20Arabia|Bahrain|Yemen|Oman|Qatar|Kuwait&limit=0"
```

**Key API Parameters:**
| Parameter | Description | Example |
|-----------|-------------|---------|
| `event_date` | Filter by date | `2026-02-28` |
| `event_date_where` | Date operator | `>=`, `BETWEEN` |
| `country` | Country filter (pipe-delimited) | `Iran\|Israel\|Jordan` |
| `event_type` | Event type filter | `Battles\|Explosions/Remote violence` |
| `fields` | Select specific columns | `event_date\|country\|latitude\|longitude\|fatalities` |
| `limit` | Row limit (default 5000, 0=all) | `0` |

**CSV Data Fields (Codebook: https://acleddata.com/methodology/acled-codebook):**
| Column | Description | Maps To (Red Alert) |
|--------|-------------|---------------------|
| `event_id_cnty` | Unique event ID | — |
| `event_date` | Date of event | `alert_datetime` |
| `event_type` | 6 types (Battles, Explosions/Remote violence, etc.) | `category` |
| `sub_event_type` | 25 sub-types (Air/drone strike, Shelling, etc.) | `category` (detailed) |
| `actor1` | Primary actor | `raw_data` |
| `actor2` | Secondary actor | `raw_data` |
| `country` | Country name | — |
| `admin1` | First admin division | — |
| `admin2` | Second admin division | — |
| `admin3` | Third admin division | — |
| `location` | Location name | `location_name` |
| `latitude` | Latitude | `lat` |
| `longitude` | Longitude | `lng` |
| `fatalities` | Reported fatalities | — (new field) |
| `source` | Source of report | `raw_data` |
| `notes` | Event description | `raw_data` |
| `tags` | Structured metadata tags | — |
| `geo_precision` | Spatial precision (1=exact, 2=near, 3=wide) | — |
| `time_precision` | Temporal precision (1=exact day, 2=week, 3=month) | — |
| `interaction` | Interaction code (actor types) | — |
| `region` | ACLED region name | — |
| `year` | Year | — |

- **Integration Notes:** Best candidate for automated ingestion. Structured CSV/API with
  lat/lng coordinates matches our existing data model. Free tier sufficient for research.
  OAuth tokens expire in 24h — need refresh token rotation in ingestion pipeline.

### 1.2 GDELT Project

- **URL:** https://www.gdeltproject.org
- **Raw Files:** http://data.gdeltproject.org/events/
- **Format:** CSV (tab-delimited), Google BigQuery (free tier)
- **Update Frequency:** Every 15 minutes
- **Geo-Blocked:** No
- **Access:** Free, no registration
- **Coverage:** Global, 1979-present (v1.0), 2015-present (v2.0 with 15-min updates)
- **Data Fields:** Actors (CAMEO codes), event type, Goldstein scale, geographic coordinates, source URLs
- **BigQuery Example:**
  ```sql
  SELECT * FROM gdeltv2.events
  WHERE ActionGeo_CountryCode IN ('IR', 'IS', 'JO', 'LB', 'SY', 'IZ', 'AE', 'SA', 'BA', 'YM', 'MU', 'QA', 'KU')
  AND SQLDATE >= '20260228'
  AND EventRootCode IN ('19', '20')  -- Military force, unconventional mass violence
  ```
- **Integration Notes:** Highest update frequency but noisiest (media-derived, not verified).
  Good for correlating media coverage with ACLED/OREF events. Free BigQuery access.

### 1.3 UCDP — Uppsala Conflict Data Program

- **URL:** https://ucdp.uu.se
- **API:** https://ucdpapi.pcr.uu.se/
- **Format:** CSV, Excel, REST API
- **Update Frequency:** Monthly (Candidate Events Dataset); annual (main dataset)
- **Geo-Blocked:** No
- **Access:** Free download
- **Coverage:** 1946-present; Candidate dataset has near-current data
- **Data Fields:** conflict_id, actors, location, date, fatality estimates (best/low/high)
- **Integration Notes:** Academic gold standard but slower updates. More conservative coding
  than ACLED. Use for validation rather than real-time tracking.

---

## Tier 2: OSINT Datasets & GitHub Repositories

### 2.1 danielrosehill/Iran-Israel-War-2026-OSINT-Data (RECOMMENDED)

- **GitHub:** https://github.com/danielrosehill/Iran-Israel-War-2026-OSINT-Data
- **Also on:** Kaggle, Hugging Face
- **Format:** JSON (with JSON Schema validation), Neo4j graph database
- **Coverage:** Iranian aerial attacks on Israel/US/coalition, 2024-2026 (4 rounds)
- **Directory Structure:**
  ```
  data/tp1-2024/waves.json    # Round 1, 2 waves
  data/tp2-2024/waves.json    # Round 2, 2 waves
  data/tp3-2025/waves.json    # Round 3, 22 waves
  data/tp4-2026/waves.json    # Round 4, 29 waves (current conflict)
  tp4-2026/reference/         # Targets, bases, vessels, launch zones
  reference/                  # Shared reference data
  schema/wave.schema.json     # JSON Schema for validation
  ```
- **Graph Model:** Property graph on Neo4j Aura: War -> Round -> Salvo, with
  Side/Actor hierarchy, weapons, defense systems, targets, 210 entity international reactions
- **Data Quality:** AI-assisted research + news + OSINT. Contains approximate timestamps.
  Munitions counts and casualties are estimates.
- **License:** Open source with ethical use restrictions
- **Integration Notes:** JSON format directly compatible with our ingestion pipeline.
  Schema available for validation. Best source for Iranian attack wave details.

### 2.2 Shor73/war-israel-usa-vs-iran-monitor

- **GitHub:** https://github.com/Shor73/war-israel-usa-vs-iran-monitor
- **Format:** JavaScript dashboard with embedded data
- **Features:**
  - Tzeva Adom (OREF) live alert feed via relay server
  - Casualty tracker by nation (Iran 1,800+, Israel 340+, Lebanon 180+, Yemen 80+, USA 6)
  - Military briefing style DTG timestamps, NATO terminology
  - Economic impact: live oil prices, defense stocks, chokepoint monitoring (Hormuz, Bab-el-Mandeb, Suez)
- **Fallback Data:** Works without API keys using hardcoded D+5 data
- **Integration Notes:** Useful reference for dashboard design. Casualty data could
  cross-reference with ACLED. OREF relay approach worth studying.

### 2.3 austinhollan/iran-conflict-monitor

- **GitHub:** https://github.com/austinhollan/iran-conflict-monitor
- **Format:** Dashboard with embedded data
- **Data:** 60+ verified news items, 71 military strikes with coordinates, 53 military asset deployments
- **Integration Notes:** Small but geocoded strike dataset. Could supplement ACLED data.

### 2.4 danielrosehill/Iran-Israel-War-OSINT

- **GitHub:** https://github.com/danielrosehill/Iran-Israel-War-OSINT
- **Focus:** Retrospective analysis of pre-war signals (June 2025 onward)
- **Integration Notes:** Useful for historical context, not real-time data.

---

## Tier 3: Institutional Dashboards & Trackers

### 3.1 INSS — Lion's Roar Dashboard

- **Dashboard:** https://www.inss.org.il/publication/lions-roar-data/
- **Interactive Map:** https://www.inss.org.il/publication/lions-roar-map/
- **Survey Data:** https://www.inss.org.il/publication/survey-lions-roar-2/ (downloadable)
- **Format:** Interactive web (no API found)
- **Coverage:** Feb 28, 2026 to present; Israeli/US strikes on Iran + Iranian strikes on Arab nations
- **Map Layers:** US force deployments, Iranian military facilities, comparative Operation Rising Lion overlay
- **Integration Notes:** Authoritative Israeli source. No API — would need scraping.
  Survey data is downloadable.

### 3.2 Critical Threats / ISW Daily Updates

- **URL:** https://www.criticalthreats.org/ (search "Iran Update")
- **Format:** HTML reports with interactive maps
- **Update Frequency:** Daily (was twice daily early in conflict)
- **Coverage:** US/Israeli strikes, Iranian responses, regional spillover
- **Interactive Maps:** Total strikes in Iran, daily timelapse, terrain control (Syria), protest locations
- **Integration Notes:** Excellent analytical source but unstructured HTML. No data download.
  Interactive maps may have underlying data accessible via browser dev tools.

### 3.3 Al Jazeera Live Trackers

- **Death Toll Tracker:** https://www.aljazeera.com/news/2026/3/1/us-israel-attacks-on-iran-death-toll-and-injuries-live-tracker
- **Attack Evolution Map:** https://www.aljazeera.com/news/2026/3/16/map-shows-how-16-days-of-attacks-have-evolved-in-us-israel-war-on-iran
- **Format:** Interactive web
- **Integration Notes:** Visual reference only. No structured export.

### 3.4 IranWarLive.com

- **URL:** https://iranwarlive.com
- **Description:** Automated OSINT engine on serverless infrastructure
- **Sources:** Reuters, AP, Al Jazeera, CENTCOM, state defense wires
- **Features:** Automated civilian vs military casualty breakdown from official reports
- **Format:** Web (no API documentation found)
- **Integration Notes:** Claims to be data-driven and automated. Worth monitoring for API availability.

### 3.5 Open Source Munitions Portal (OSMP)

- **URL:** https://osmp.ngo/collection/the-iran-war-2026/
- **Format:** Web (images + metadata)
- **Coverage:** Munitions used by all parties, expert-reviewed
- **Integration Notes:** Specialized — useful for weapons categorization, not event tracking.

### 3.6 Airwars

- **URL:** https://airwars.org
- **Data Portal:** https://airwars.org/data/
- **Format:** CSV downloads, interactive maps
- **Coverage:** Historically Iraq, Syria, Libya, Yemen, Somalia; likely expanded to Iran
- **Key Finding:** Documented first acknowledged civilian death from AI-assisted US strike (March 10, 2026)
- **Integration Notes:** Gold standard for civilian casualty data. Check for Iran-specific
  data exports.

### 3.7 HRANA (Human Rights Activists in Iran)

- **Format:** Reports
- **Key Stats (by March 17, 2026):**
  - 3,114 deaths documented
  - 1,354 civilians, 1,138 military, 622 unclassified
  - At least 15% of casualties under age 18
- **Integration Notes:** Important civilian impact source. Unstructured reports — would need NLP extraction.

---

## Tier 4: US Military / Government Sources

### 4.1 CENTCOM Press Releases

- **URL:** https://www.centcom.mil/MEDIA/PRESS-RELEASES/
- **RSS:** https://www.centcom.mil/RSS/
- **Format:** HTML, RSS
- **Key Data Points Published:**
  - ~900 strikes in first 12 hours
  - 1,000+ targets by Day 2
  - ~250 strikes/day average by mid-March
  - 6,000-7,000+ cumulative targets by March 16
  - 20+ distinct weapons systems (Tomahawk, PrSM, LUCAS, MQ-9, F/A-18, F-35, Patriot, THAAD)
  - 11 Iranian vessels sunk in Gulf of Oman
  - 90% decline in Iranian ballistic missile attacks (per CENTCOM Commander, March 5)
- **Integration Notes:** Authoritative but unstructured. Would need web scraping + NLP to
  extract structured strike data. RSS feed enables automated monitoring.

### 4.2 Department of Defense

- **Press:** https://www.defense.gov/News/Releases/
- **FOIA:** https://open.defense.gov/ and https://www.esd.whs.mil/FOIA/Reading-Room/
- **CENTCOM FOIA:** https://www.centcom.mil/FOIA/
- **Format:** HTML, PDF
- **Integration Notes:** FOIA data lags by months-years. Press releases same as CENTCOM.

### 4.3 US Congressional Research Service (CRS)

- **URL:** https://crsreports.congress.gov/
- **Mirror:** https://sgp.fas.org/crs/
- **Format:** PDF
- **Integration Notes:** Detailed policy analysis, not raw data. Useful for context.

### 4.4 UK House of Commons Library

- **URL:** https://commonslibrary.parliament.uk/research-briefings/cbp-10521/
- **Format:** PDF, web
- **Coverage:** Consolidated briefing on US-Israel strikes, Feb/March 2026
- **Integration Notes:** Good summary source with consolidated figures.

---

## Tier 5: Gulf State Civil Defense Systems

As of March 2026, all Gulf states have activated civil defense alert systems in response
to Iranian attacks. **No public APIs have been found for any of these systems.**

### Country-by-Country Status

| Country | Alert System Active | Attacks Received | Public API | Data Available Via |
|---------|-------------------|------------------|------------|-------------------|
| **UAE** | Yes (Defense Ministry) | 398 ballistic missiles, 1,872 drones, 15 cruise missiles intercepted; 11 killed | No | ACLED, news reports |
| **Saudi Arabia** | Yes (state TV alerts) | Drone attacks on Ras Tanura refinery, eastern oil region | No | ACLED, news reports |
| **Bahrain** | Yes (Interior Ministry sirens) | Fire in Muharraq from Iranian attack; US 5th Fleet base targeted | No | ACLED, news reports |
| **Kuwait** | Yes (Civil Defense) | Interceptions near Rumaithiya/Salwa; smoke near US embassy | No | ACLED, news reports |
| **Qatar** | Yes | Al Udeid Air Base hit; 44 missiles + 8 UAVs on Feb 28; airport attacked | No | ACLED, news reports |
| **Jordan** | Yes (military) | Muwaffaq Salti Air Base THAAD radar damaged | No | ACLED, news reports |
| **Oman** | Unknown | Included in EASA airspace advisory | No | ACLED, news reports |
| **Yemen** | Active conflict (Houthis) | Houthi participation in attacks on Israel/Gulf | No | ACLED, news reports |

### US Bases in the Region (Attacked)

| Base | Country | Status |
|------|---------|--------|
| Al Udeid Air Base | Qatar | Attacked; radar system damaged |
| NSA Bahrain / 5th Fleet | Bahrain | Targeted |
| Camp Arifjan | Kuwait | Near attack zone |
| Al Dhafra Air Base | UAE | In threat area |
| Muwaffaq Salti Air Base | Jordan | THAAD radar damaged (satellite confirmed March 2) |
| Ain al-Assad / Erbil | Iraq | Retaliatory attacks reported |

---

## Tier 6: Humanitarian & Academic Data

| Source | URL | Format | Focus |
|--------|-----|--------|-------|
| **HDX / OCHA** | https://data.humdata.org (search: Iran, Middle East) | CSV, JSON, API (CKAN) | Displacement, casualties, infrastructure damage |
| **UNHCR** | https://data.unhcr.org/en/documents/details/121558 | Documents | Middle East Situation report (March 13, 2026) |
| **SNU Asia Center** | https://snuac.snu.ac.kr/eng/index.php/2026/03/23/news-aric/ | Web platform | "Understanding the Iran War Through Data" — state capacity, markets, governance |
| **SIPRI** | https://www.sipri.org/databases | Excel, PDF | Arms transfers, military expenditure (context, not events) |
| **Alma Research Center** | https://israel-alma.org | Analysis | Iranian attack patterns Feb 28 - March 11 |

---

## Tier 7: Real-Time Monitoring (Non-Structured)

### OSINT Aggregator Accounts (Twitter/X)

- @IntelDoge, @sentdefender, @AuroraIntel, @OSINTdefender, @ELINTNews, @RedAlertIsrael
- **Access:** X API (paid tiers). Unstructured text.

### Telegram Channels

- Red Alert bots: @RedAlertIsrael, @tzaboronAlert, @redalert_bot
- Conflict channels: @CIG_telegram, @Middle_East_Spectator
- Iranian state media: IRNA, Fars, Tasnim channels
- **Access:** Telegram API via `telethon` or `pyrogram` Python libraries

### Other Dashboards

- **IranMonitor.org** — OSINT dashboard: news sentiment, X feeds, flight radar, prediction markets, internet connectivity
- **Warboard.live** — Iran-Israel-US conflict monitor
- **war-conflits.com** — Live tracking with GDELT integration (features still rolling out)
- **iranwar.info** — Independent live updates
- **Safe Airspace** (safeairspace.net) — Aviation risk summaries, EASA advisories

---

## Integration Recommendations

### Priority 1: ACLED Daily Data

**Why:** Best structured dataset with daily updates, lat/lng coordinates, event types, and
actor coding. Free registration. CSV/API format matches our pipeline.

**How:**
- Register at https://acleddata.com
- Use curated daily Iran conflict data endpoint
- Ingest CSV into `alerts` table with `source = 'acled'`
- Map ACLED event types to our `alert_categories`
- Dedup by (datetime, location, event_type) — same pattern as OREF

### Priority 2: danielrosehill OSINT Dataset

**Why:** JSON with schema validation, specifically covers Iranian attack waves on Israel/coalition.
Complements OREF data with attacker-side details (weapons, launch zones, targets).

**How:**
- Clone/download from GitHub
- Parse `data/tp4-2026/waves.json` for current conflict
- Cross-reference with OREF alerts by timestamp to correlate attacks with Israeli alerts

### Priority 3: GDELT via BigQuery

**Why:** 15-minute updates, free, covers all countries. Good for gap-filling and correlation.

**How:**
- Query BigQuery with country/date/event-type filters
- Use as supplementary source, not primary (noisy, media-derived)

### Priority 4: CENTCOM RSS Monitoring

**Why:** Authoritative US military source for strike data.

**How:**
- Monitor RSS feed for new releases
- NLP extraction of strike counts, locations, weapons from press release text
- Lower priority due to unstructured format

### Not Yet Viable: Gulf State Alert APIs

No Gulf state has a public civil defense alert API comparable to Israel's OREF.
All Gulf state attack data flows through ACLED event coding and news reports.
Monitor for API emergence as these countries build out civilian alert infrastructure.

---

## Key Statistics Summary (as of March 28, 2026)

| Metric | Value | Source |
|--------|-------|--------|
| Conflict start | February 28, 2026 | Multiple |
| ACLED events documented | 2,800+ across 29 Iranian provinces | ACLED |
| Iranian airstrikes | 823 (483 intercepted) through March 13 | Bloomberg/ACLED |
| US/Israeli strikes | 1,879 (1,661 Israeli, 218 US) through March 13 | Bloomberg/ACLED |
| CENTCOM cumulative targets | 7,000+ by March 16 | CENTCOM |
| Iran deaths (HRANA) | 3,114 (1,354 civilian, 1,138 military, 622 unclassified) by March 17 | HRANA |
| UAE interceptions | 398 ballistic missiles, 1,872 drones, 15 cruise missiles | UAE Defense Ministry |
| Countries with active alerts | Israel, UAE, Saudi Arabia, Bahrain, Kuwait, Qatar, Jordan | Multiple |
| Countries with public alert APIs | Israel only (OREF, Tzofar) | This research |
