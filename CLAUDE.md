# Red Alert Analytics Dashboard

## Project Overview
Analytics dashboard built on top of Israel's Home Front Command (OREF) alert history data from https://www.oref.org.il/heb/alerts-history.

## Architecture Decisions
- Data ingestion: Tzofar API (no geo-blocking) + dleshem/israel-alerts-data CSV for historical backfill
- OREF direct API requires Israeli IP — use Tzofar as primary, OREF as secondary when running from Israel
- All OREF API responses have UTF-8 BOM — must strip before JSON parsing

## Key API Endpoints
- Real-time: `https://www.oref.org.il/WarningMessages/alert/alerts.json` (geo-blocked to Israel)
- History (24h): `https://www.oref.org.il/WarningMessages/History/AlertsHistory.json` (geo-blocked)
- History (date range): `https://www.oref.org.il/Shared/Ajax/GetAlarmsHistory.aspx?lang=he&fromDate=DD.MM.YYYY&toDate=DD.MM.YYYY&mode=0` (geo-blocked)
- Tzofar history: `https://api.tzevaadom.co.il/alerts-history` (no geo-blocking)
- Tzofar real-time WebSocket: `wss://ws.tzevaadom.co.il/socket?platform=ANDROID`

## Required OREF Headers
```
Referer: https://www.oref.org.il/
X-Requested-With: XMLHttpRequest
User-Agent: <browser UA string>
```

## Development Guidelines
- Write tests before implementing new features or bug fixes
- Never push to Git without asking for permission
- Check cyclomatic complexity when modifying functions — report if > 5
