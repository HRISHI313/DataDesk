"""
JSON serialization helpers for API responses.

get_full_analysis() (and other analyser/comparator functions) return nested
dicts that contain pandas DataFrames and numpy scalar types (np.int64,
np.float64, etc). Neither serializes to JSON out of the box. Rather than
touching modules/analyser.py to change what it returns, we convert the
result at the API boundary - the business logic module stays untouched.
"""

import math
import numpy as np
import pandas as pd


def serialize_for_json(obj):
    """
    Recursively walk a result (dict / list / DataFrame / numpy scalar / etc.)
    and return a plain-Python, JSON-safe equivalent.

    - DataFrame -> list of row dicts (NaN -> None, since NaN is not valid JSON)
    - numpy int/float -> native Python int/float
    - dict / list -> recursed into
    - everything else -> returned as-is
    """
    if isinstance(obj, pd.DataFrame):
        # NOTE: we do NOT use obj.where(pd.notnull(obj), None) here - pandas
        # silently casts None back into NaN for numeric-dtype columns (the
        # column keeps its float64 dtype, which can't hold a real None).
        # That was the cause of a "nan is not JSON compliant" crash before.
        # Instead, convert to plain dicts first, then recursively clean each
        # individual value below, which correctly catches NaN regardless of
        # column dtype.
        records = obj.to_dict(orient="records")
        return [serialize_for_json(record) for record in records]

    if isinstance(obj, pd.Series):
        return serialize_for_json(obj.to_dict())

    if isinstance(obj, pd.Index):
        return serialize_for_json(list(obj))

    if isinstance(obj, pd.api.extensions.ExtensionArray):
        return serialize_for_json(list(obj))

    if isinstance(obj, np.ndarray):
        return serialize_for_json(obj.tolist())

    if isinstance(obj, dict):
        return {key: serialize_for_json(value) for key, value in obj.items()}

    if isinstance(obj, (list, tuple)):
        return [serialize_for_json(item) for item in obj]

    if isinstance(obj, (np.integer,)):
        return int(obj)

    if isinstance(obj, (np.floating,)):
        f = float(obj)
        return None if math.isnan(f) else f

    if isinstance(obj, np.bool_):
        return bool(obj)

    if isinstance(obj, float) and math.isnan(obj):
        return None

    # Dates/timestamps: pandas can return pd.Timestamp, pd.NaT, or raw
    # numpy datetime64/timedelta64 depending on the column dtype. None of
    # these are guaranteed to survive FastAPI's default JSON encoding.
    if obj is pd.NaT:
        return None

    if isinstance(obj, (pd.Timestamp, np.datetime64)):
        ts = pd.Timestamp(obj)
        return None if pd.isna(ts) else ts.isoformat()

    if isinstance(obj, (pd.Timedelta, np.timedelta64)):
        return str(pd.Timedelta(obj))

    import datetime as _dt
    if isinstance(obj, (_dt.date, _dt.datetime)):
        return obj.isoformat()

    # Plain JSON-safe primitives pass through untouched.
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj

    # Last-resort fallback: anything else unrecognized (e.g. a numpy array,
    # a pandas Index, a custom object) gets stringified rather than crashing
    # the whole response. This trades a slightly odd value for a working
    # endpoint - worth revisiting if you spot "<...>" style strings in the
    # response, since that means something new needs a proper case above.
    try:
        return str(obj)
    except Exception:
        return None