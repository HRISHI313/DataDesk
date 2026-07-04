"""
Task Launcher API endpoints.

Wraps the EXACT SAME functions your Streamlit Task Launcher tab calls:
    - utils.file_handler.read_excel / write_multi_sheet_excel
    - utils.validators.validate_file_not_empty / check_required_columns
    - modules.task_launcher.detect_retailer_mode
    - modules.task_launcher.get_retailer_counts
    - modules.task_launcher.calculate_target
    - modules.task_launcher.equal_split
    - modules.task_launcher.random_split_retailer
    - modules.task_launcher.build_output_excel
    - config.LIST_NAME_COL

No business logic is duplicated here. Bug fixes to splitting, targets, or
assignment rules still happen in modules/task_launcher.py only.

DESIGN NOTE: assignment interactions (assign/unassign/bulk-assign/split
inputs/balance tracker) are NOT endpoints here on purpose - they happen
entirely in React state on the frontend, using the retailer_counts returned
by /upload. That's what removes the "every click recomputes everything"
slowness from Streamlit. The backend is only hit twice per task: once on
upload, once on generate.
"""

import io
import json
from datetime import datetime
from typing import Dict, List

import pandas as pd
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from utils.file_handler import read_excel, write_multi_sheet_excel
from utils.validators import validate_file_not_empty, check_required_columns
from utils.upload_cache import store_dataframe, get_entry, clear_entry
from modules.task_launcher import (
    detect_retailer_mode,
    get_retailer_counts,
    calculate_target,
    equal_split,
    random_split_retailer,
    build_output_excel,
)
from config import LIST_NAME_COL

router = APIRouter()


class SingleGenerateRequest(BaseModel):
    upload_id: str
    analyst_names: List[str]
    task_name: str = ""


class MultiGenerateRequest(BaseModel):
    upload_id: str
    analyst_names: List[str]
    retailer_assignments: Dict[str, str]          # {retailer: analyst_name_or_"Split"}
    split_counts: Dict[str, Dict[str, int]] = {}   # {retailer: {analyst_name: count}}
    task_name: str = ""


def _uploaded_file_to_dataframe(file: UploadFile, raw_bytes: bytes):
    buffer = io.BytesIO(raw_bytes)
    buffer.name = file.filename
    return read_excel(buffer)


def _excel_bytes(output) -> bytes:
    """write_multi_sheet_excel's return value gets handed straight to
    st.download_button as `data=`, which accepts either raw bytes or a
    file-like object. Normalize either case to raw bytes for the HTTP
    response body."""
    if isinstance(output, (bytes, bytearray)):
        return bytes(output)
    if hasattr(output, "getvalue"):
        return output.getvalue()
    raise HTTPException(status_code=500, detail="Unexpected Excel output type from write_multi_sheet_excel")


# ─── UPLOAD ──────────────────────────────────────────
@router.post("/upload")
async def upload_task_file(file: UploadFile = File(...)):
    """
    Reads and validates the file, detects single vs multi retailer mode,
    caches the parsed DataFrame, and returns everything the frontend needs
    to render the Task Launcher screen WITHOUT further backend calls until
    Generate.
    """
    raw_bytes = await file.read()

    try:
        df = _uploaded_file_to_dataframe(file, raw_bytes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read file: {e}")

    try:
        validate_file_not_empty(df)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    missing_cols = check_required_columns(df)
    if missing_cols:
        return {
            "needs_mapping": True,
            "missing_columns": missing_cols,
            "available_columns": [str(c) for c in df.columns],
            "row_count": len(df),
        }

    mode = detect_retailer_mode(df)
    retailer_counts = get_retailer_counts(df)
    upload_id = store_dataframe(df, mode)

    return {
        "needs_mapping": False,
        "upload_id": upload_id,
        "mode": mode,
        "total_alis": len(df),
        "retailer_counts": retailer_counts,
    }


@router.post("/upload-with-mapping")
async def upload_task_file_with_mapping(
    file: UploadFile = File(...),
    mapping: str = Form(...),
):
    """Same as /upload, but applies a column rename first (mirrors the
    Analyser's mapping flow)."""
    raw_bytes = await file.read()

    try:
        df = _uploaded_file_to_dataframe(file, raw_bytes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read file: {e}")

    try:
        validate_file_not_empty(df)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        mapping_dict = json.loads(mapping)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="mapping must be valid JSON")

    df = df.rename(columns=mapping_dict)

    missing_cols = check_required_columns(df)
    if missing_cols:
        raise HTTPException(
            status_code=400,
            detail=f"Still missing required columns after mapping: {missing_cols}",
        )

    mode = detect_retailer_mode(df)
    retailer_counts = get_retailer_counts(df)
    upload_id = store_dataframe(df, mode)

    return {
        "needs_mapping": False,
        "upload_id": upload_id,
        "mode": mode,
        "total_alis": len(df),
        "retailer_counts": retailer_counts,
    }


# ─── TARGET CALCULATION ──────────────────────────────
@router.get("/target")
def get_target(upload_id: str, num_analysts: int):
    """Returns (target, remainder) for splitting total_alis across
    num_analysts - called once when the analyst count changes, not per
    click."""
    entry = get_entry(upload_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Upload not found or expired - please re-upload the file.")

    target, remainder = calculate_target(entry["total_alis"], num_analysts)
    return {"target": target, "remainder": remainder}


# ─── SINGLE RETAILER MODE: GENERATE ──────────────────
@router.post("/single/generate")
def generate_single(body: SingleGenerateRequest):
    entry = get_entry(body.upload_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Upload not found or expired - please re-upload the file.")

    df = entry["df"]
    assignments = equal_split(df, body.analyst_names)
    sheets_dict = build_output_excel(assignments)

    clean_name = body.task_name.strip().replace(" ", "_") if body.task_name.strip() else "TaskList"
    filename = f"{clean_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    output = write_multi_sheet_excel(sheets_dict, filename)
    file_bytes = _excel_bytes(output)

    return StreamingResponse(
        io.BytesIO(file_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ─── MULTI RETAILER MODE: GENERATE ───────────────────
@router.post("/multi/generate")
def generate_multi(body: MultiGenerateRequest):
    entry = get_entry(body.upload_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Upload not found or expired - please re-upload the file.")

    df = entry["df"]
    final_assignments = {name: pd.DataFrame() for name in body.analyst_names}

    for retailer, assignment in body.retailer_assignments.items():
        retailer_df = df[df[LIST_NAME_COL] == retailer].copy()

        if assignment == "Split":
            if retailer not in body.split_counts:
                raise HTTPException(status_code=400, detail=f"Missing split counts for retailer: {retailer}")
            try:
                split_result = random_split_retailer(df, retailer, body.split_counts[retailer])
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            for name, split_df in split_result.items():
                final_assignments[name] = pd.concat([final_assignments[name], split_df], ignore_index=True)

        elif assignment in body.analyst_names:
            final_assignments[assignment] = pd.concat([final_assignments[assignment], retailer_df], ignore_index=True)

    sheets_dict = build_output_excel(final_assignments)

    clean_name = body.task_name.strip().replace(" ", "_") if body.task_name.strip() else "TaskList"
    filename = f"{clean_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    output = write_multi_sheet_excel(sheets_dict, filename)
    file_bytes = _excel_bytes(output)

    return StreamingResponse(
        io.BytesIO(file_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/{upload_id}")
def clear_upload(upload_id: str):
    """Frees the cached DataFrame once a task has been generated and the
    user is done, or if they cancel and re-upload a different file."""
    clear_entry(upload_id)
    return {"cleared": True}