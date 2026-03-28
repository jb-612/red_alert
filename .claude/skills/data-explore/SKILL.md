---
name: data-explore
description: Explore and validate OREF/Tzofar data sources. Fetch samples, check schemas, verify BOM handling.
argument-hint: "[source: tzofar|oref|csv]"
allowed-tools: Read, Glob, Grep, Bash, WebFetch
---

Explore data source $ARGUMENTS:

## Available Sources

### Tzofar API (no geo-blocking)
```bash
curl -s https://api.tzevaadom.co.il/alerts-history | python3 -m json.tool | head -50
```
- Check response schema (date, area, title, category, latitude, longitude)
- Verify multilingual fields (name_en, name_ru, name_ar)
- Count total records returned

### OREF API (geo-blocked to Israel)
```bash
curl -s -H "Referer: https://www.oref.org.il/" \
  -H "X-Requested-With: XMLHttpRequest" \
  "https://www.oref.org.il/WarningMessages/History/AlertsHistory.json" | python3 -c "
import sys, codecs, json
raw = sys.stdin.buffer.read()
text = codecs.decode(raw, 'utf-8-sig')
data = json.loads(text)
print(json.dumps(data[:3], indent=2, ensure_ascii=False))
print(f'Total records: {len(data)}')
"
```
- Verify BOM handling works
- Check response fields (data, date, time, datetime, category, category_desc, rid, outLat, outLong)

### CSV Dataset (dleshem/israel-alerts-data)
```bash
head -5 data/alerts.csv
wc -l data/alerts.csv
```
- Check column headers
- Count total records
- Verify date range coverage

## Validation Checks

1. **Schema match** — Do response fields match our DB schema?
2. **BOM handling** — Does stripping produce valid JSON?
3. **Deduplication candidates** — Any duplicate (datetime, location, category) tuples?
4. **Hebrew text** — Are Hebrew strings intact (not mojibake)?
5. **Coordinate validity** — Are lat/lng within Israel bounds (29-34 N, 34-36 E)?
