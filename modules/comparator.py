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


# ─── HELPER ─────────────────────────────────────────
def extract_columns(df):
    logger.info("extract_columns() called")
    available = [col for col in OUTPUT_COLUMNS if col in df.columns]
    result = df[available].copy()
    logger.info(f"extract_columns() complete | {len(available)} columns extracted")
    return result


# ─── TYPE 1 — ALI COMPARISON ────────────────────────
def compare_by_ali(df1, df2):
    logger.info("compare_by_ali() called")

    d1 = extract_columns(df1)
    d2 = extract_columns(df2)

    matched = d1[d1[ALI_COL].isin(d2[ALI_COL])].copy()
    logger.info(f"compare_by_ali() | matched: {len(matched)}")

    only_file1 = d1[~d1[ALI_COL].isin(d2[ALI_COL])].copy()
    logger.info(f"compare_by_ali() | only_file1: {len(only_file1)}")

    only_file2 = d2[~d2[ALI_COL].isin(d1[ALI_COL])].copy()
    logger.info(f"compare_by_ali() | only_file2: {len(only_file2)}")

    conflicts = _get_conflicts(d1, d2, ALI_COL)
    logger.info(f"compare_by_ali() | conflicts: {len(conflicts)}")

    logger.info("compare_by_ali() complete")
    return {
        "matched"    : matched,
        "only_file1" : only_file1,
        "only_file2" : only_file2,
        "conflicts"  : conflicts
    }


# ─── TYPE 2 — ADDRESS COMPARISON ────────────────────
def compare_by_address(df1, df2):
    logger.info("compare_by_address() called")

    d1 = extract_columns(df1)
    d2 = extract_columns(df2)

    matched = d1[d1[ADDRESS_COL].isin(d2[ADDRESS_COL])].copy()
    logger.info(f"compare_by_address() | matched: {len(matched)}")

    only_file1 = d1[~d1[ADDRESS_COL].isin(d2[ADDRESS_COL])].copy()
    logger.info(f"compare_by_address() | only_file1: {len(only_file1)}")

    only_file2 = d2[~d2[ADDRESS_COL].isin(d1[ADDRESS_COL])].copy()
    logger.info(f"compare_by_address() | only_file2: {len(only_file2)}")

    conflicts = _get_conflicts(d1, d2, ADDRESS_COL)
    logger.info(f"compare_by_address() | conflicts: {len(conflicts)}")

    logger.info("compare_by_address() complete")
    return {
        "matched"    : matched,
        "only_file1" : only_file1,
        "only_file2" : only_file2,
        "conflicts"  : conflicts
    }


# ─── TYPE 3 — MIGRATION COMPARISON ──────────────────
def compare_migration(df1, df2):
    logger.info("compare_migration() called")

    d1 = extract_columns(df1)
    d2 = extract_columns(df2)

    # merge on address
    merged = d1.merge(
        d2,
        on       = ADDRESS_COL,
        how      = "outer",
        suffixes = ("_old", "_new"),
        indicator = True
    )
    logger.info(f"compare_migration() | merged shape: {merged.shape}")

    # only in old file
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

    # only in new file
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

    # address matched records
    both = merged[merged["_merge"] == "both"].copy()
    logger.info(f"compare_migration() | address matched: {len(both)}")

    # ALI changed + polygon lost
    ali_changed_polygon_lost = both[
        (both[f"{ALI_COL}_old"] != both[f"{ALI_COL}_new"]) &
        (both[f"{POLYGON_STATUS_COL}_old"].notna()) &
        (both[f"{POLYGON_STATUS_COL}_new"].isna())
    ].copy()
    logger.info(f"compare_migration() | ali_changed_polygon_lost: {len(ali_changed_polygon_lost)}")

    # ALI changed + never marked
    ali_changed_never_marked = both[
        (both[f"{ALI_COL}_old"] != both[f"{ALI_COL}_new"]) &
        (both[f"{POLYGON_STATUS_COL}_old"].isna()) &
        (both[f"{POLYGON_STATUS_COL}_new"].isna())
    ].copy()
    logger.info(f"compare_migration() | ali_changed_never_marked: {len(ali_changed_never_marked)}")

    # polygon lost only — ALI same
    polygon_lost_only = both[
        (both[f"{ALI_COL}_old"] == both[f"{ALI_COL}_new"]) &
        (both[f"{POLYGON_STATUS_COL}_old"].notna()) &
        (both[f"{POLYGON_STATUS_COL}_new"].isna())
    ].copy()
    logger.info(f"compare_migration() | polygon_lost_only: {len(polygon_lost_only)}")

    # clean migration
    clean = both[
        (both[f"{ALI_COL}_old"] == both[f"{ALI_COL}_new"]) &
        (both[f"{POLYGON_STATUS_COL}_old"] == both[f"{POLYGON_STATUS_COL}_new"])
    ].copy()
    logger.info(f"compare_migration() | clean: {len(clean)}")

    logger.info("compare_migration() complete")
    return {
        "only_old"                : only_old,
        "only_new"                : only_new,
        "ali_changed_polygon_lost": ali_changed_polygon_lost,
        "ali_changed_never_marked": ali_changed_never_marked,
        "polygon_lost_only"       : polygon_lost_only,
        "clean"                   : clean
    }


# ─── CONFLICTS HELPER ───────────────────────────────
def _get_conflicts(df1, df2, key_col):
    logger.info(f"_get_conflicts() called | key: {key_col}")

    # get records where key exists in both
    common_keys = set(df1[key_col]).intersection(set(df2[key_col]))

    d1_common = df1[df1[key_col].isin(common_keys)].copy()
    d2_common = df2[df2[key_col].isin(common_keys)].copy()

    # merge on key column
    merged = d1_common.merge(
        d2_common,
        on       = key_col,
        suffixes = ("_file1", "_file2")
    )

    # find rows where any other column differs
    check_cols = [col for col in OUTPUT_COLUMNS if col != key_col and col != LIST_NAME_COL]

    conflict_mask = pd.Series(False, index=merged.index)
    for col in check_cols:
        if f"{col}_file1" in merged.columns and f"{col}_file2" in merged.columns:
            conflict_mask |= merged[f"{col}_file1"] != merged[f"{col}_file2"]

    conflicts = merged[conflict_mask].copy()
    logger.info(f"_get_conflicts() complete | conflicts: {len(conflicts)}")
    return conflicts


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