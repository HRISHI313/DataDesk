# modules/comparator.py

import pandas as pd
import logging
from config import *

logger = logging.getLogger("datadesk")

# ─── OUTPUT COLUMNS ─────────────────────────────────
OUTPUT_COLUMNS = [
    LIST_NAME_COL,
    ALI_COL,
    ADDRESS_COL,
    CITY_COL,
    ZIP_COL,
    POLYGON_STATUS_COL
]


# ─── HELPER — EXTRACT COLUMNS ───────────────────────
def extract_columns(df):
    logger.info("extract_columns() called")
    available = [col for col in OUTPUT_COLUMNS if col in df.columns]
    result    = df[available].copy()
    logger.info(f"extract_columns() complete | {len(available)} columns extracted")
    return result


# ─── HELPER — GET UNMATCHED ─────────────────────────
def _get_unmatched(only_file1, only_file2, key_col):
    logger.info(f"_get_unmatched() called | key: {key_col}")

    # add source column
    only_file1 = only_file1.copy()
    only_file2 = only_file2.copy()
    only_file1["Source"] = "File 1"
    only_file2["Source"] = "File 2"

    # combine
    unmatched = pd.concat([only_file1, only_file2], ignore_index=True)

    # flag duplicates on key column
    unmatched["Duplicate"] = unmatched[key_col].duplicated(keep=False).map({
        True  : "⚠️ Yes",
        False : "No"
    })

    duplicate_count = unmatched[key_col].duplicated().sum()

    logger.info(f"_get_unmatched() complete | total: {len(unmatched)} | duplicates: {duplicate_count}")
    return unmatched, duplicate_count


# ─── HELPER — GET CONFLICTS ─────────────────────────
def _get_conflicts(df1, df2, key_col, check_col):
    logger.info(f"_get_conflicts() called | key: {key_col} | check: {check_col}")

    common_keys = set(df1[key_col]).intersection(set(df2[key_col]))

    d1_common = df1[df1[key_col].isin(common_keys)].copy()
    d2_common = df2[df2[key_col].isin(common_keys)].copy()

    d1_common = d1_common.drop_duplicates(subset=[key_col])
    d2_common = d2_common.drop_duplicates(subset=[key_col])

    d1_common = d1_common.fillna("")
    d2_common = d2_common.fillna("")

    merged = d1_common.merge(
        d2_common,
        on       = key_col,
        suffixes = ("_file1", "_file2")
    )

    conflict_mask = (
        merged[f"{check_col}_file1"] != merged[f"{check_col}_file2"]
    )

    conflicts = merged[conflict_mask].copy()
    logger.info(f"_get_conflicts() complete | conflicts: {len(conflicts)}")
    return conflicts


# ─── TYPE 1 — ALI COMPARISON ────────────────────────
def compare_by_ali(df1, df2):
    logger.info("compare_by_ali() started")
    logger.info(f"compare_by_ali() | File1: {len(df1)} rows | File2: {len(df2)} rows")

    d1 = extract_columns(df1)
    d2 = extract_columns(df2)

    matched    = d1[d1[ALI_COL].isin(d2[ALI_COL])].copy()
    only_file1 = d1[~d1[ALI_COL].isin(d2[ALI_COL])].copy()
    only_file2 = d2[~d2[ALI_COL].isin(d1[ALI_COL])].copy()

    unmatched, duplicate_count = _get_unmatched(only_file1, only_file2, ALI_COL)
    conflicts                  = _get_conflicts(d1, d2, ALI_COL, ADDRESS_COL)

    logger.info(f"compare_by_ali() | matched: {len(matched)} | unmatched: {len(unmatched)} | conflicts: {len(conflicts)}")
    logger.info("compare_by_ali() complete")

    return {
        "matched"                   : matched,
        "unmatched"                 : unmatched,
        "unmatched_duplicate_count" : duplicate_count,
        "conflicts"                 : conflicts
    }


# ─── TYPE 2 — ADDRESS COMPARISON ────────────────────
def compare_by_address(df1, df2):
    logger.info("compare_by_address() started")
    logger.info(f"compare_by_address() | File1: {len(df1)} rows | File2: {len(df2)} rows")

    d1 = extract_columns(df1)
    d2 = extract_columns(df2)

    matched    = d1[d1[ADDRESS_COL].isin(d2[ADDRESS_COL])].copy()
    only_file1 = d1[~d1[ADDRESS_COL].isin(d2[ADDRESS_COL])].copy()
    only_file2 = d2[~d2[ADDRESS_COL].isin(d1[ADDRESS_COL])].copy()

    unmatched, duplicate_count = _get_unmatched(only_file1, only_file2, ADDRESS_COL)
    conflicts                  = _get_conflicts(d1, d2, ADDRESS_COL, ALI_COL)

    logger.info(f"compare_by_address() | matched: {len(matched)} | unmatched: {len(unmatched)} | conflicts: {len(conflicts)}")
    logger.info("compare_by_address() complete")

    return {
        "matched"                   : matched,
        "unmatched"                 : unmatched,
        "unmatched_duplicate_count" : duplicate_count,
        "conflicts"                 : conflicts
    }


# ─── TYPE 3 — MIGRATION COMPARISON ──────────────────
def compare_migration(df1, df2):
    logger.info("compare_migration() called")

    d1 = extract_columns(df1)
    d2 = extract_columns(df2)

    merged = d1.merge(
        d2,
        on        = ADDRESS_COL,
        how       = "outer",
        suffixes  = ("_old", "_new"),
        indicator = True
    )
    logger.info(f"compare_migration() | merged shape: {merged.shape}")

    only_old = merged[merged["_merge"] == "left_only"].copy()
    only_old = only_old[[
        f"{LIST_NAME_COL}_old",
        f"{ALI_COL}_old",
        ADDRESS_COL,
        f"{CITY_COL}_old",
        f"{ZIP_COL}_old",
        f"{POLYGON_STATUS_COL}_old"
    ]]
    only_old.columns = [LIST_NAME_COL, ALI_COL, ADDRESS_COL, CITY_COL, ZIP_COL, POLYGON_STATUS_COL]
    logger.info(f"compare_migration() | only_old: {len(only_old)}")

    only_new = merged[merged["_merge"] == "right_only"].copy()
    only_new = only_new[[
        f"{LIST_NAME_COL}_new",
        f"{ALI_COL}_new",
        ADDRESS_COL,
        f"{CITY_COL}_new",
        f"{ZIP_COL}_new",
        f"{POLYGON_STATUS_COL}_new"
    ]]
    only_new.columns = [LIST_NAME_COL, ALI_COL, ADDRESS_COL, CITY_COL, ZIP_COL, POLYGON_STATUS_COL]
    logger.info(f"compare_migration() | only_new: {len(only_new)}")

    both = merged[merged["_merge"] == "both"].copy()
    logger.info(f"compare_migration() | address matched: {len(both)}")

    ali_changed_polygon_lost = both[
        (both[f"{ALI_COL}_old"] != both[f"{ALI_COL}_new"]) &
        (both[f"{POLYGON_STATUS_COL}_old"].notna()) &
        (both[f"{POLYGON_STATUS_COL}_new"].isna())
    ].copy()

    ali_changed_never_marked = both[
        (both[f"{ALI_COL}_old"] != both[f"{ALI_COL}_new"]) &
        (both[f"{POLYGON_STATUS_COL}_old"].isna()) &
        (both[f"{POLYGON_STATUS_COL}_new"].isna())
    ].copy()

    polygon_lost_only = both[
        (both[f"{ALI_COL}_old"] == both[f"{ALI_COL}_new"]) &
        (both[f"{POLYGON_STATUS_COL}_old"].notna()) &
        (both[f"{POLYGON_STATUS_COL}_new"].isna())
    ].copy()

    clean = both[
        (both[f"{ALI_COL}_old"] == both[f"{ALI_COL}_new"]) &
        (both[f"{POLYGON_STATUS_COL}_old"] == both[f"{POLYGON_STATUS_COL}_new"])
    ].copy()

    logger.info(f"compare_migration() | ali_changed_polygon_lost: {len(ali_changed_polygon_lost)} | ali_changed_never_marked: {len(ali_changed_never_marked)} | polygon_lost_only: {len(polygon_lost_only)} | clean: {len(clean)}")
    logger.info("compare_migration() complete")

    return {
        "only_old"                : only_old,
        "only_new"                : only_new,
        "ali_changed_polygon_lost": ali_changed_polygon_lost,
        "ali_changed_never_marked": ali_changed_never_marked,
        "polygon_lost_only"       : polygon_lost_only,
        "clean"                   : clean
    }


# ─── MASTER FUNCTION ────────────────────────────────
def get_comparison_summary(df1, df2, comparison_type):
    logger.info(f"get_comparison_summary() called | type: {comparison_type}")

    if comparison_type == COMPARISON_ALI:
        result = compare_by_ali(df1, df2)

    elif comparison_type == COMPARISON_ADDRESS:
        result = compare_by_address(df1, df2)

    elif comparison_type == COMPARISON_MIGRATION:
        result = compare_migration(df1, df2)

    else:
        logger.error(f"Unknown comparison type: {comparison_type}")
        raise ValueError(f"Unknown comparison type: {comparison_type}")

    logger.info("get_comparison_summary() complete")
    return result



