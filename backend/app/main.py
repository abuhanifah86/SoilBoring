from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@app.get("/")
def root():
    return {"status": "ok", "service": "ddr-ops"}
