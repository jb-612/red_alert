# Red Alert Analytics Dashboard

Analytics dashboard for Israel's Home Front Command (OREF) alert history data.

## Project Structure

```
red_alert/
├── docs/
│   ├── design/          # Architecture and design documents
│   │   └── architecture.md
│   └── research/        # API research and repo reviews
│       ├── oref-api-endpoints.md
│       ├── alternative-data-sources.md
│       └── repo-security-review.md
├── CLAUDE.md            # AI assistant instructions
├── README.md
└── .gitignore
```

## Data Sources

| Source | Geo-Blocked | Use Case |
|--------|------------|----------|
| OREF GetAlarmsHistory.aspx | Yes (Israeli IP) | Historical date-range queries |
| Tzofar REST API | No | Ongoing ingestion |
| Tzofar WebSocket | No | Real-time alerts |
| dleshem/israel-alerts-data | No (GitHub CSV) | Historical backfill |

## Status

Project is in the design and research phase. See `docs/` for details.
