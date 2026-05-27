import pandas as pd
import logging
from config import *

logger = logging.getLogger("datadesk")


def total_record(dataframe):
    logger.info("total_record() called")
    result = len(dataframe)
    logger.info(f"total_record() returned {result}")
    return result


def total_unique_retailers(dataframe):
    logger.info("total_unique_retailers() called")
    result = dataframe[LIST_NAME_COL].unique()
    logger.info(f"total_unique_retailers() found {len(result)} retailers")
    return result


def total_unique_retailers_count(dataframe):
    logger.info("total_unique_retailers_count() called")
    result = dataframe[LIST_NAME_COL].nunique()
    logger.info(f"total_unique_retailers_count() returned {result}")
    return result


def records_per_retailer(dataframe):
    logger.info("records_per_retailer() called")
    result = dataframe[LIST_NAME_COL].value_counts().reset_index()
    result.columns = ["Retailer", "Record Count"]
    logger.info("records_per_retailer() complete")
    return result


def construction_flag_breakdown(dataframe):
    logger.info("construction_flag_breakdown() called")
    df = dataframe.copy()
    df[CONSTRUCTION_FLAG_COL] = df[CONSTRUCTION_FLAG_COL].fillna(NORMAL)
    breakdown_df = df.groupby([LIST_NAME_COL, CONSTRUCTION_FLAG_COL]).size().unstack(fill_value=0)
    breakdown_df["Total"] = breakdown_df.sum(axis=1)
    breakdown_df = breakdown_df.reset_index()    # ← add this
    logger.info(f"construction_flag_breakdown() complete | {len(breakdown_df)} retailers")
    return breakdown_df


def polygon_status_breakdown(dataframe):
    logger.info("polygon_status_breakdown() called")
    df = dataframe.copy()
    df[POLYGON_STATUS_COL] = df[POLYGON_STATUS_COL].fillna(NORMAL)
    polygon_status_df = df.groupby([LIST_NAME_COL, POLYGON_STATUS_COL]).size().unstack(fill_value=0)
    polygon_status_df["Total"] = polygon_status_df.sum(axis=1)
    polygon_status_df = polygon_status_df.reset_index()    # ← add this
    logger.info(f"polygon_status_breakdown() complete | {len(polygon_status_df)} retailers")
    return polygon_status_df


def duplicate_ali_analysis(dataframe):
    logger.info("duplicate_ali_analysis() called")
    duplicates      = dataframe[dataframe[ALI_COL].duplicated(keep=False)]
    duplicate_count = dataframe[ALI_COL].duplicated().sum()
    unique_count    = dataframe[ALI_COL].nunique()
    total           = len(dataframe)
    logger.info(f"duplicate_ali_analysis() | total: {total} | duplicates: {duplicate_count}")
    return {
        "total"           : total,
        "unique_ali"      : unique_count,
        "duplicate_count" : duplicate_count,
        "duplicate_rows"  : duplicates
    }


def get_full_analysis(dataframe):
    logger.info("get_full_analysis() started")
    result = {
        "total_records"          : total_record(dataframe),
        "unique_retailers"       : total_unique_retailers(dataframe),
        "unique_retailers_count" : total_unique_retailers_count(dataframe),
        "per_retailer"           : records_per_retailer(dataframe),
        "construction_flag"      : construction_flag_breakdown(dataframe),
        "polygon_status"         : polygon_status_breakdown(dataframe),
        "duplicate_ali"          : duplicate_ali_analysis(dataframe)
    }
    logger.info("get_full_analysis() complete")
    return result