# DataDesk
**Internal Data Operations Platform**
Built for the RetailStat / Catalyst Partner operations team.

---

## What Is This
DataDesk is an internal tool that helps the operations team analyse POI data files, compare datasets and distribute field tasks across analysts — all from a simple browser-based interface. No Python knowledge required to use it.

---

## Features
- **Analyser** — upload a POI Excel file and get instant breakdown of polygon coverage, construction flags, polygon status, parent ALI connections and duplicate ALI detection
- **Comparator** — compare two files by ALI or Address, detect matched, unmatched and conflicting records, and run migration/prior work checks
- **Launcher** — distribute POI tasks across analysts with live balance tracking, bulk assignment and smart split for multi-retailer files

---

## Project Structure
DataDesk/
├── app.py
├── config.py
├── version.txt
├── requirements.txt
├── README.md
├── .gitignore
├── .streamlit/
│   └── config.toml
├── modules/
│   ├── comparator.py
│   ├── analyser.py
│   └── task_launcher.py
├── utils/
│   ├── file_handler.py
│   ├── validators.py
│   ├── version_checker.py
│   └── logger.py
├── tests/
│   ├── sample_data/
│   └── notebooks/
├── logs/
├── output/
├── assets/
│   ├── logo.png
│   └── styles.css
└── data/temp/

---

## Requirements
- Python 3.10+
- Install dependencies: pip install -r requirements.txt

---

## How To Run
streamlit run app.py

Browser opens automatically at localhost:8501

---

## Required Columns
Every Excel file uploaded must contain these columns:

| Column | Description |
|---|---|
| ALI | Unique location identifier |
| List Name | Retailer name |
| List ID | Retailer ID |
| Store Name | Store name |
| Address | Street address |
| City | City |
| State | State |
| ZIP | ZIP code |
| constructionFlag | Location type flag |
| Polygon Status | Verification status |
| Latitude | Latitude coordinate |
| Longitude | Longitude coordinate |

---

## Tag Values
Values used internally for record classification:

| Tag | Source | Meaning |
|---|---|---|
| Construction | constructionFlag | Blocked, cannot be drawn |
| Mall Tenant | constructionFlag | Inside a mall, no polygon needed |
| Multi Level | constructionFlag | Upper floor, no polygon needed |
| Verified QA | Polygon Status | Already verified and drawn |
| Normal | Internal label | Standard field work required |

---

## Polygon Coverage Logic
| Record Type | Marked Or Pending |
|---|---|
| Mall Tenant | Marked ✅ |
| Multi Level | Marked ✅ |
| Normal + Polygon Status filled | Marked ✅ |
| Construction | Pending ❌ |
| Normal + Polygon Status empty | Pending ❌ |

---

## QC Error Rules
| Rule | Error Condition |
|---|---|
| Mall Tenant | Should NEVER have Polygon Status |
| Multi Level | Should NEVER have Polygon Status |
| Construction | Should NEVER have Polygon Status |

---

## Task Launcher Output Columns
App fills these from source file:
- Category, List ID, List Name, ALI, Store Name, Address, City, State, ZIP

Analyst fills these manually after field work:
- Date, Polygon Status, Source-1, Source-2, Remark

---

## Logs
- Saved in logs/ folder as .txt files
- One file per session with timestamp
- Format: datadesk_YYYYMMDD_HHMMSS.txt
- Never pushed to GitHub

---

## Version
Current version: 1.0

---

## Project Rules
1. Never change code that affects another tab's output or logic unless explicitly discussed
2. config.py is frozen — no changes without assessing impact across all modules first
3. All manipulation happens in modules/ — app.py handles UI only
4. Test in Jupyter notebooks before moving logic to production files

---

## Version 2 Backlog
- User Workload Summary in Analyser
- Date Effective Analysis in Analyser
- Drawing Progress per Retailer
- Carry forward file from Analyser to Launcher via session state
- Analyst name input per sheet in Launcher
- Auto suggest distribution in Launcher
- Fuzzy address matching in Comparator
- Summary sheet in Launcher output Excel
- Sidebar with help and settings
- PyInstaller EXE build
- GitHub/OneDrive version checker and distribution