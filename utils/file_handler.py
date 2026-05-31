import pandas as pd
import logging
import io

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

def write_excel(df, filename):
    logger.info(f"write_excel() called | filename: {filename}")
    output = io.BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    logger.info(f"write_excel() complete | {len(df)} rows")
    return output


def write_multi_sheet_excel(sheets_dict, filename):
    logger.info(f"write_multi_sheet_excel() called | filename: {filename} | sheets: {list(sheets_dict.keys())}")
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sheet_name, df in sheets_dict.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            logger.info(f"Sheet written: {sheet_name} | {len(df)} rows")
    output.seek(0)
    logger.info(f"write_multi_sheet_excel() complete | {len(sheets_dict)} sheets")
    return output