"""
Analyser API endpoints.

These wrap the EXACT SAME functions your Streamlit Analyser tab calls:
    - utils.file_handler.read_excel
    - utils.validators.validate_file_not_empty / check_required_columns
    - modules.analyser.get_full_analysis

No business logic is duplicated or reimplemented here. If you need to fix a
bug in the analysis itself (QC rules, pending calculation, polygon coverage,
etc.), fix it in modules/analyser.py like before - this file will pick up
the change automatically since it just calls that function.
"""

import io
import json

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from utils.file_handler import read_excel
from utils.validators import validate_file_not_empty, check_required_columns
from modules.analyser import get_full_analysis
from modules.task_launcher import detect_retailer_mode, get_retailer_counts
from utils.serializers import serialize_for_json
from utils.upload_cache import store_dataframe, get_entry
from config import GEO_ACCURACY_COL, GEO_ACCURACY_VERIFIED_VALUES, LIST_NAME_COL

router = APIRouter()


class LaunchTaskRequest(BaseModel):
    upload_id: str
    selected_retailers: list[str] | None = None  # None = launch all retailers


def _uploaded_file_to_dataframe(file: UploadFile, raw_bytes: bytes):
    """
    Adapts a FastAPI UploadFile into whatever read_excel() expects.

    read_excel() was written against Streamlit's uploaded-file object, which
    behaves like a file-like object with a `.name` attribute (e.g. ends in
    .xlsx/.csv). io.BytesIO accepts an arbitrary `.name` attribute, so we
    build a shim that looks the same to read_excel() without changing it.
    """
    buffer = io.BytesIO(raw_bytes)
    buffer.name = file.filename
    return read_excel(buffer)


@router.post("/upload")
async def upload_and_analyse(file: UploadFile = File(...)):
    """
    First-pass upload: reads the file and checks required columns.

    - If columns are missing, returns needs_mapping=True plus the missing
      columns and the available columns in the file, so the frontend can
      render a mapping form (mirrors handle_column_mapping in app.py).
    - If nothing is missing, runs the full analysis immediately and returns
      the results in one call.
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

    results = get_full_analysis(df)

    upload_id = store_dataframe(df, mode="analyser")

    payload = {
        "needs_mapping": False,
        "row_count": len(df),
        "upload_id": upload_id,
        "results": serialize_for_json(results),
    }
    return JSONResponse(content=payload)


@router.post("/upload-with-mapping")
async def upload_with_mapping(
    file: UploadFile = File(...),
    mapping: str = Form(...),
):
    """
    Second-pass upload: called after the user fills in the column mapping
    form returned by /upload. `mapping` is a JSON string like:
        {"Store Address": "Address", "Store City": "City"}
    (i.e. {existing_column_in_file: required_column_name}), matching the
    same rename direction used in handle_column_mapping().
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

    results = get_full_analysis(df)

    upload_id = store_dataframe(df, mode="analyser")

    payload = {
        "needs_mapping": False,
        "row_count": len(df),
        "upload_id": upload_id,
        "results": serialize_for_json(results),
    }
    return JSONResponse(content=payload)


@router.post("/launch-task-preview")
def launch_task_preview(body: LaunchTaskRequest):
    """
    Shows how many records still need work PER RETAILER, before actually
    launching anything. Retailers with 0 remaining are still included
    (so the frontend can grey them out) rather than hidden - keeps the
    full list of retailers visible for context.
    """
    entry = get_entry(body.upload_id)
    if entry is None:
        raise HTTPException(
            status_code=404,
            detail="Original upload not found or expired - please re-upload and re-analyse the file.",
        )

    df = entry["df"]
    needs_work_mask = ~df[GEO_ACCURACY_COL].isin(GEO_ACCURACY_VERIFIED_VALUES)

    all_retailers = df[LIST_NAME_COL].unique().tolist()
    needs_work_counts = df[needs_work_mask][LIST_NAME_COL].value_counts().to_dict()

    retailers = [
        {"name": name, "needs_work_count": int(needs_work_counts.get(name, 0))}
        for name in all_retailers
    ]
    # Most work-needed first, so the busiest lists are easy to spot
    retailers.sort(key=lambda r: r["needs_work_count"], reverse=True)

    return {"retailers": retailers}


@router.post("/launch-task")
def launch_task(body: LaunchTaskRequest):
    """
    Filters the previously-uploaded file down to records that still need
    work, then hands that subset off in the same shape as Task Launcher's
    own /upload response - so the frontend can jump straight to the
    assignment screen without asking the user to upload the file again.

    THE RULE (confirmed): a record needs launching if its Geo Accuracy is
    NOT already one of the verified-rooftop values - regardless of
    constructionFlag or Polygon Status. Even a Mall Tenant/Multi-Level or
    already-Marked record still needs launching if nobody has actually
    pinned the rooftop location yet. This is a single boolean filter, so
    there's no risk of a record appearing twice.

    If selected_retailers is provided, only those retailers are included -
    letting the user launch a subset of lists instead of everything at
    once. The original upload stays cached either way (not consumed),
    so the same analysis can be launched again later for different
    retailers without re-uploading.
    """
    entry = get_entry(body.upload_id)
    if entry is None:
        raise HTTPException(
            status_code=404,
            detail="Original upload not found or expired - please re-upload and re-analyse the file.",
        )

    df = entry["df"]

    needs_work = df[~df[GEO_ACCURACY_COL].isin(GEO_ACCURACY_VERIFIED_VALUES)].copy()

    if body.selected_retailers is not None:
        needs_work = needs_work[needs_work[LIST_NAME_COL].isin(body.selected_retailers)]

    if len(needs_work) == 0:
        return {
            "upload_id": None,
            "mode": None,
            "total_alis": 0,
            "retailer_counts": {},
        }

    mode = detect_retailer_mode(needs_work)
    retailer_counts = get_retailer_counts(needs_work)
    new_upload_id = store_dataframe(needs_work, mode)

    return {
        "upload_id": new_upload_id,
        "mode": mode,
        "total_alis": len(needs_work),
        "retailer_counts": retailer_counts,
    }