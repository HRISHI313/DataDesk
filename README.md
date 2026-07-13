# DataDesk V2

Internal data operations tool for the RetailStat/Catalyst Partner operations
team. Covers two tools: **Analyser** (data quality checks on a task list)
and **Task Launcher** (splitting/assigning ALI records to field analysts).

V2 replaces the original Streamlit app (V1, now fully retired and removed)
with a FastAPI backend + React frontend, to fix the performance problem
V1 had with large files: Streamlit re-runs the entire script on every
click, which made big files and multi-retailer task launches slow. V2
only hits the backend on upload and on the final "Generate", and does all
click-heavy interaction (assigning retailers, balance tracking, splitting)
in the browser.

---

## Architecture

```
Browser  <---->  FastAPI (main.py, one process, one port)
                    |
                    +-- serves the built React app (frontend/dist)
                    +-- /api/analyser/*        (routers/analyser.py)
                    +-- /api/task-launcher/*   (routers/task_launcher.py)
                    |
                    +-- calls into modules/analyser.py,
                        modules/task_launcher.py, config.py, utils/
                        (the actual business logic - unchanged from V1,
                        just wrapped in HTTP endpoints now)
```

Everything runs as **one process on one port (8000)**. No database - an
uploaded file is parsed into a pandas DataFrame and held in a simple
in-memory cache (`utils/upload_cache.py`), keyed by a generated
`upload_id`. This is intentional: DataDesk runs locally, one instance per
machine, zero budget, sensitive data that must never leave the local
machine. Restarting the server clears the cache; users just re-upload.

---

## Folder structure

```
DataDesk/
├── main.py                 FastAPI entrypoint - CORS, routers, serves frontend/dist
├── config.py                Shared constants: column names, tag values, Geo Accuracy rules
├── modules/
│   ├── analyser.py           Analyser business logic (QC checks, Marked/Pending, etc.)
│   └── task_launcher.py      Task Launcher business logic (mode detection, splitting, Excel output)
├── routers/
│   ├── analyser.py           Analyser API endpoints
│   └── task_launcher.py      Task Launcher API endpoints
├── utils/
│   ├── file_handler.py        Excel/CSV reading, multi-sheet Excel writing
│   ├── validators.py          File/column validation
│   ├── serializers.py         Converts DataFrames/numpy/NaN into JSON-safe values for API responses
│   └── upload_cache.py        In-memory DataFrame cache keyed by upload_id
├── frontend/
│   ├── src/
│   │   ├── components/Analyser/        Analyser UI
│   │   ├── components/TaskLauncher/    Task Launcher UI
│   │   └── api/                        fetch() clients calling the backend
│   └── dist/                 Built static files (created by `npm run build`) - this is what main.py serves
├── RunDataDeskV2.bat         One-click launcher (double-click to run)
├── requirements.txt
└── venv/
```

---

## Running it

### Normal use (once built)

```
Double-click RunDataDeskV2.bat
```

This activates the Python virtual environment, starts the server, and
opens `http://localhost:8000` in your browser automatically. This is the
only thing needed day-to-day - no separate frontend server, no Node.js
required at this point.

**Requirement:** `frontend/dist/` must already exist (see "Building the
frontend" below). The `.bat` file does not build the frontend for you.

### Developing

Two things need to run in two terminals while actively changing code:

**Backend** (auto-reloads on save):
```powershell
uvicorn main:app --reload --port 8000
```

**Frontend** (live-reloads in the browser on save):
```powershell
cd frontend
npm run dev
```
This starts a dev server on `http://localhost:5173` - use this URL while
developing, not 8000, since 5173 has live-reload and 8000 only serves
whatever was last built.

### Building the frontend

Whenever frontend code changes and you want to actually run/ship it:
```powershell
cd frontend
npm install      # only needed the first time, or after pulling dependency changes
npm run build
```
This produces `frontend/dist/` - plain static HTML/CSS/JS that `main.py`
serves directly. **Teammates never need Node.js installed** - only you,
the developer, need it to run `npm run build`. Once built, everyone else
just needs Python and `RunDataDeskV2.bat`.

---

## Business logic reference

### Marked vs Pending (Analyser)

A record counts as **Marked** if ANY of the following is true:
- Polygon Status is `VerifiedQA` or `VerifiedAdmin`, OR
- constructionFlag is `Mall Tenant` or `Multi-Level`, OR
- constructionFlag is `Normal`, Polygon Status is still `None`/`Draft`,
  AND Geo Accuracy is already a verified-rooftop value (see below) -
  meaning an analyst has manually pinned the exact location via the
  geofencer, even though Polygon Status hasn't caught up yet.

Everything else counts as **Pending**, EXCEPT: a `Construction`-flagged
record always stays Pending regardless of Geo Accuracy - a site still
under construction shouldn't have a finished rooftop pin, so if it does,
that's a QC error, not a completed record.

These three conditions are combined into a single boolean mask (not
summed as separate counts) specifically to avoid double-counting a record
that matches more than one condition at once (e.g. a QC-error row like
Multi-Level with a Polygon Status set).

### Verified-rooftop Geo Accuracy values

```python
GEO_ACCURACY_RETAILSTAT_VERIFIED = "RETAILSTAT VERIFIED: ROOFTOP"
GEO_ACCURACY_AGGDATA_VERIFIED    = "AGGDATA_VERIFIED: ROOFTOP"
```
These are computer-generated values set automatically when an analyst
manually pins a location's exact rooftop position using the geofencer -
distinct from geocoded/approximate values like `"STREET ADDRESS: ROOFTOP"`
or `"PREMISE: ROOFTOP"`, which come from address-based geocoding, not
manual verification.

### QC error types

- **Mall Tenant with a Polygon Status set** - should never have one
- **Multi-Level with a Polygon Status set** - should never have one
- **Construction record that looks already completed** - has a Polygon
  Status set, OR Geo Accuracy already shows a verified-rooftop pin (the
  contradiction: a site still under construction shouldn't be pinned yet)

### Launch Task (Analyser -> Task Launcher hand-off)

Filters the analysed file down to records that still need work:
```
Include a record if Geo Accuracy is NOT one of the verified-rooftop values
(regardless of constructionFlag or Polygon Status)
```
This is deliberately broader than "Pending" above - even an already-Marked
Mall Tenant/Multi-Level record still needs launching if nobody has
actually pinned its rooftop location yet.

The user can preview per-retailer "needs work" counts before launching,
and select a subset of retailers to launch rather than all of them. The
original analysed file stays cached (not consumed by a launch), so the
same analysis can be launched again later for different retailers without
re-uploading. The cache only clears when the server restarts.

---

## API reference

All endpoints are prefixed `/api/analyser` or `/api/task-launcher`.

**Analyser**
| Endpoint | Method | Purpose |
|---|---|---|
| `/upload` | POST | Upload a file, run full analysis. Returns `needs_mapping` if columns don't match, otherwise the full results + an `upload_id` for later use. |
| `/upload-with-mapping` | POST | Same as above, with a column rename applied first. |
| `/launch-task-preview` | POST | Per-retailer "needs work" counts, for the launch checklist. |
| `/launch-task` | POST | Filters to records needing work (optionally limited to selected retailers) and hands off in Task Launcher's format. |

**Task Launcher**
| Endpoint | Method | Purpose |
|---|---|---|
| `/upload` | POST | Upload a file, detect single/multi retailer mode, cache the DataFrame. |
| `/upload-with-mapping` | POST | Same, with column mapping applied first. |
| `/target` | GET | Calculates the equal-split target + remainder for a given analyst count. |
| `/single/generate` | POST | Generates the output Excel for single-retailer equal-split mode. |
| `/multi/generate` | POST | Generates the output Excel for multi-retailer mode (including Split assignments). |
| `/{upload_id}` | DELETE | Frees a cached upload once done with it. |

---

## Known constraints (by design, not oversights)

- **No database** - everything is file-upload + in-memory cache. Sensitive
  data never needs to leave the local machine.
- **Single-user per machine** - the in-memory cache isn't shared across
  machines or persisted to disk. Each teammate runs their own local copy.
- **Comparator tab does not exist in V2** - it existed in V1 (Streamlit)
  but was never rebuilt here; deliberately dropped as out of scope.
