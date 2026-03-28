# OREF API Endpoints — Complete Reference

Research date: 2026-03-28

## 1. Real-Time Alerts

**URL:** `https://www.oref.org.il/WarningMessages/alert/alerts.json`
**Method:** GET
**Geo-blocked:** Yes (Israeli IP only)
**Polling interval:** Every 2-3 seconds for real-time use
**Notes:** Each alert stays active for ~5 seconds

### Response Format
```json
{
  "id": "133213399870000000",
  "cat": "1",
  "title": "ירי רקטות וטילים",
  "data": ["סעד", "אשדוד - יא,יב,טו,יז,מרינה"],
  "desc": "היכנסו למרחב המוגן ושהו בו 10 דקות"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique alert identifier (timestamp-based) |
| `cat` | string | Category number |
| `title` | string | Alert type description (Hebrew) |
| `data` | string[] | Affected cities/zones (Hebrew) |
| `desc` | string | Safety instructions (includes shelter duration) |

## 2. Recent History (Last ~24 Hours)

**URL:** `https://www.oref.org.il/WarningMessages/History/AlertsHistory.json`
**Method:** GET
**Geo-blocked:** Yes
**Delay:** Updates ~10+ seconds after an alert occurs

## 3. Historical Alerts with Date Range (PRIMARY FOR ANALYTICS)

**URL:** `https://www.oref.org.il/Shared/Ajax/GetAlarmsHistory.aspx`
**Method:** GET
**Geo-blocked:** Yes

### Query Parameters
| Parameter | Example | Description |
|-----------|---------|-------------|
| `lang` | `he` or `en` | Language code |
| `fromDate` | `01.10.2023` | Start date (DD.MM.YYYY) |
| `toDate` | `31.10.2023` | End date (DD.MM.YYYY) |
| `mode` | `0` | 0 = all alerts, 1 = city-specific |
| `city_0` | URL-encoded city name | When mode=1 |

### Example Request
```
GET https://www.oref.org.il/Shared/Ajax/GetAlarmsHistory.aspx?lang=he&fromDate=01.10.2023&toDate=31.10.2023&mode=0
```

### Response Format
```json
[
  {
    "data": "תל אביב - מרכז העיר",
    "date": "07.10.2023",
    "time": "06:30",
    "datetime": "2023-10-07T06:30:00",
    "category": 1,
    "category_desc": "ירי רקטות וטילים",
    "matrix_id": 4,
    "rid": "1234567",
    "outLat": "32.0853",
    "outLong": "34.7818",
    "inLat": "32.0853",
    "inLong": "34.7818"
  }
]
```

## 4. Alert Categories

**URL:** `https://www.oref.org.il/alerts/alertCategories.json`

| cat | Hebrew | English |
|-----|--------|---------|
| 1 | ירי רקטות וטילים | Rocket and missile fire |
| 2 | חדירת כלי טיס עוין | Hostile aircraft intrusion |
| 3 | רעידת אדמה | Earthquake |
| 4 | צונאמי | Tsunami |
| 5 | חדירת מחבלים | Terrorist infiltration |
| 6 | אירוע חומרים מסוכנים | Hazardous materials event |
| 7 | אירוע רדיולוגי | Radiological event |
| 13 | ניתן לצאת מהמרחב המוגן | Safe to leave protected space (all-clear) |
| 14 | הנחיה מקדימה | Preliminary guidance / early warning |

## 5. Required HTTP Headers

```
Host: www.oref.org.il
Referer: https://www.oref.org.il/
X-Requested-With: XMLHttpRequest
Content-Type: application/json
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
Accept: */*
Connection: keep-alive
Accept-Encoding: gzip, deflate, br
Accept-Language: en-US,en;q=0.9
```

## 6. Encoding Caveat

OREF API responses are UTF-8 with BOM (byte sequence `EF BB BF`). This breaks standard JSON parsers.

**Python fix:**
```python
import codecs
clean = codecs.decode(response.text.encode(), 'utf-8-sig')
data = json.loads(clean)
```

**Node.js fix:**
```javascript
const text = response.data.replace(/^\uFEFF/, '');
const data = JSON.parse(text);
```

## 7. Geo-Blocking Workarounds

The OREF API blocks all non-Israeli IPs. Solutions:
1. **GCP me-west1 (Tel Aviv)** — e2-micro VM (free tier eligible)
2. **Run locally in Israel**
3. **Israeli VPN exit node**
4. **Use Tzofar API instead** (see alternative-data-sources.md)
