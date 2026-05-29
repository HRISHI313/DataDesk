import pandas as pd
import logging

logger = logging.getLogger("datadesk")


def read_excel(uploaded_file):
    
    if hasattr(uploaded_file, "name"):
        filename = uploaded_file.name
    else:
        filename = str(uploaded_file)

    logger.info(f"Reading file: {filename}")

    # ── CSV ─────────────────────────────────────────
    if filename.endswith(".csv"):
        logger.info("CSV detected — reading directly")
        df = pd.read_csv(uploaded_file)
        logger.info(f"CSV read complete | {len(df)} rows")
        return df

    # ── Excel ────────────────────────────────────────
    xl          = pd.ExcelFile(uploaded_file)
    sheet_names = xl.sheet_names
    logger.info(f"Sheets found: {sheet_names}")

    all_sheets = []
    for sheet in sheet_names:
        df = pd.read_excel(xl, sheet_name=sheet)
        all_sheets.append(df)
        logger.info(f"Sheet appended: {sheet} | {len(df)} rows")

    combined_df = pd.concat(all_sheets, ignore_index=True)
    logger.info(f"All sheets combined | total {len(combined_df)} rows")
    return combined_df