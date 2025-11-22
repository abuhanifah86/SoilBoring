from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from .routers import reports, ai, summaries, dashboard, auth, users


app = FastAPI(title="DDR Ops API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(reports.router)
app.include_router(ai.router)
app.include_router(summaries.router)
app.include_router(dashboard.router)
app.include_router(auth.router)
app.include_router(users.router)


@app.middleware("http")
async def _dedupe_api_prefix(request: Request, call_next):
    # Some clients may still call /api/api/...; redirect them to the correct path.
    if request.url.path.startswith("/api/api/"):
        new_path = request.url.path.replace("/api/api", "/api", 1)
        if request.url.query:
            new_path = f"{new_path}?{request.url.query}"
        return RedirectResponse(new_path, status_code=307)
    return await call_next(request)


@app.get("/")
def root():
    return {"status": "ok", "service": "ddr-ops"}
