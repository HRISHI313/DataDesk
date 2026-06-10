import pandas as pd
import logging
import random
from config import *

logger = logging.getLogger("datadesk")

# ─── ANALYST FILL COLUMNS ───────────────────────────
ANALYST_FILL_COLUMNS = [
    "Date",
    POLYGON_STATUS_COL,
    "Source-1",
    "Source-2",
    "Remark"
]


# ─── DETECT MODE ────────────────────────────────────
def detect_retailer_mode(df):
    logger.info("detect_retailer_mode() called")
    unique_retailers = df[LIST_NAME_COL].nunique()
    mode = "single" if unique_retailers == 1 else "multi"
    logger.info(f"detect_retailer_mode() | unique retailers: {unique_retailers} | mode: {mode}")
    return mode


# ─── RETAILER COUNTS ────────────────────────────────
def get_retailer_counts(df):
    logger.info("get_retailer_counts() called")
    counts = df[LIST_NAME_COL].value_counts().to_dict()
    logger.info(f"get_retailer_counts() | {len(counts)} retailers found")
    return counts


# ─── CALCULATE TARGET ───────────────────────────────
def calculate_target(total, num_analysts):
    logger.info(f"calculate_target() called | total: {total} | analysts: {num_analysts}")
    target    = total // num_analysts
    remainder = total % num_analysts
    logger.info(f"calculate_target() | target: {target} | remainder: {remainder}")
    return target, remainder


# ─── EQUAL SPLIT — SINGLE MODE ──────────────────────
def equal_split(df, analyst_names):
    logger.info("equal_split() called")
    num_analysts      = len(analyst_names)
    total             = len(df)
    target, remainder = calculate_target(total, num_analysts)

    df_shuffled = df.sample(frac=1).reset_index(drop=True)

    assignments = {}
    start       = 0

    for i, name in enumerate(analyst_names):
        extra              = remainder if i == 0 else 0
        end                = start + target + extra
        assignments[name]  = df_shuffled.iloc[start:end].copy()
        logger.info(f"equal_split() | {name}: {len(assignments[name])} records")
        start = end

    logger.info("equal_split() complete")
    return assignments


# ─── RANDOM SPLIT — ONE RETAILER ────────────────────
def random_split_retailer(df, retailer_name, split_counts):
    logger.info(f"random_split_retailer() called | retailer: {retailer_name}")

    retailer_df     = df[df[LIST_NAME_COL] == retailer_name].copy()
    retailer_df     = retailer_df.sample(frac=1).reset_index(drop=True)
    total_requested = sum(split_counts.values())
    total_available = len(retailer_df)

    if total_requested != total_available:
        logger.error(f"random_split_retailer() | requested {total_requested} but retailer has {total_available}")
        raise ValueError(f"Numbers do not add up. Requested {total_requested} but retailer has {total_available} ALIs.")

    result = {}
    start  = 0

    for analyst_name, count in split_counts.items():
        result[analyst_name] = retailer_df.iloc[start:start + count].copy()
        logger.info(f"random_split_retailer() | {analyst_name}: {count} records")
        start += count

    logger.info("random_split_retailer() complete")
    return result


# ─── CHECK UNASSIGNED ───────────────────────────────
def check_unassigned(df, assignments):
    logger.info("check_unassigned() called")

    assigned_alis   = set()
    for analyst_df in assignments.values():
        assigned_alis.update(analyst_df[ALI_COL].tolist())

    all_alis         = set(df[ALI_COL].tolist())
    unassigned_count = len(all_alis - assigned_alis)

    logger.info(f"check_unassigned() | unassigned: {unassigned_count}")
    return unassigned_count


# ─── BUILD OUTPUT EXCEL ──────────────────────────────
def build_output_excel(assignments):
    logger.info("build_output_excel() called")

    sheets_dict = {}

    # 1. Create Summary Sheet
    total_assigned = sum(len(df) for df in assignments.values())
    summary_rows = []
    for analyst_name, analyst_df in assignments.items():
        count = len(analyst_df)
        pct = round(count / total_assigned * 100, 1) if total_assigned > 0 else 0.0
        
        # Get unique retailers
        if LIST_NAME_COL in analyst_df.columns and not analyst_df.empty:
            retailers = ", ".join(map(str, analyst_df[LIST_NAME_COL].unique()))
        else:
            retailers = ""
            
        summary_rows.append({
            "Analyst Name": analyst_name,
            "Tasks Assigned": count,
            "Percentage (%)": f"{pct}%",
            "Assigned Retailers": retailers
        })
        
    summary_rows.append({
        "Analyst Name": "Total",
        "Tasks Assigned": total_assigned,
        "Percentage (%)": "100.0%",
        "Assigned Retailers": ""
    })
    
    sheets_dict["Summary"] = pd.DataFrame(summary_rows)

    # 2. Create Analyst Sheets
    for analyst_name, analyst_df in assignments.items():
        logger.info(f"build_output_excel() | building sheet: {analyst_name} | {len(analyst_df)} records")

        output_df = pd.DataFrame(columns=LAUNCHER_OUTPUT_COLUMNS)

        for col in LAUNCHER_OUTPUT_COLUMNS:
            if col in ANALYST_FILL_COLUMNS:
                output_df[col] = ""
            elif col in analyst_df.columns:
                output_df[col] = analyst_df[col].values
            else:
                output_df[col] = ""

        sheets_dict[analyst_name] = output_df

    logger.info(f"build_output_excel() complete | {len(sheets_dict)} sheets")
    return sheets_dict