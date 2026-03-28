# GitHub Repository Security & Functionality Review

Research date: 2026-03-28

## 1. dmatik/oref-alerts-proxy-ms

**Description:** Java Spring Boot microservice to proxy OREF alert APIs
**Language:** Java | **Stars:** 16 | **Forks:** 2 | **License:** GPL-3.0
**Last commit:** 2025-06-22 | **Created:** 2021-07-14

### What It Does
- Exposes two REST endpoints: `GET /current` and `GET /history`
- Proxies requests to OREF's `alerts.json` and `AlertsHistory.json` with browser-spoofing headers
- Handles OREF's malformed responses (BOM, control characters) via HTTP interceptors
- Docker-ready with environment variables for test mode and mock data

### Security Issues

| Severity | Issue | File | Detail |
|----------|-------|------|--------|
| CRITICAL | SSL verification disabled globally | `SSLUtil.java` | Uses `UNQUESTIONING_TRUST_MANAGER` that accepts ANY certificate. Vulnerable to MITM attacks. All HTTPS connections in the JVM are affected. |
| HIGH | Severely outdated base image | `Dockerfile` | `openjdk:11.0.1-jdk-slim-sid` (2018) — hundreds of known CVEs |
| HIGH | EOL framework version | `pom.xml` | Spring Boot 2.5.2 (July 2021) — end of life, unpatched vulnerabilities |
| HIGH | Unresolved dependency vulnerabilities | Issues #2, #3 | Automated scanner flagged vulnerable deps — still open |
| MEDIUM | Outdated JSON library | `pom.xml` | `org.json:json:20211205` — known DoS vulnerability |
| MEDIUM | No authentication | `OrefAlertsController.java` | Endpoints are open — anyone on the network can query |
| LOW | Broad regex in response cleaning | `CurrentAlertHttpRequestInterceptor.java` | Strips control chars aggressively — could mask data issues |

### Functionality Assessment
- **Works** but is a thin proxy — only forwards OREF's recent-24h endpoints
- No date-range history querying capability
- Has basic test mode with mock JSON files
- Low maintenance (last code change Dec 2024, last README update Jun 2025)

### Verdict
**Do NOT use as-is.** The SSL bypass is disqualifying for any production use. The outdated dependencies compound the risk. The functionality is too thin to justify adopting — easily replicated in ~30 lines of code with proper SSL handling.

---

## 2. eladnava/pikud-haoref-api

**Description:** Node.js wrapper library for Pikud Haoref's unofficial alert API
**Language:** JavaScript | **Stars:** 118 | **Forks:** 23 | **License:** Apache-2.0
**Last commit:** 2026-03-21 | **Created:** 2016-02-13

### What It Does
- Wraps OREF's real-time `alerts.json` endpoint with proper encoding handling
- Maps alert category numbers to human-readable types (missiles, earthquakes, infiltration, etc.)
- Provides rich city metadata with multilingual support (Hebrew, English, Russian, Arabic)
- Includes geolocation data, shelter countdown timers, and polygon mapping
- Falls back to `AlertsHistory.json` for alerts within 120 seconds if primary endpoint misses them

### Security Assessment

| Severity | Issue | Detail |
|----------|-------|--------|
| LOW | Legacy async patterns | Uses `co` + `co-request` (wraps deprecated `request` library) — not a vulnerability but technical debt |
| LOW | No input sanitization on geocoding | City names passed directly to Google Maps API — only used in metadata utility, not in alert-fetching path |
| NONE | No hardcoded secrets | Clean codebase |
| NONE | No eval() or prototype pollution vectors | Safe patterns throughout |
| NONE | Dependencies kept current | axios 1.9.0, Dependabot PRs merged regularly |

### Functionality Assessment
- **Solid and actively maintained** (commits in March 2026, responsive to issues)
- Correctly handles OREF's quirky encoding (UTF-16-LE, BOM bytes, null characters)
- Comprehensive alert type mapping (categories 1-13, 101-113, historical 1-26)
- Rich `cities.json` with 1,500+ locations, coordinates, multilingual names
- **No test suite** (`"test": "echo \"Error: no test specified\""`) — open issue #38
- Active community (47 issues total, most resolved)

### Verdict
**Reasonably safe to use** as a reference and for its `cities.json` geo-data. The codebase is clean and actively maintained. However, it only wraps real-time alerts — it does NOT provide the historical date-range queries needed for an analytics dashboard. Best used for: city metadata enrichment and as a reference for OREF API quirks.
