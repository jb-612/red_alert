# Alternative Data Sources for OREF Alert History

Research date: 2026-03-28

## 1. Tzofar / TzevaAdom (RECOMMENDED — No Geo-Blocking)

**Website:** https://www.tzevaadom.co.il/en/
**Historical archive UI:** https://www.tzevaadom.co.il/en/historical/

### REST API
```
GET https://api.tzevaadom.co.il/alerts-history
```

### WebSocket (Real-Time Push)
```
wss://ws.tzevaadom.co.il/socket?platform=ANDROID
```

### Response Fields
- `date`, `area`, `title`, `icon`, `emoji`, `category`, `district`
- `home_distance`, `latitude`, `longitude`, `channel`
- Multilingual: `name`, `name_en`, `name_ru`, `name_ar`
- Zone: `zone`, `zone_en`, `zone_ru`, `zone_ar`

### Client Libraries
- Python: `pip install tzevaadom`
- JavaScript: `github.com/ZeEitan/TzevaAdom`

**Advantage:** No Israeli IP required. Full archive with graphs, heat maps, and filters since 2022.

## 2. Pre-Built Historical Datasets

### dleshem/israel-alerts-data (BEST FOR BACKFILL)
- **URL:** https://github.com/dleshem/israel-alerts-data
- **Format:** CSV, 52.7 MB
- **Updates:** 8,831 commits (automated, actively maintained)
- **License:** Apache-2.0
- **Coverage:** Comprehensive historical alert data

### yuval-harpaz/alarms
- **URL:** https://github.com/yuval-harpaz/alarms
- **Format:** Various (includes visualizations and maps)
- **Updates:** 40,563 commits (automated)
- **Coverage:** Rocket/mortar alarms since 2019

### Kaggle — Rocket Alerts
- **URL:** https://www.kaggle.com/datasets/sab30226/rocket-alerts-in-israel-made-by-tzeva-adom
- **License:** CC BY-SA 4.0
- **Coverage:** Historical dataset (2013-2014 era)

### Hugging Face — Israel-Alerting-Zones
- **URL:** https://huggingface.co/datasets/danielrosehill/Israel-Alerting-Zones
- **Format:** Zone definitions (~1,500 zones with Hebrew/English names)
- **Snapshot:** May 2025

## 3. Third-Party Mirrors

### Mako (Israeli News)
```
GET https://www.mako.co.il/Collab/amudanan/alerts.json
```
May or may not be geo-blocked.

### Prog.co.il
```
GET https://www.prog.co.il/pakar-tests.php?a=3
```

## 4. Community Libraries & Wrappers

| Language | Project | URL | Status |
|----------|---------|-----|--------|
| Node.js | pikud-haoref-api | github.com/eladnava/pikud-haoref-api | Active (Mar 2026) |
| Python | python-red-alert | github.com/Zontex/python-red-alert | Active |
| Java/Docker | oref-alerts-proxy-ms | github.com/dmatik/oref-alerts-proxy-ms | Low maintenance |
| C# | RedAlert | github.com/Enum0x539/RedAlert | Active |
| Java | Tzeva-Adom-API | github.com/DavidTheExplorer/Tzeva-Adom-API | Active |
| Home Assistant | oref_alert | github.com/amitfin/oref_alert | Active |
| Home Assistant | RedAlert | github.com/idodov/RedAlert | Active |
| MCP Server | pikud-a-oref-mcp | github.com/LeonMelamud/pikud-a-oref-mcp | Active |
| Map Viz | oref-map | github.com/maorcc/oref-map | Active |

## 5. Legal Considerations

- OREF alert data is **public government emergency information** intended for broad dissemination.
- No official API documentation or published terms of use for programmatic access.
- Multiple open-source projects (MIT, Apache-2.0) access this data freely.
- **Recommendation:** Use responsibly. Don't overload servers during active emergencies. Attribute the source. Don't republish in ways that could cause confusion about active alerts.
