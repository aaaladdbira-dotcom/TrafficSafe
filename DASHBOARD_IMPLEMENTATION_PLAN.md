# Dashboard Implementation Plan

This document outlines a staged plan to complete the Power-BI-like statistics dashboard for the Traffic Accident app. It is scoped to the features and tech already in the repository: Flask backend, SQLAlchemy models, Jinja templates, Chart.js, Leaflet, and a small in-process cache.

## 1) Contract (inputs / outputs / success criteria)
- Inputs:
  - Filters: start (ISO date), end (ISO date), year (YYYY), month (MM), governorate, delegation, severity, cause, source
- Outputs:
  - KPIs endpoint: total, yearToDate, monthToDate, topCause (cause, count, pct), topGovernorate, topDelegation, avgPerDay, highSeverityRate, yoyChangePct
  - Timeseries endpoints: accidents by day/month/year, by_hour_by_weekday (heatmap), confirmed_vs_reported
  - Breakdown endpoints: by_severity, by_cause, by_governorate, by_delegation
- Success criteria:
  - KPI values match authoritative `Accident` rows and respect filters.
  - Charts render quickly for typical dataset sizes (up to ~100k rows) with caching.
  - Map supports click-to-filter (Leaflet) and a Google iframe fallback for visual preference.

## 2) High-level stages
1. Stabilize API & caching (small in-process cache -> Redis optional)
2. Map: authoritative GeoJSON acquisition and normalization
3. Frontend: charts, map integration, filters, paging, and accessibility
4. Advanced visuals (heatmap, treemap)
5. Performance, tests, and deployment notes

## 3) Backend: endpoints & data contracts
- /api/stats/kpis
  - Query string accepts filters; returns JSON with keys described above
- /api/stats/accidents/by_month (granularity param: day|month|year)
- /api/stats/accidents/by_cause
- /api/stats/accidents/by_severity
- /api/stats/accidents/by_governorate
- /api/stats/accidents/by_delegation
- /api/stats/reports/confirmed_vs_reported

Notes:
- Implement server-side pagination for any list endpoints used by the UI.
- Add `label` fields to breakdown responses (optional) if clients want pretty labels.

## 4) Frontend components
- Filter panel (sticky): date range, year, month, governorate, delegation, severity, cause, source, apply/reset
- KPI cards (already present): wire to `/api/stats/kpis` with caching on client side for 30s
- Time series hero: Chart.js line with granularity switch
- Charts pages: severity, cause (bar), delegation (bar), confirmed vs reported (stacked)
- Map card: Leaflet overlay with choropleth and delegation drilldown; a toggle to show Google iframe (no-key) or full Google JS API (key required)
- Accessibility: ensure all form controls have labels, tab order, and ARIA roles where appropriate

## 5) Map / GeoJSON handling
- Required files: `static/geo/tunisia_governorates.geojson`, `static/geo/tunisia_delegations.geojson`
- Implement `scripts/fetch_geojson.py` (exists) to download from authoritative sources. Validate by checking bounding box and `NAME`/`name` properties.
- Normalize feature properties server-side or in JS: accept `name`, `NAME`, `gov_name` mapping
- If polygon geojson is missing, fallback to approximate polygon or sample points (already implemented)

## 6) Performance & caching
- Short-term: in-process TTL cache (already present) for heavy aggregation endpoints (kpis, timeseries)
- Medium-term: add Redis cache for cross-worker persistence and larger ttl for less-frequently changing aggregates
- DB: add indexes on `Accident.occurred_at`, `Accident.governorate`, `Accident.delegation`, `Accident.cause`, `Accident.severity`
- Query scaling: consider pre-aggregated daily counters (materialized table) for large datasets

## 7) Testing & QA
- Unit tests for endpoints (happy path + filters + edge cases)
- Integration test for the main statistics page: ensure filter panel triggers requests and charts update
- Manual checks for map interactions and fallback notice

## 8) Deliverables & timeline (suggested quick plan)
- Day 1 (small): finalize API contracts, add `label` fields to breakdown results, stabilize in-process caching
- Day 2: complete authoritative GeoJSON fetch+normalize and wire Leaflet choropleth; ensure click-to-filter works
- Day 3: add advanced visuals (heatmap), finish accessibility pass, add basic tests
- Day 4: performance pass (Redis or materialized tables) and final QA

## 9) Next steps for me now
1. Implement objective #1: expand API responses to include `label` for breakdown endpoints (so frontends need no extra prettifying) and add small unit tests.
2. Acquire authoritative governorates/delegations GeoJSON (run fetch script and validate) or accept uploaded files.

---
If you want I can begin working on step 1 immediately (add `label` fields in API responses and update JS to prefer `label` when present). Reply with "start step 1" and I'll implement and run quick checks.