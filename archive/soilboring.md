# Soil Boring Application — Technical & Functional Specification (FastAPI + React)

**Prepared for:** Abu Hanifah, Manager Business Process & Technology  
**Domain:** Upstream O\&G — geotechnical operations  
**Version:** v2.0 (FastAPI + React)  
**Date format (UI & reports):** `dd-mm-yyyy`  
**Units:** Metric  
**Primary outputs:** CSV (raw daily), Web reports, Dashboard exports (PNG/PDF), Excel for detail

***

## 1) Executive Summary

Build a **web application** with:

*   **React frontend** (responsive, PWA-ready) for field/office users
*   **FastAPI backend** (served with **uvicorn**) for APIs, validation, CSV export, reporting aggregation
*   **PostgreSQL** primary datastore
*   **CSV export service** for raw daily data
*   **Report endpoints** (weekly/monthly summaries)
*   **KPI dashboard** (server-side aggregates + client visuals)
*   **Role-based access control** (RBAC), audit log, schema versioning

***

## 2) Architecture Overview

### 2.1 High-Level Diagram (conceptual)

    [React SPA] <--> [FastAPI (uvicorn)]
                         |
                    [PostgreSQL]
                         |
                   [File Storage] --> CSV Exports (daily, UTF-8)

**Notes**

*   React SPA communicates via REST (JSON).
*   FastAPI provides OpenAPI docs (`/docs`, `/openapi.json`).
*   CSV written to a designated storage path (local or object storage like S3/Azure Blob—configurable).
*   Support for **offline capture (Phase-2)** via service worker & local queue.

### 2.2 Technology Stack

*   **Frontend**: React 18, TypeScript, Vite/CRA, React Router, Zustand/Redux Toolkit (state), React Query (server state), MUI/AntD (UI), Recharts/Nivo/ECharts (charts), Leaflet/Mapbox GL (map), Day.js (dates), `date-fns-tz` for TZ handling
*   **Backend**: FastAPI, uvicorn, SQLAlchemy 2.x, Alembic (migrations), Pydantic v2, Pandas (optional for CSV & Excel), Jinja2/WeasyPrint (PDF—optional), Gunicorn+Uvicorn workers for prod
*   **Database**: PostgreSQL 14+ (UTF-8, time zone aware)
*   **Auth**: OAuth2 (JWT access/refresh), Azure AD OIDC (Phase-2 SSO option)
*   **Testing**: Pytest, Playwright/Cypress (E2E)
*   **CI/CD**: GitHub Actions/Azure DevOps; Docker images; IaC (Terraform—optional)
*   **Observability**: Logging (structlog), Prometheus metrics (optional), Sentry (optional)

***

## 3) User Roles & Permissions (RBAC)

| Role             | Permissions                                                                        |
| ---------------- | ---------------------------------------------------------------------------------- |
| Field Crew       | Create/Edit daily entries (own/assigned), upload attachments, view own records.    |
| Supervisor       | Review/approve, edit before approval, run reports, view dashboards.                |
| Geotech Engineer | Read all approved, analytics, export.                                              |
| Admin            | Manage users/master data, full access, schema/version control, bulk import/export. |

**Backend enforcement:** Role claims in JWT → dependency injection in FastAPI routes (e.g., `Depends(require_roles(...))`).

***

## 4) Data Model (PostgreSQL)

### 4.1 Core Tables

**`daily_activity`**

*   `id` (UUID, PK)
*   `schema_version` (text, default `'1.0'`)
*   `activity_date` (date)  **(UI shows as `dd-mm-yyyy`)**
*   `project_area` (text)
*   `borehole_id` (text)
*   `latitude` (numeric(9,6))
*   `longitude` (numeric(9,6))
*   `rig_id` (text)
*   `crew_lead` (text)
*   `method` (text)  **(enum list managed by dictionary)**
*   `planned_depth_m` (numeric(6,2))
*   `actual_depth_m` (numeric(6,2))
*   `start_time` (time without tz)
*   `end_time` (time without tz)
*   `total_boring_hours` (numeric(5,2))  *(calculated or manual override)*
*   `progress_m_per_day` (numeric(6,2))
*   `samples_taken_count` (int)
*   `spt_conducted` (bool)
*   `spt_intervals` (text)  *(e.g., "1.5;3.0;4.5")*
*   `groundwater_level_m` (numeric(6,2), nullable)
*   `soil_layers_notes` (text)
*   `weather` (text) **(enum)**
*   `downtime_hours` (numeric(5,2))
*   `downtime_causes` (text)
*   `hse_incidents` (bool)
*   `incident_notes` (text)
*   `remarks` (text)
*   `attachments_indicator` (bool)
*   `approval_status` (text) **(enum: Draft, Submitted, Approved, Rejected)**
*   `created_by` (text)
*   `created_at` (timestamptz, default now)
*   `modified_by` (text, nullable)
*   `modified_at` (timestamptz, nullable)
*   `approved_by` (text, nullable)
*   `approved_at` (timestamptz, nullable)

**`attachment`** *(optional MVP)*

*   `id` (UUID, PK)
*   `daily_activity_id` (UUID, FK → daily\_activity.id)
*   `file_name` (text), `content_type` (text), `file_url` (text | object storage key)
*   `uploaded_by` (text), `uploaded_at` (timestamptz)

**`dictionary`** *(for enums/master data)*

*   `id` (UUID, PK)
*   `type` (text)  *(e.g., 'method','weather','rig','project\_area')*
*   `code` (text), `label` (text), `active` (bool), `sort_order` (int)

**`audit_log`**

*   `id` (UUID, PK)
*   `entity` (text), `entity_id` (UUID), `action` (text) *(CREATE/UPDATE/APPROVE/REJECT/EXPORT)*
*   `changed_by` (text), `changed_at` (timestamptz), `payload` (jsonb)

**Indexes**

*   `idx_daily_unique` on (`borehole_id`, `activity_date`) *(prevent duplicates)*
*   `idx_date`, `idx_project_area`, `idx_rig_id`, `idx_status`

### 4.2 Schema Versioning

*   Column `schema_version` monitors structure.
*   Backward-compatible reading; migration scripts via Alembic.

***

## 5) API Design (FastAPI)

**Base URL:** `/api/v1`  
**Auth:** OAuth2 password flow with JWT (access/refresh) or OIDC (Azure AD) in Phase-2.

### 5.1 Authentication

*   `POST /auth/login` → returns `{ access_token, refresh_token, expires_in }`
*   `POST /auth/refresh` → new tokens
*   Middleware to extract user & roles.

### 5.2 Daily Activities

*   `POST /daily-activities` *(Field Crew, Supervisor, Admin)*  
    Create a record. Validate requireds; compute `total_boring_hours` if omitted.
*   `GET /daily-activities` *(All roles w/ RLS)*  
    Query parameters: `from`, `to` (`dd-mm-yyyy`), `project_area`, `rig_id`, `borehole_id`, `status`, `page`, `page_size`, `sort`.
*   `GET /daily-activities/{id}`
*   `PUT /daily-activities/{id}` *(edit if Draft/Submitted; Approved read-only unless Admin override)*
*   `POST /daily-activities/{id}/submit`
*   `POST /daily-activities/{id}/approve`
*   `POST /daily-activities/{id}/reject`

### 5.3 Attachments

*   `POST /daily-activities/{id}/attachments` (multipart)
*   `GET /daily-activities/{id}/attachments`
*   `DELETE /attachments/{attachment_id}` *(role-based)*

### 5.4 CSV Export & Raw Data

*   `GET /exports/daily-csv?date=dd-mm-yyyy&project_area=...`  
    Generates or fetches `soil_boring_daily_YYYYMMDD.csv` with UTF-8 header & rows.
*   `GET /raw-data`  
    Streams all raw daily activity data (paged); CSV/Excel export via `format` query.

### 5.5 Weekly/Monthly Reports

*   `GET /reports/weekly?from=dd-mm-yyyy&to=dd-mm-yyyy`  
    Returns computed KPIs, series, tables.
*   `GET /reports/monthly?month=1-12&year=YYYY`  
    Same structure as weekly + plan-vs-actual (if plan provided via upload endpoint).
*   `POST /reports/plan/upload` *(optional)*  
    Accept plan CSV/XLSX; stored & referenced in monthly aggregation.

### 5.6 KPI Dashboard

*   `GET /dashboard/kpis?from=dd-mm-yyyy&to=dd-mm-yyyy&project_area=...&rig_id=...`  
    Returns KPI cards + datasets for graphs (meters/day, Pareto downtime, by rig/crew).
*   `GET /dashboard/map?from=...&to=...`  
    Returns geospatial points (lat/lon + borehole summary).

### 5.7 Dictionaries & Admin

*   `GET /dictionaries/{type}`  *(method, weather, rig, project\_area)*
*   `POST /dictionaries/{type}` *(Admin)*
*   `GET /admin/audit` *(Admin)*
*   `GET /healthz` *(readiness/liveness)*

### 5.8 Validation Rules (Server-Side)

*   Required: date, project\_area, borehole\_id, rig\_id, method, planned\_depth\_m, actual\_depth\_m or progress, approval\_status
*   `End Time ≥ Start Time`
*   `Lat ∈ [-90,90], Lon ∈ [-180,180]`
*   `Actual Depth ≤ Planned Depth + 5%` → warn (allow with flag `override_depth_check=true`)
*   Unique (`borehole_id`,`activity_date`)
*   Approval transitions only by roles

### 5.9 Response Shapes (Samples)

**Daily Activity (GET)**

```json
{
  "id": "uuid",
  "schema_version": "1.0",
  "activity_date": "14-11-2025",
  "project_area": "North Pad",
  "borehole_id": "BH-022",
  "latitude": -6.178,
  "longitude": 106.866,
  "rig_id": "RIG-03",
  "crew_lead": "Supriyadi",
  "method": "Auger",
  "planned_depth_m": 20.0,
  "actual_depth_m": 20.0,
  "start_time": "07:30",
  "end_time": "15:00",
  "total_boring_hours": 7.0,
  "progress_m_per_day": 20.0,
  "samples_taken_count": 4,
  "spt_conducted": true,
  "spt_intervals": "1.5;3.0;4.5",
  "groundwater_level_m": 2.2,
  "soil_layers_notes": "ML then SM",
  "weather": "Clear",
  "downtime_hours": 0.5,
  "downtime_causes": "Rain shower",
  "hse_incidents": false,
  "incident_notes": "",
  "remarks": "Completed",
  "attachments_indicator": true,
  "approval_status": "Approved",
  "created_by": "hanifah",
  "created_at": "14-11-2025 17:35",
  "modified_by": "supervisor",
  "modified_at": "14-11-2025 18:10",
  "approved_by": "supervisor",
  "approved_at": "14-11-2025 18:12"
}
```

***

## 6) CSV Export Specification

**Purpose:** Persist raw daily activities to CSV.

*   **File name**: `soil_boring_daily_YYYYMMDD.csv`
*   **Path**: `/Project/<ProjectArea>/Daily/` (configurable root)
*   **Encoding**: UTF-8; comma delimiter; double quotes for text; `.` decimals.
*   **Header** (fixed, versioned):

<!---->

    schema_version,record_id,date,project_area,borehole_id,latitude,longitude,rig_id,crew_lead,method,planned_depth_m,actual_depth_m,start_time,end_time,total_boring_hours,progress_m_per_day,samples_taken_count,spt_conducted,spt_intervals,groundwater_level_m,soil_layers_notes,weather,downtime_hours,downtime_causes,hse_incidents,incident_notes,remarks,attachments_indicator,created_by,created_at,modified_by,modified_at,approval_status,approved_by,approved_at

*   **Atomic write**: write `*.tmp` → fsync → rename to final.
*   **Idempotent**: exporting the same date overrides file if checksum differs; audit logged.
*   **Scope**: include all rows with `activity_date=YYYY-MM-DD` irrespective of approval; optional flag `approved_only=true`.

***

## 7) Frontend (React) — UX & Components

### 7.1 Pages

1.  **Sign In** (JWT login)
2.  **Daily Entry**
    *   Sections: Project/Borehole, Time & Progress, Sampling/SPT, Conditions, HSE/Downtime, Remarks/Attachments
    *   Actions: Save Draft, Submit, Export Today’s CSV (if role)
    *   Client validations mirror backend
3.  **Reports — Weekly/Monthly**
    *   Inputs: (weekly) `From/To`; (monthly) `Month/Year`
    *   Cards: Totals, Avg, SPT coverage, Downtime, HSE
    *   Charts: line (meters/day), bar (meters by borehole/rig), Pareto (downtime)
    *   Export: PDF/Excel buttons
4.  **KPI Dashboard**
    *   Global filters: Date range (`dd-mm-yyyy`), Project Area, Rig, Method, Status
    *   Cards + charts + map (borehole points)
    *   Drill-through to raw records
5.  **Raw Data Grid**
    *   Sort/filter/search; column chooser; export visible
    *   Row audit modal
6.  **Admin**
    *   Dictionaries (method/weather/rig/project); Users (optional); Audit log

### 7.2 Component Structure (suggested)

    /src
      /api (React Query hooks)
      /components
        /forms (DailyActivityForm, TimeRangePicker, SPTIntervalsInput)
        /charts (MetersLine, ParetoDowntime, BarByRig, KPIGrid)
        /tables (RawDataTable)
        /layout (Navbar, Sidebar, ProtectedRoute)
      /pages (Login, DailyEntry, ReportsWeekly, ReportsMonthly, Dashboard, RawData, Admin)
      /state (Zustand/Redux slices for filters, session)
      /utils (date, validation, formatters)
      /styles

### 7.3 Date & Time Handling

*   UI uses `dd-mm-yyyy`.
*   Convert to ISO for API (backend accepts `dd-mm-yyyy`; converts to date).
*   Time inputs: 24h `HH:mm`.
*   Maintain timezone consistency (server in UTC; display in user’s locale).

### 7.4 Accessibility & i18n

*   WCAG AA color contrast, keyboard nav.
*   i18n (English/Indonesian) Phase-2 via `react-i18next`.

***

## 8) Reporting & KPI Logic (Server-Side Aggregates)

**Weekly/Monthly KPIs**

*   Total Boreholes Worked: `COUNT(DISTINCT borehole_id)`
*   Boreholes Completed: `COUNT(DISTINCT borehole_id WHERE actual_depth_m >= planned_depth_m)` or `approval_status='Approved' AND marked complete`
*   Total Meters Bored: sum of `progress_m_per_day` or `actual_depth_m` on completion rows (agreed rule)
*   Average Meters/Day: `SUM(progress_m_per_day) / COUNT(DISTINCT activity_date)`
*   Average Boring Hours/Day: `AVG(total_boring_hours)`
*   Total Downtime Hours: `SUM(downtime_hours)`
*   SPT Coverage: `distinct boreholes with spt_conducted / distinct boreholes worked`
*   HSE Incident Rate: `incidents / total activity rows * 100`

**Monthly extras**

*   Plan vs Actual (if plan table available)
*   Best/Worst day (by meters, downtime)
*   Rig utilization: `productive_hours / total_available_hours` *(requires rig calendar, Phase-2 optional master)*

***

## 9) Non-Functional Requirements

*   **Performance**:
    *   API P95 < 300 ms for CRUD; < 2s for report endpoints
    *   Frontend load < 2s on fast network
*   **Availability**: 99% business hours; graceful degradation when DB/FS intermittent
*   **Security**:
    *   JWT with short-lived access, refresh token rotation
    *   TLS 1.2+ end-to-end
    *   RBAC enforced in routes and queries
    *   OWASP ASVS controls; input validation & output encoding
*   **Auditability**: all state transitions & exports are logged
*   **Scalability**: 250k+ rows; index strategy; pagination; cache hot aggregates (e.g., Redis—Phase-2)
*   **Maintainability**: typed models (Pydantic), linting, CI checks, OpenAPI docs

***

## 10) Error Handling & Responses

*   Consistent error schema:

```json
{ "error": { "code": "VALIDATION_ERROR", "message": "End Time cannot be earlier than Start Time.", "field": "end_time" } }
```

*   HTTP codes: 200/201, 400 (validation), 401/403 (auth), 404, 409 (duplicate), 500
*   Idempotent endpoints for exports; retries safe
*   CSV write errors: retry with backoff; alert Admin via log/notification

***

## 11) Security & Governance

*   **RBAC** at API layer
*   **Row-level** read constraints (e.g., Field Crew can only see own/assigned project area)
*   **Data masking** (if needed) for HSE notes outside Admin/Supervisor
*   **Attachment scanning** (Phase-2) for malware
*   **Retention**: raw & CSV retained 5+ years, archival storage policy
*   **Secrets management**: environment variables via Vault/Azure Key Vault

***

## 12) DevOps & Deployment

*   **Environments**: Dev, Staging, Prod
*   **Containerization**: Docker (backend & frontend)
*   **Runtime**:
    *   Backend: `gunicorn -k uvicorn.workers.UvicornWorker -w 2 app.main:app`
    *   Frontend: Nginx static hosting (or Vercel/Azure Static Web Apps)
*   **CI/CD**:
    *   Lint & tests (pytest, coverage), type checks (mypy)
    *   Build images, run Alembic migrations
    *   Deploy with blue/green or rolling updates
*   **Monitoring**: health endpoints, metrics, structured logs

***

## 13) Sample File & Directory Structure

**Backend**

    backend/
      app/
        main.py
        api/
          v1/
            routes_daily.py
            routes_reports.py
            routes_dashboard.py
            routes_auth.py
            routes_admin.py
        core/
          config.py
          security.py
          dependencies.py
        db/
          base.py
          session.py
          models.py
          schemas.py
          repositories.py
          migrations/ (alembic)
        services/
          csv_exporter.py
          reporting.py
          attachments.py
          audit.py
        utils/
          dates.py
      tests/
        unit/
        integration/
      pyproject.toml
      Dockerfile

**Frontend**

    frontend/
      src/
        api/ (React Query hooks)
        components/
        pages/
        state/
        utils/
        assets/
      vite.config.ts
      package.json
      Dockerfile

***

## 14) Acceptance Criteria & Test Scenarios

**AC-1 Daily Capture & Validation**

*   Given valid inputs, POST `/daily-activities` creates row; row appears in grid; timestamps correct.

**AC-2 Duplicate Prevention**

*   Creating same `borehole_id + activity_date` returns 409 with helpful message.

**AC-3 CSV Export**

*   For a date, `GET /exports/daily-csv` produces the file with correct header order, encoding, and values; atomic write ensured.

**AC-4 Weekly Report Accuracy**

*   For a known dataset, weekly totals match manual calculations; charts reflect filters; export to PDF/Excel succeeds.

**AC-5 KPI Dashboard Filters**

*   Selection of date range + rig updates all KPIs/charts within 2 seconds; map points correspond to filtered rows.

**AC-6 Role Enforcement**

*   Field Crew cannot approve; Supervisor can approve; Approved records are read-only except Admin override.

**AC-7 Audit Trail**

*   CREATE/UPDATE/APPROVE/EXPORT actions are visible in `/admin/audit` with actor, time, and payload delta.

***

## 15) Implementation Plan (6–7 Weeks)

**Sprint 1 (Week 1–2): Backend Foundations**

*   DB schema + Alembic migrations
*   Auth (JWT), RBAC guardrails
*   CRUD for daily activities + validation
*   Dictionaries API
*   Basic tests

**Sprint 2 (Week 2–3): Frontend MVP**

*   Login flow; protected routes
*   Daily Entry form with client-side validation
*   Raw Data grid (list, filter, sort, paginate)

**Sprint 3 (Week 3–4): Reporting & Exports**

*   CSV exporter service + endpoint
*   Weekly & Monthly report endpoints (aggregates)
*   Frontend report pages & chart components

**Sprint 4 (Week 4–5): KPI Dashboard & Map**

*   KPI & trend endpoints; downtime Pareto
*   Dashboard page, slicers, map visualization

**Sprint 5 (Week 5–6): Attachments, Audit, Hardening**

*   Attachment upload & listing
*   Audit logging UI
*   Performance tuning; security review

**Go-Live (Week 7)**

*   UAT, bug fixes, training, runbook

***

## 16) OpenAPI Excerpt (Illustrative)

```yaml
openapi: 3.0.3
info:
  title: Soil Boring API
  version: "1.0"
paths:
  /api/v1/daily-activities:
    get:
      parameters:
        - in: query
          name: from
          schema: { type: string, example: "10-11-2025" }
        - in: query
          name: to
          schema: { type: string, example: "14-11-2025" }
      responses: { "200": { description: OK } }
    post:
      requestBody:
        required: true
        content:
          application/json:
            schema: { $ref: "#/components/schemas/DailyActivityCreate" }
      responses: { "201": { description: Created } }
  /api/v1/reports/weekly:
    get:
      parameters:
        - in: query
          name: from
          schema: { type: string }
        - in: query
          name: to
          schema: { type: string }
      responses: { "200": { description: OK } }
components:
  schemas:
    DailyActivityCreate:
      type: object
      required: [activity_date, project_area, borehole_id, rig_id, method, planned_depth_m]
      properties:
        activity_date: { type: string, example: "14-11-2025" }
        project_area: { type: string }
        borehole_id: { type: string }
        latitude: { type: number }
        longitude: { type: number }
        rig_id: { type: string }
        method: { type: string }
        planned_depth_m: { type: number }
        actual_depth_m: { type: number }
        start_time: { type: string, example: "07:30" }
        end_time: { type: string, example: "16:30" }
```

***

## 17) Risks & Mitigations

*   **Field connectivity gaps** → PWA offline cache (Phase-2), local queue with retry
*   **Data quality drift** → strict server validation, approval workflow, dictionaries
*   **Performance with large datasets** → indexes, paginated queries, pre-aggregations for reports
*   **Time zone confusion** → store UTC; display local; strict input format (`dd-mm-yyyy`)
*   **Schema evolution** → version column + Alembic migrations; backward-compatible CSV

***

## 18) Sample Calculations (Backend)

*   **Total Meters Bored (progress-based)**
    *   SQL:
        ```sql
        SELECT COALESCE(SUM(progress_m_per_day),0) AS total_meters
        FROM daily_activity
        WHERE activity_date BETWEEN :from AND :to;
        ```
*   **SPT Coverage**
    ```sql
    SELECT 
      COALESCE(SUM(CASE WHEN spt_conducted THEN 1 ELSE 0 END),0)::decimal
      / NULLIF(COUNT(DISTINCT borehole_id),0) AS spt_coverage
    FROM daily_activity
    WHERE activity_date BETWEEN :from AND :to;
    ```
*   **Downtime Pareto**
    ```sql
    SELECT downtime_causes, SUM(downtime_hours) AS hours
    FROM daily_activity
    WHERE activity_date BETWEEN :from AND :to
    GROUP BY downtime_causes
    ORDER BY hours DESC;
    ```

***
