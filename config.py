# APP INFO
APP_NAME           = "DataDesk"
APP_VERSION        = "1.0"
GITHUB_VERSION_URL = ""

# PATH
TEMP_PATH          = "data/temp/"
OUTPUT_PATH        = "output/"

# COLUMN NAMES
CATEGORY_COL           = "Category"
LIST_ID_COL            = "List ID"
LIST_NAME_COL          = "List Name"
ALI_COL                = "ALI"
POLYGON_STATUS_COL     = "Polygon Status"
STORE_NAME_COL         = "Store Name"
ADDRESS_COL            = "Address"
CITY_COL               = "City"
STATE_COL              = "State"
ZIP_COL                = "ZIP"
GEO_ACCURACY_COL       = "Geo Accuracy"
SQFT_COL               = "SQFT"
MANUAL_SQFT_COL        = "Manual SQFT"
SC_COL                 = "SC"
USER_COL               = "User"
TYPE_COL               = "Type"
DATE_EFFECTIVE_COL     = "Date Effective"
LATITUDE_COL           = "Latitude"
LONGITUDE_COL          = "Longitude"
PARENT_ALI_COL         = "Parent ALI"
PARENT_STORE_NAME_COL  = "Parent Store Name"
PARENT_LIST_NAME_COL   = "Parent List Name"
HIDE_TRAFFIC_COL       = "HideTraffic"
HIDE_FROM_APP_COL      = "HideFromApp"
LAST_UPDATED_COL       = "LastUpdated"
HIDE_TRAFFIC_FOR_COL   = "hideTrafficFor"
CONSTRUCTION_FLAG_COL  = "constructionFlag"

# TAG VALUES — keep original casing as these are data values not column names
CONSTRUCTION   = "Construction"
MALL_TENANT    = "Mall Tenant"
MULTI_LEVEL    = "Multi-Level"
VERIFIED_QA    = "VerifiedQA"
VERIFIED_ADMIN = "VerifiedAdmin"
NORMAL         = "Normal"

# GEO ACCURACY — values that mean an analyst has manually pinned the exact
GEO_ACCURACY_RETAILSTAT_VERIFIED = "RETAILSTAT VERIFIED: ROOFTOP"
GEO_ACCURACY_AGGDATA_VERIFIED    = "AGGDATA_VERIFIED: ROOFTOP"
GEO_ACCURACY_VERIFIED_VALUES     = [
    GEO_ACCURACY_RETAILSTAT_VERIFIED,
    GEO_ACCURACY_AGGDATA_VERIFIED,
]

# Comparison Types
COMPARISON_ALI       = "ALI"
COMPARISON_ADDRESS   = "Address"
COMPARISON_MIGRATION = "Migration"

# Task Launcher
LAUNCHER_OUTPUT_COLUMNS = [
    "Date",
    CATEGORY_COL,
    LIST_ID_COL,
    LIST_NAME_COL,
    ALI_COL,
    POLYGON_STATUS_COL,
    STORE_NAME_COL,
    ADDRESS_COL,
    CITY_COL,
    STATE_COL,
    ZIP_COL,
    "Source-1",
    "Source-2",
    "Remark"
]