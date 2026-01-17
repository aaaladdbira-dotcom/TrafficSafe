
# Copilot Instructions for Traffic Accident App

## Project Overview
- **Purpose:** Web app for reporting, managing, and analyzing traffic accidents in Tunisia.
- **Stack:** Flask (API/backend), SQLAlchemy (ORM), Jinja2 (templates), Chart.js & Leaflet (frontend), in-process cache (Redis optional).
- **Key Directories:**
  - `models/`: SQLAlchemy models (Accident, AccidentReport, User, ImportBatch)
  - `resources/`: Flask REST API endpoints (stats, accidents, reports, users, etc.)
  - `schemas/`: Marshmallow schemas for serialization/validation
  - `ui/`: UI logic for rendering and handling user flows (see `ui/accidents_ui.py`)
  - `templates/`: Jinja2 HTML templates (dashboard, forms, detail views)
  - `static/`: JS, CSS, images, geo data (see `static/js/toast.js`, `static/geo/`)
  - `utils/`: Shared utilities

## Architecture & Data Flow
- **API endpoints** in `resources/` serve data to frontend and UI layer. Each entity (e.g., Accident) is mirrored in `models/`, `resources/`, and `schemas/`.
- **UI logic** in `ui/` proxies API calls, manages session, and renders templates. Never call the DB directly from UI.
- **Templates** in `templates/` are rendered by Flask, using context from UI and API.
- **Frontend** uses Chart.js (charts) and Leaflet (maps) for visualization; see `templates/dashboard.html` for integration.
- **Caching:** In-process TTL cache for stats endpoints (see `resources/stats.py`); Redis can be enabled for scaling.

## Developer Workflows
- **Run app:** `python app.py` (dependencies in `requirements.txt`)
- **Migrations:** Alembic in `migrations/` (edit models, then run Alembic commands)
- **Static assets:** Place in `static/`; geo data in `static/geo/` (see `scripts/fetch_geojson.py`)
- **Templates:** Add/modify in `templates/`; UI logic in `ui/`
- **Testing:** No explicit test suite; add tests in `tests/` if needed

## Project-Specific Patterns & Conventions
- **API endpoints:** Use filter/query params for all stats endpoints (see `DASHBOARD_IMPLEMENTATION_PLAN.md` for contract)
- **Pagination:** All list endpoints (e.g., `/api/accidents`) support server-side pagination via `page` and `per_page` query params
- **KPIs/Stats:** `/api/stats/*` endpoints return JSON for dashboard; required keys and filters are defined in the dashboard plan
- **Geo data:** Use authoritative GeoJSON in `static/geo/`; normalize property names server-side or in JS
- **Frontend caching:** KPI cards cache API results for 30s on client
- **Toast notifications:** Use `Toast.success/info/error/warning` from `static/js/toast.js` for user feedback
- **Role-based access:** Government and non-government users have different permissions (see `resources/accident_report.py`)
- **Proxy pattern:** UI routes in `ui/` proxy API calls, attach session JWT, and handle pagination/filtering for templates
- **Naming conventions:**
  - Python: snake_case for files, functions, variables
  - Static assets: kebab-case
  - Templates: snake_case or descriptive names

## Integration & Cross-Component Communication
- **Models/resources/schemas** are tightly coupled by entity (e.g., `accident.py` in each)
- **UI logic** is separated from API/resource logic; never call DB directly from UI
- **Jinja2 is used for all HTML rendering**; avoid mixing JS templating with server templates
- **AJAX/data proxy:** Use `/ui/accidents/data` to proxy API data to frontend without exposing JWT

## References & Examples
- See `DASHBOARD_IMPLEMENTATION_PLAN.md` for dashboard API/data contract and required filters/outputs
- Example endpoints:
  - `/api/stats/kpis` (KPI cards)
  - `/api/stats/accidents/by_month` (time series)
  - `/api/stats/accidents/by_cause` (breakdown)
- Key files:
  - `app.py` (Flask app setup)
  - `models/accident.py` (core model)
  - `resources/stats.py` (stats endpoints, caching)
  - `ui/accidents_ui.py` (UI logic, API proxy, pagination)
  - `templates/dashboard.html` (dashboard UI)
  - `static/js/toast.js` (toast notifications)

---
For new features, follow the established patterns in `models/`, `resources/`, and `ui/`. Reference the dashboard plan and existing endpoints for structure, naming, and data contracts. When in doubt, check the relevant files above.