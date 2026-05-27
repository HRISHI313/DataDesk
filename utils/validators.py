import pandas as pd
import logging
from config import *

logger = logging.getLogger("datadesk")

# columns that must exist in every file
REQUIRED_COLUMNS = [
    ALI_COL,
    LIST_NAME_COL,
    STORE_NAME_COL,
    ADDRESS_COL,
    CITY_COL,
    STATE_COL,
    CONSTRUCTION_FLAG_COL,
    POLYGON_STATUS_COL,
    LATITUDE_COL,
    LONGITUDE_COL
]

def validate_file_not_empty(df):
    logger.info("Validating file is not empty")
    if df.empty:
        logger.error("Uploaded file is empty")
        raise ValueError("Uploaded file is empty. Please upload a valid file.")
    logger.info(f"File has {len(df)} rows")
    return True

def validate_required_columns(df):
    logger.info("Validating required columns")
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        logger.error(f"Missing columns: {missing}")
        raise ValueError(f"Missing required columns: {missing}")
    logger.info("All required columns present")
    return True