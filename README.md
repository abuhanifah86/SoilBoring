## Soil Boring Ops – Geotechnical Field Log

Comprehensive borehole logging with AI-assisted narratives and dashboards. The steps below guide everyone from first-time users to experienced engineers.

- **Backend:** Python + FastAPI (Uvicorn)
- **Frontend:** React + Vite (TypeScript)
- **Data:** `data/reports.csv` ships with 123 synthetic 2024 borehole logs following a typical geotechnical schema.

---

### Quick Start (fast path)

If you want the app running quickly with defaults:

```bash
# from the repo root
./dev.sh          # macOS/Linux
# or
pwsh ./dev.ps1    # Windows PowerShell
```

Open the frontend URL shown in the terminal (default `http://localhost:5173`). Sign in with a user from `data/users.json`.

---

### Prerequisites

- Python 3.10+
- Node.js 18+
- (Optional) Local Ollama server for AI narratives  
  - `OLLAMA_URL` default: `http://localhost:11434/api/chat`  
  - `OLLAMA_MODEL` default: `gpt-oss:120b-cloud`

---

### Install & Run (step-by-step)

#### 1) Backend

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Environment variables:
- `DATA_DIR` — where CSV/user files live (default `data/`).
- `AUTH_TOKEN_SECRET` — signing secret for auth tokens (set in non-dev).
- `AUTH_TOKEN_TTL` — token lifetime in seconds (default 28800 = 8h).
- `OLLAMA_URL`, `OLLAMA_MODEL` — AI service endpoint/model.

#### 2) Frontend

```bash
cd frontend
npm install
echo "VITE_API_URL=http://localhost:8000" > .env   # adjust if backend host changes
npm run dev    # default http://localhost:5173
```

Both services bind to `0.0.0.0` by default so they are reachable on your LAN. Override with `BACKEND_HOST/BACKEND_PORT` or `FRONTEND_HOST/FRONTEND_PORT` if needed.

---

### Authentication

- App access requires sign-in.
- Users live in `data/users.json`.
- Entry format: `{ "email": "...", "password": "sha256$<salt>$<digest>", "role": "admin|general" }`.
- Admins can add/remove users in the **Users** tab (visible only to admins).
- Tokens are signed with `AUTH_TOKEN_SECRET` and expire per `AUTH_TOKEN_TTL`.

---

### Data Schema

`data/reports.csv` headers:

```
BoreholeID, ProjectName, SiteName, Latitude, Longitude, GroundElevation_mRL,
StartDate, EndDate, DrillingMethod, BoreholeDiameter_mm, TargetDepth_m, FinalDepth_m,
CasingInstalled_mm, GroundwaterDepth_m, GroundwaterEncountered, SoilDescription,
USCS_Class, Avg_SPT_N60, Contractor, LoggingGeologist, Remarks, SubmittedBy
```

Every log submitted via the UI maps to these columns. `SubmittedBy` is injected automatically based on the signed-in user.

---

### Features at a Glance

- **Borehole Log:** Form-driven capture of project/site, drilling parameters, groundwater, USCS, and SPT stats.
- **Borehole Data:** Filter/search/sort logs, export CSV, and edit/delete rows with confirmations.
- **Dashboard:** KPIs, method and USCS breakdowns, and recent activity with an executive AI brief.
- **Summaries:** Weekly (date range) and monthly (month/year) rollups with stats, highlights, and markdown AI narratives.
- **Geo AI:** Q&A backed by the borehole CSV with evidence display.
- **About:** Primer derived from `template/soilboring.md`.

---

### Project Structure

```
backend/
  app/
    auth.py
    analytics.py
    ollama_client.py
    routers/
      auth.py
      ai.py
      reports.py
      summaries.py
      dashboard.py
frontend/
  src/
    App.tsx
    Login.tsx
    api.ts
    tabs/
      DailyReportForm.tsx
      DailyReportData.tsx
      QA.tsx
      Summary.tsx
      Dashboard.tsx
      AboutSoilBoring.tsx
data/
  reports.csv        # synthetic 2024 borehole logs
  users.json         # sample users
```

---

### Tips for New Users

- Ensure backend (`http://localhost:8000`) and frontend (`http://localhost:5173`) are both running.
- If you see auth errors, verify your account exists in `data/users.json` and `AUTH_TOKEN_SECRET` is consistent.
- To reset logs, delete `data/reports.csv`; it will be recreated on the next save using the schema above.

### Tips for Power Users

- Point `VITE_API_URL` to a remote backend to use the UI against a shared server.
- Set `DATA_DIR` to an external volume to keep field logs on shared storage.
- Harden production: set a strong `AUTH_TOKEN_SECRET`, adjust `AUTH_TOKEN_TTL`, and review CORS before exposing beyond localhost.
- Override `OLLAMA_MODEL`/`OLLAMA_URL` to plug in your own model or hosted AI endpoint.

---

### Docker (single VM)

Build and run the full stack behind one port (frontend at `/`, backend at `/api`):

```bash
# from repo root
docker compose build
docker compose up -d
```

Config you may want to set:
- `AUTH_TOKEN_SECRET` (required in prod)
- `AUTH_TOKEN_TTL` (seconds, default 28800)
- `OLLAMA_URL` (if using AI summaries/QA)
- `VITE_API_URL` build-arg (defaults to `/api`)

Data persistence: `./data` on the host is bind-mounted into the backend container at `/app/data` so reports/users survive restarts.

### Deployment notes (latest changes)
- Frontend now defaults to calling `/api` when `VITE_API_URL` is unset; rebuild frontend if you change this.
- Backend redirects any `/api/api/*` requests to `/api/*` to tolerate stale caches.
- AI/Ollama is optional. If you run Ollama on the host, set `OLLAMA_URL=http://host.docker.internal:11434/api/chat` (or your host IP) in `docker-compose.yml` and restart the backend. If Ollama is not reachable, AI endpoints return a friendly “AI service unavailable” message instead of failing.
- If you prefer containerized Ollama, add an `ollama` service to `docker-compose.yml` and point `OLLAMA_URL` to `http://ollama:11434/api/chat`; mount a volume for models so downloads persist.
