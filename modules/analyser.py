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

def construction_flag_percentages(dataframe):
    logger.info("construction_flag_percentages() called")
    df = dataframe.copy()
    df[CONSTRUCTION_FLAG_COL] = df[CONSTRUCTION_FLAG_COL].fillna(NORMAL)
    total = len(df)
    counts = df[CONSTRUCTION_FLAG_COL].value_counts()
    result = {
        "Construction" : {
            "count" : int(counts.get(CONSTRUCTION, 0)),
            "pct"   : round(counts.get(CONSTRUCTION, 0) / total * 100, 1)
        },
        "Mall Tenant"  : {
            "count" : int(counts.get(MALL_TENANT, 0)),
            "pct"   : round(counts.get(MALL_TENANT, 0) / total * 100, 1)
        },
        "Multi Level"  : {
            "count" : int(counts.get(MULTI_LEVEL, 0)),
            "pct"   : round(counts.get(MULTI_LEVEL, 0) / total * 100, 1)
        },
        "Normal"       : {
            "count" : int(counts.get(NORMAL, 0)),
            "pct"   : round(counts.get(NORMAL, 0) / total * 100, 1)
        }
    }
    logger.info(f"construction_flag_percentages() complete")
    return result


def polygon_status_percentages(dataframe):
    logger.info("polygon_status_percentages() called")
    total       = len(dataframe)
    verified    = int(dataframe[POLYGON_STATUS_COL].eq(VERIFIED_QA).sum())
    unverified  = total - verified
    result = {
        "Verified QA" : {
            "count" : verified,
            "pct"   : round(verified / total * 100, 1)
        },
        "Unverified"  : {
            "count" : unverified,
            "pct"   : round(unverified / total * 100, 1)
        }
    }
    logger.info(f"polygon_status_percentages() complete")
    return result


def parent_ali_percentages(dataframe):
    logger.info("parent_ali_percentages() called")
    df    = dataframe.copy()
    total = len(df)

    connected = int(df[PARENT_ALI_COL].notna().sum())
    unknown   = total - connected

    # breakdown by retailer
    df["Parent Status"] = df[PARENT_ALI_COL].apply(
        lambda x: "Connected" if pd.notna(x) else "Unknown"
    )

    per_retailer = df.groupby(
        [LIST_NAME_COL, "Parent Status"]
    ).size().unstack(fill_value=0).reset_index()

    per_retailer["Total"] = per_retailer.select_dtypes("number").sum(axis=1)

    result = {
        "connected"    : {
            "count" : connected,
            "pct"   : round(connected / total * 100, 1)
        },
        "unknown"      : {
            "count" : unknown,
            "pct"   : round(unknown / total * 100, 1)
        },
        "per_retailer" : per_retailer
    }

    logger.info(f"parent_ali_percentages() complete | connected: {connected} | unknown: {unknown}")
    return result

def qc_error_check(dataframe):
    logger.info("qc_error_check() called")
    df = dataframe.copy()

    # records that should NEVER have polygon status
    # but do have a value in Polygon Status column
    mall_tenant_errors = df[
        (df[CONSTRUCTION_FLAG_COL] == MALL_TENANT) &
        (df[POLYGON_STATUS_COL].notna())
    ]

    multi_level_errors = df[
        (df[CONSTRUCTION_FLAG_COL] == MULTI_LEVEL) &
        (df[POLYGON_STATUS_COL].notna())
    ]

    # Construction errors — broadened (was: Polygon Status notna() only).
    # A Construction record is contradictory if EITHER:
    #   - it already has a Polygon Status set (old check), OR
    #   - its Geo Accuracy is already a verified-rooftop value, meaning an
    #     analyst has manually pinned the exact location - which shouldn't
    #     happen for a site still under construction, even if Polygon
    #     Status hasn't been officially set yet.
    # NOTE: this is a judgment call folding the new rooftop-contradiction
    # case into the existing construction_errors bucket rather than adding
    # a 4th separate QC category - flag if you'd rather split it out.
    construction_errors = df[
        (df[CONSTRUCTION_FLAG_COL] == CONSTRUCTION) &
        (
            (df[POLYGON_STATUS_COL].notna()) |
            (df[GEO_ACCURACY_COL].isin(GEO_ACCURACY_VERIFIED_VALUES))
        )
    ]

    total_errors = (
        len(mall_tenant_errors) +
        len(multi_level_errors) +
        len(construction_errors)
    )

    logger.info(f"qc_error_check() | mall_tenant: {len(mall_tenant_errors)} | multi_level: {len(multi_level_errors)} | construction: {len(construction_errors)}")

    return {
        "total_errors"        : total_errors,
        "mall_tenant_errors"  : mall_tenant_errors,
        "multi_level_errors"  : multi_level_errors,
        "construction_errors" : construction_errors
    }

def polygon_coverage(dataframe):
    logger.info("polygon_coverage() called")
    df    = dataframe.copy()
    total = len(df)

    # normalize — treat Draft and empty as not done
    df[POLYGON_STATUS_COL]     = df[POLYGON_STATUS_COL].fillna("None")
    df[CONSTRUCTION_FLAG_COL]  = df[CONSTRUCTION_FLAG_COL].fillna(NORMAL)

    # ── MARKED ──────────────────────────────────────
    # Combined into ONE mask (rather than summing separate filter lengths)
    # so a row matching more than one condition at once - e.g. a QC-error
    # row like Multi-Level WITH a Polygon Status set - doesn't get counted
    # twice. That double-counting bug existed in the original code; this
    # fixes it as part of adding the new rooftop-accuracy rule.

    # Condition 1 — Polygon Status verified
    cond1_verified_status = df[POLYGON_STATUS_COL].isin([VERIFIED_QA, VERIFIED_ADMIN])

    # Condition 2 — constructionFlag = Mall Tenant or Multi Level
    cond2_flagged_type = df[CONSTRUCTION_FLAG_COL].isin([MALL_TENANT, MULTI_LEVEL])

    # Condition 3 (NEW) — Polygon Status still None/Draft, but Geo Accuracy
    # is already a verified-rooftop value. Means an analyst has manually
    # pinned the exact location using the geofencer, even though Polygon
    # Status hasn't caught up yet - so treat it as Marked.
    # Restricted to Normal-flagged records only:
    #   - Mall Tenant/Multi-Level already covered by condition 2
    #   - Construction is deliberately EXCLUDED - those always stay
    #     Pending regardless of Geo Accuracy (a rooftop-verified
    #     Construction record is a QC error, not a completed one)
    cond3_rooftop_verified = (
        (df[POLYGON_STATUS_COL].isin(["None", "Draft"])) &
        (df[CONSTRUCTION_FLAG_COL] == NORMAL) &
        (df[GEO_ACCURACY_COL].isin(GEO_ACCURACY_VERIFIED_VALUES))
    )

    marked_mask = cond1_verified_status | cond2_flagged_type | cond3_rooftop_verified
    marked_count = int(marked_mask.sum())

    # Kept separately for the "Polygon Done" breakdown metric below -
    # deliberately NOT deduplicated against the other conditions, since
    # this one specifically describes "Polygon Status is explicitly set",
    # regardless of any overlap with Mall Tenant/Multi-Level QC errors.
    filter1_marked = df[cond1_verified_status]

    # ── PENDING ──────────────────────────────────────
    # Same as before, EXCEPT Normal-flagged records with a verified-rooftop
    # Geo Accuracy are excluded here (they moved to Marked via filter3
    # above). Construction records stay Pending unconditionally.
    pending_rows = df[
        (df[POLYGON_STATUS_COL].isin(["None", "Draft"])) &
        (
            (df[CONSTRUCTION_FLAG_COL] == CONSTRUCTION) |
            (
                (df[CONSTRUCTION_FLAG_COL] == NORMAL) &
                (~df[GEO_ACCURACY_COL].isin(GEO_ACCURACY_VERIFIED_VALUES))
            )
        )
    ]

    pending_count = len(pending_rows)

    # ── VIEW BREAKDOWN ───────────────────────────────
    # Polygon Done
    polygon_done_count = len(filter1_marked)

    # Polygon Missing — same definition as pending_count now
    polygon_missing_count = pending_count

    # Mall Tenant count
    mall_tenant_count = len(df[df[CONSTRUCTION_FLAG_COL] == MALL_TENANT])

    # Multi Level count
    multi_level_count = len(df[df[CONSTRUCTION_FLAG_COL] == MULTI_LEVEL])

    # Construction count
    construction_count = len(df[df[CONSTRUCTION_FLAG_COL] == CONSTRUCTION])

    result = {
        "total"                 : total,
        "marked_count"          : marked_count,
        "marked_pct"            : round(marked_count / total * 100, 1),
        "pending_count"         : pending_count,
        "pending_pct"           : round(pending_count / total * 100, 1),
        "polygon_done_count"    : polygon_done_count,
        "polygon_missing_count" : polygon_missing_count,
        "mall_tenant_count"     : mall_tenant_count,
        "multi_level_count"     : multi_level_count,
        "construction_count"    : construction_count,
        # NOTE: pending_rows dropped from the returned dict per decision -
        # the raw row-by-row pending list wasn't being used for anything.
        # pending_count above still reflects the correct total.
    }
    logger.info(f"polygon_coverage() | marked: {marked_count} | pending: {pending_count}")
    return result


def get_full_analysis(dataframe):
    logger.info("get_full_analysis() started")

    polygon_cov = polygon_coverage(dataframe)    # ← call once, store result

    result = {
        "total_records"          : total_record(dataframe),
        "unique_retailers"       : total_unique_retailers(dataframe),
        "unique_retailers_count" : total_unique_retailers_count(dataframe),
        "per_retailer"           : records_per_retailer(dataframe),
        "construction_flag"      : construction_flag_breakdown(dataframe),
        "construction_pct"       : construction_flag_percentages(dataframe),
        "polygon_status"         : polygon_status_breakdown(dataframe),
        "polygon_pct"            : polygon_status_percentages(dataframe),
        "duplicate_ali"          : duplicate_ali_analysis(dataframe),
        "parent_ali"             : parent_ali_percentages(dataframe),
        "qc_errors"              : qc_error_check(dataframe),
        "polygon_coverage"       : polygon_cov         
    }
    logger.info("get_full_analysis() complete")
    return result