"""
Simple in-memory cache for uploaded task-launcher files.

Task Launcher involves many small interactions (assign, split, bulk assign)
before a final "Generate Excel" - in Streamlit these all read from
st.session_state. Here, we parse the file ONCE on upload and cache the
DataFrame under a short-lived upload_id, so the frontend only needs to send
that id (not the whole file again) for later calls like /generate.

This is intentionally simple (a plain dict) since DataDesk runs locally,
single-user per machine - no need for Redis/a database. If the FastAPI
process restarts, the cache clears and the user just re-uploads. That's an
acceptable tradeoff for a zero-budget internal tool.
"""

import uuid

_cache: dict = {}


def store_dataframe(df, mode: str) -> str:
    """Cache a parsed DataFrame and return a new upload_id referencing it."""
    upload_id = str(uuid.uuid4())
    _cache[upload_id] = {
        "df": df,
        "mode": mode,
        "total_alis": len(df),
    }
    return upload_id


def get_entry(upload_id: str) -> dict | None:
    """Retrieve the cached entry (df, mode, total_alis) for an upload_id."""
    return _cache.get(upload_id)


def clear_entry(upload_id: str) -> None:
    """Remove a cached entry once it's no longer needed (e.g. after generate)."""
    _cache.pop(upload_id, None)