"""
DataDesk V2 - FastAPI entrypoint.

This does NOT reimplement any business logic. It imports and calls the same
modules/analyser.py, config.py, and utils/ files that the existing Streamlit
app (app.py) already uses. FastAPI is just a new way to reach that logic
over HTTP, so the React frontend can call it.

Run locally with:
    uvicorn main:app --reload --port 8000

Place this file at the ROOT of your existing DataDesk project, next to
app.py, config.py, modules/, and utils/ - it imports from those directly.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routers import analyser, task_launcher

app = FastAPI(title="DataDesk API", version="2.0.0")

# ─── CORS ────────────────────────────────────────────
# During development, React (Vite) runs on its own port (usually 5173) and
# needs permission to call this API on port 8000. Once we build the React
# app and serve it as static files from FastAPI (later step), this can be
# tightened since everything will be same-origin.
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
# After running `npm run build` inside frontend/, Vite outputs plain static
# files (HTML/CSS/JS) to frontend/dist/. Mounting that folder here means
# FastAPI serves both the API and the UI from ONE process - no separate
# Node/Vite server needed to actually run the app. This only works once
# frontend/dist/ exists (i.e. after you've run the build at least once).
_frontend_dist = Path(__file__).parent / "frontend" / "dist"
if _frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="frontend")