from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routers import analyser, task_launcher

app = FastAPI(title="DataDesk API", version="2.0.0")

# ─── CORS ────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── ROUTERS ─────────────────────────────────────────
app.include_router(analyser.router, prefix="/api/analyser", tags=["analyser"])
app.include_router(task_launcher.router, prefix="/api/task-launcher", tags=["task-launcher"])


@app.get("/api/health")
def health_check():
    """Quick check that the backend is alive - useful when wiring up the frontend."""
    return {"status": "ok", "service": "DataDesk API"}


# ─── SERVE THE BUILT REACT APP ───────────────────────

_frontend_dist = Path(__file__).parent / "frontend" / "dist"
if _frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="frontend")