import pandas as pd
import logging

logger = logging.getLogger("datadesk")

def read_excel(uploaded_file):
    logger.info(f"Reading Excel file: {uploaded_file.name}")
    
    xl = pd.ExcelFile(uploaded_file)
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