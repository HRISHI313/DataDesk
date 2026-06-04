import streamlit as st
import pandas as pd
import logging
from utils.logger import setup_logger
from config import *
from utils.file_handler import read_excel
from utils.validators import validate_required_columns, validate_file_not_empty
from modules.analyser import get_full_analysis
from modules.comparator import get_comparison_summary
from modules.task_launcher import *
import base64
from pathlib import Path

# ─── LOGGING SETUP ──────────────────────────────────
logger = setup_logger()
logger.info("DataDesk started")

# ─── PAGE CONFIG ────────────────────────────────────
st.set_page_config(
    page_title = "DataDesk",
    page_icon  = "📍",
    layout     = "wide"
)

# ─── BASE PATH ───────────────────────────────────────
BASE_DIR = Path(__file__).parent
CSS_PATH  = BASE_DIR / "assets" / "style.css"
LOGO_PATH = BASE_DIR / "assets" / "logo.png"

# ─── LOAD CSS ────────────────────────────────────────
def load_css():
    with open(CSS_PATH, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# ─── HEADER ──────────────────────────────────────────
def get_logo_base64():
    with open(LOGO_PATH, "rb") as f:
        return base64.b64encode(f.read()).decode()

try:
    logo_b64  = get_logo_base64()
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" class="dd-logo"/>'
except:
    logo_html = ""

st.markdown(f"""
<div class="dd-header">
    <div class="dd-header-left">
        {logo_html}
        <div>
            <div class="dd-title">DataDesk</div>
            <div class="dd-subtitle">Built for analyse your data, compare your files and launch tasks in minutes.</div>
        </div>
    </div>
    <div class="dd-header-right">
        <div class="dd-version">v{APP_VERSION}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── TABS ───────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["Analyser", "Comparator", "Task Launcher"])

# ─── ANALYSER TAB ───────────────────────────────────
with tab1:
    st.subheader("Analyser")

    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "xls", "csv"])

    if uploaded_file:

        # ── File Info Bar ────────────────────────────
        with st.spinner("Reading file..."):
            start_time = pd.Timestamp.now()
            df         = read_excel(uploaded_file)
            elapsed    = round((pd.Timestamp.now() - start_time).total_seconds(), 2)

        try:
            validate_file_not_empty(df)
            validate_required_columns(df)
        except ValueError as e:
            st.error(str(e))
            st.stop()

        st.caption(f"📄 {uploaded_file.name}  |  {len(df)} rows  |  loaded in {elapsed}s")
        st.divider()

        # ── Run Analysis ─────────────────────────────
        with st.spinner("Analysing..."):
            results = get_full_analysis(df)

        # ── QC Error Check ───────────────────────────
        if results["qc_errors"]["total_errors"] > 0:
            st.warning(f"⚠️ {results['qc_errors']['total_errors']} QC Errors Found — records have Polygon Status but should not")

            if len(results["qc_errors"]["mall_tenant_errors"]) > 0:
                with st.expander(f"🔴 {len(results['qc_errors']['mall_tenant_errors'])} Mall Tenant records have Polygon Status — should never have one"):
                    st.dataframe(results["qc_errors"]["mall_tenant_errors"], use_container_width=True)

            if len(results["qc_errors"]["multi_level_errors"]) > 0:
                with st.expander(f"🔴 {len(results['qc_errors']['multi_level_errors'])} Multi Level records have Polygon Status — should never have one"):
                    st.dataframe(results["qc_errors"]["multi_level_errors"], use_container_width=True)

            if len(results["qc_errors"]["construction_errors"]) > 0:
                with st.expander(f"🔴 {len(results['qc_errors']['construction_errors'])} Construction records have Polygon Status — should never have one"):
                    st.dataframe(results["qc_errors"]["construction_errors"], use_container_width=True)

        # ── Polygon Coverage ─────────────────────────
        st.subheader("Polygon Coverage")

        marked_pct    = results["polygon_coverage"]["marked_pct"]
        pending_pct   = results["polygon_coverage"]["pending_pct"]
        marked_count  = results["polygon_coverage"]["marked_count"]
        pending_count = results["polygon_coverage"]["pending_count"]
        total         = results["polygon_coverage"]["total"]

        st.caption(f"Marked — {marked_count} of {total} records ({marked_pct}%)")
        st.progress(marked_pct / 100)

        st.caption(f"Pending — {pending_count} of {total} records ({pending_pct}%)")
        st.progress(pending_pct / 100)

        st.divider()

        with st.expander("📊 View Breakdown"):
            b1, b2, b3, b4, b5 = st.columns(5)
            b1.metric("Mall Tenant",     results["polygon_coverage"]["mall_tenant_count"])
            b2.metric("Multi Level",     results["polygon_coverage"]["multi_level_count"])
            b3.metric("Construction",    results["polygon_coverage"]["construction_count"])
            b4.metric("Polygon Done",    results["polygon_coverage"]["polygon_done_count"])
            b5.metric("Polygon Missing", results["polygon_coverage"]["polygon_missing_count"])

        st.divider()

        # ── Launch Task Button ───────────────────────
        if results["polygon_coverage"]["pending_count"] > 0:
            st.divider()
            st.caption(f"📋 {results['polygon_coverage']['pending_count']} pending records ready to launch")
            if st.button("🚀 Launch Task From Pending Records", key="launch_from_analyser"):
                st.session_state["launcher_df"]       = results["polygon_coverage"]["pending_rows"]
                st.session_state["launcher_from_analyser"] = True
                st.info("✅ Pending records transferred. Go to Launcher tab to continue.")
                logger.info(f"Pending records transferred to Launcher | {results['polygon_coverage']['pending_count']} records")

        st.divider()

        # ── Top Summary Cards — Row 1 ────────────────
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total Records",    results["total_records"])
        col2.metric("Unique Retailers", results["unique_retailers_count"])
        col3.metric("Verified QA",      results["polygon_pct"]["Verified QA"]["count"])
        col4.metric("Duplicate ALIs",   results["duplicate_ali"]["duplicate_count"])
        col5.metric("Unique ALIs",      results["duplicate_ali"]["unique_ali"])

        # ── Top Summary Cards — Row 2 ────────────────
        col6, col7, col8, col9, col10 = st.columns(5)
        col6.metric("Connected",  results["parent_ali"]["connected"]["count"])
        col7.metric("Unlinked",   results["parent_ali"]["unknown"]["count"])
        col8.metric("Marked",     results["polygon_coverage"]["marked_count"])
        col9.metric("Pending",    results["polygon_coverage"]["pending_count"])
        col10.metric("",          "")    # empty placeholder for alignment

        st.divider()

        st.divider()

        # ── Polygon Status ───────────────────────────
        st.subheader("Polygon Status")
        p1, p2 = st.columns(2)
        p1.metric("Verified QA",
                  results["polygon_pct"]["Verified QA"]["count"],
                  f'{results["polygon_pct"]["Verified QA"]["pct"]}%')
        p2.metric("Unverified",
                  results["polygon_pct"]["Unverified"]["count"],
                  f'{results["polygon_pct"]["Unverified"]["pct"]}%')

        st.divider()

        # ── Per Retailer Table ───────────────────────
        st.subheader("Records Per Retailer")
        st.dataframe(results["per_retailer"], use_container_width=True)

        st.divider()

        # ── Parent ALI Breakdown Table ───────────────
        st.subheader("Parent ALI")
        st.dataframe(
            results["parent_ali"]["per_retailer"],
            use_container_width=True
        )

        st.divider()

        # ── Duplicate ALI Expander ───────────────────
        if results["duplicate_ali"]["duplicate_count"] > 0:
            with st.expander(f"⚠️ {results['duplicate_ali']['duplicate_count']} Duplicate ALIs found — click to view"):
                st.dataframe(
                    results["duplicate_ali"]["duplicate_rows"],
                    use_container_width=True
                )
        else:
            st.success("✅ No duplicate ALIs found")

# ─── COMPARATOR TAB ─────────────────────────────────
with tab2:
    st.subheader("Comparator")

    # ── File Upload ──────────────────────────────────
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        file1 = st.file_uploader("Upload File 1", type=["xlsx", "xls", "csv"], key="comp_file1")
    with col_f2:
        file2 = st.file_uploader("Upload File 2", type=["xlsx", "xls", "csv"], key="comp_file2")

    # ── Comparison Type ──────────────────────────────
    comparison_type = st.selectbox(
        "Select Comparison Type",
        [COMPARISON_ALI, COMPARISON_ADDRESS, COMPARISON_MIGRATION]
    )

    # ── Run Button ───────────────────────────────────
    run = st.button("Run Comparison")

    if file1 and file2 and run:

        logger.info(f"Comparator started | type: {comparison_type}")

        with st.spinner("Reading files..."):
            df1 = read_excel(file1)
            df2 = read_excel(file2)

        logger.info(f"Files loaded | File1: {file1.name} {len(df1)} rows | File2: {file2.name} {len(df2)} rows")

        try:
            validate_file_not_empty(df1)
            validate_file_not_empty(df2)
        except ValueError as e:
            logger.error(f"Validation failed: {str(e)}")
            st.error(str(e))
            st.stop()

        st.caption(f"📄 {file1.name}  |  {len(df1)} rows")
        st.caption(f"📄 {file2.name}  |  {len(df2)} rows")
        st.divider()

        with st.spinner("Comparing..."):
            results = get_comparison_summary(df1, df2, comparison_type)

        logger.info(f"Comparison complete | type: {comparison_type}")

        # ── Type 1 and Type 2 Results ────────────────
        if comparison_type in [COMPARISON_ALI, COMPARISON_ADDRESS]:

            # summary cards
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("File 1 Total",  len(df1))
            c2.metric("File 2 Total",  len(df2))
            c3.metric("Matched",       len(results["matched"]))
            c4.metric("Unmatched",     len(results["unmatched"]))
            c5.metric("Conflicts",     len(results["conflicts"]))

            st.divider()

            # matched
            with st.expander(f"✅ Matched — {len(results['matched'])} records"):
                st.dataframe(results["matched"], use_container_width=True)

            # unmatched
            if results["unmatched_duplicate_count"] > 0:
                st.warning(f"⚠️ {results['unmatched_duplicate_count']} duplicate ALIs detected in unmatched records — review before acting")

            with st.expander(f"📋 Unmatched — {len(results['unmatched'])} records"):
                st.dataframe(results["unmatched"], use_container_width=True)

            # conflicts
            if len(results["conflicts"]) > 0:
                with st.expander(f"⚠️ Conflicts — {len(results['conflicts'])} records"):
                    st.dataframe(results["conflicts"], use_container_width=True)
            else:
                st.success("✅ No conflicts found")

        # ── Type 3 Migration Results ─────────────────
        elif comparison_type == COMPARISON_MIGRATION:

            logger.info(f"Migration results | ali_changed_polygon_lost: {len(results['ali_changed_polygon_lost'])} | ali_changed_never_marked: {len(results['ali_changed_never_marked'])} | clean: {len(results['clean'])}")

            # ── Summary Cards With Tooltips ──────────
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Only in Old",                len(results["only_old"]),
                      help="Addresses in old file not found in new file. May be address format changes during migration.")
            m2.metric("Only in New",                len(results["only_new"]),
                      help="Addresses in new file not found in old file. New locations or changed address format.")
            m3.metric("ALI Changed + Poly Lost",    len(results["ali_changed_polygon_lost"]),
                      help="Address matched, ALI got a new number, Polygon Status was lost. These need redrawing.")
            m4.metric("ALI Changed + Never Marked", len(results["ali_changed_never_marked"]),
                      help="Address matched, ALI changed, but was never marked before either. Track the new ALI.")
            m5.metric("Clean Migration",            len(results["clean"]),
                      help="Everything matched perfectly. No action needed.")

            st.divider()

            # ── Help Popover ─────────────────────────
            with st.popover("ℹ️ How to read these results"):
                st.markdown("""
                    **🔴 ALI Changed + Polygon Lost**
                    Address matched, ALI got a new number, Polygon Status was lost. These need redrawing.

                    ---

                    **🟡 ALI Changed + Never Marked**
                    Address matched, ALI changed, but was never marked before either. Track new ALI.

                    ---

                    **🟡 Polygon Lost Only**
                    Address matched, ALI intact, but Polygon Status was lost. Redrawing needed.

                    ---

                    **📁 Only in Old File**
                    Address not found in new file. May be address format change during migration.

                    ---

                    **📁 Only in New File**
                    Address not found in old file. New locations or changed address format.

                    ---

                    **✅ Clean Migration**
                    Everything matched perfectly. No action needed.
                """)

            # ── Expanders ────────────────────────────
            if len(results["ali_changed_polygon_lost"]) > 0:
                with st.expander(f"🔴 ALI Changed + Polygon Lost — {len(results['ali_changed_polygon_lost'])} records"):
                    st.dataframe(results["ali_changed_polygon_lost"], use_container_width=True)

            if len(results["ali_changed_never_marked"]) > 0:
                with st.expander(f"🟡 ALI Changed + Never Marked — {len(results['ali_changed_never_marked'])} records"):
                    st.dataframe(results["ali_changed_never_marked"], use_container_width=True)

            if len(results["polygon_lost_only"]) > 0:
                with st.expander(f"🟡 Polygon Lost Only — {len(results['polygon_lost_only'])} records"):
                    st.dataframe(results["polygon_lost_only"], use_container_width=True)

            with st.expander(f"📁 Only in Old File — {len(results['only_old'])} records"):
                st.dataframe(results["only_old"], use_container_width=True)

            with st.expander(f"📁 Only in New File — {len(results['only_new'])} records"):
                st.dataframe(results["only_new"], use_container_width=True)

            with st.expander(f"✅ Clean Migration — {len(results['clean'])} records"):
                st.dataframe(results["clean"], use_container_width=True)

            logger.info("Migration results displayed successfully")

# ─── LAUNCHER TAB ───────────────────────────────────
with tab3:
    st.subheader("Task Launcher")

    # ── File Source ──────────────────────────────────
    if st.session_state.get("launcher_from_analyser") and st.session_state.get("launcher_df") is not None:
        df_launcher = st.session_state["launcher_df"]

        st.success(f"📊 {len(df_launcher)} pending records loaded from Analyser")
        if st.button("🔄 Clear and Upload Different File", key="clear_launcher"):
            st.session_state["launcher_from_analyser"] = False
            st.session_state["launcher_df"]            = None
            st.rerun()
        st.divider()

    else:
        launcher_file = st.file_uploader("Upload Excel File", type=["xlsx", "xls", "csv"], key="launcher_file")

        if launcher_file:
            with st.spinner("Reading file..."):
                df_launcher = read_excel(launcher_file)

            try:
                validate_file_not_empty(df_launcher)
                validate_required_columns(df_launcher)
            except ValueError as e:
                logger.error(f"Launcher validation failed: {str(e)}")
                st.error(str(e))
                st.stop()

            st.caption(f"📄 {launcher_file.name}  |  {len(df_launcher)} rows")
            st.divider()

        else:
            df_launcher = None

    # ── Only proceed if df_launcher exists ───────────
    if df_launcher is not None:

        # ── Detect Mode ──────────────────────────────
        mode            = detect_retailer_mode(df_launcher)
        retailer_counts = get_retailer_counts(df_launcher)
        total_alis      = len(df_launcher)

        # ── Detect Mode ──────────────────────────────
        mode            = detect_retailer_mode(df_launcher)
        retailer_counts = get_retailer_counts(df_launcher)
        total_alis      = len(df_launcher)

        if mode == "single":
            st.info(f"📋 Single Retailer Mode — {list(retailer_counts.keys())[0]} | {total_alis} ALIs")
        else:
            st.info(f"📋 Multi Retailer Mode — {len(retailer_counts)} retailers | {total_alis} ALIs")

        st.divider()

        # ── Analyst Setup ────────────────────────────
        st.subheader("Analyst Setup")
        num_analysts = st.number_input("Number of Analysts", min_value=1, max_value=20, value=2, step=1)

        analyst_names = []
        name_cols     = st.columns(num_analysts)
        for i, col in enumerate(name_cols):
            name = col.text_input(f"Analyst {i+1} Name", value=f"Analyst {i+1}", key=f"analyst_name_{i}")
            analyst_names.append(name)

        target, remainder = calculate_target(total_alis, num_analysts)

        st.divider()

        # ─────────────────────────────────────────────
        # SINGLE RETAILER MODE
        # ─────────────────────────────────────────────
        if mode == "single":

            st.subheader("Distribution")

            t_cols = st.columns(num_analysts)
            for i, (col, name) in enumerate(zip(t_cols, analyst_names)):
                target_count = target + remainder if i == 0 else target
                col.metric(name, f"{target_count} ALIs")

            st.divider()

            task_name = st.text_input(
                "Task Name",
                placeholder = "e.g. Five Below June 2026",
                key         = "single_task_name"
            )

            if st.button("Generate Excel", key="single_generate"):
                with st.spinner("Building task list..."):
                    assignments = equal_split(df_launcher, analyst_names)
                    sheets_dict = build_output_excel(assignments)
                    from utils.file_handler import write_multi_sheet_excel
                    from datetime import datetime
                    clean_name = task_name.strip().replace(" ", "_") if task_name else "TaskList"
                    filename   = f"{clean_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                    output     = write_multi_sheet_excel(sheets_dict, filename)

                st.success("✅ Task list ready")
                st.download_button(
                    label     = "📥 Download Task List",
                    data      = output,
                    file_name = filename,
                    mime      = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                logger.info(f"Single mode Excel generated | {filename}")

        # ─────────────────────────────────────────────
        # MULTI RETAILER MODE
        # ─────────────────────────────────────────────
        else:

            # initialize session state
            if "retailer_assignments" not in st.session_state:
                st.session_state["retailer_assignments"] = {}
            if "split_counts" not in st.session_state:
                st.session_state["split_counts"] = {}
            if "confirm_generate" not in st.session_state:
                st.session_state["confirm_generate"] = False
            if "show_confirm" not in st.session_state:
                st.session_state["show_confirm"]     = False
            if "pending_assignments" not in st.session_state:
                st.session_state["pending_assignments"] = None

            # ── Balance Tracker (TOP) ─────────────────
            st.subheader("Balance Tracker")

            balance_cols = st.columns(num_analysts)
            for i, (col, name) in enumerate(zip(balance_cols, analyst_names)):

                assigned_count = 0
                for retailer, assignment in st.session_state["retailer_assignments"].items():
                    if assignment == name:
                        assigned_count += retailer_counts.get(retailer, 0)
                    elif assignment == "Split":
                        if retailer in st.session_state["split_counts"]:
                            assigned_count += st.session_state["split_counts"][retailer].get(name, 0)

                analyst_target = target + remainder if i == 0 else target
                remaining      = analyst_target - assigned_count
                pct            = assigned_count / analyst_target if analyst_target > 0 else 0

                if pct > 1.0:
                    bar_color = "🔴"
                    status    = f"Over by {assigned_count - analyst_target}"
                elif pct >= 0.9:
                    bar_color = "🟢"
                    status    = "On target ✅"
                elif pct >= 0.5:
                    bar_color = "🟡"
                    status    = f"{remaining} more needed"
                else:
                    bar_color = "🔵"
                    status    = f"{remaining} more needed"

                col.metric(
                    label = f"{bar_color} {name}",
                    value = f"{assigned_count} / {analyst_target}",
                    delta = status
                )
                col.progress(min(pct, 1.0))

            st.divider()

            # ── Bulk Assign ───────────────────────────
            st.subheader("Assign Retailers")

            bulk_col1, bulk_col2, bulk_col3 = st.columns([1, 2, 2])

            with bulk_col1:
                if st.button("Select All", key="select_all"):
                    for retailer in retailer_counts.keys():
                        if retailer not in st.session_state["retailer_assignments"]:
                            st.session_state[f"check_{retailer}"] = True

            with bulk_col2:
                bulk_analyst = st.selectbox(
                    "Assign selected to",
                    options = ["— Select —"] + analyst_names,
                    key     = "bulk_analyst"
                )

            with bulk_col3:
                if st.button("Assign Selected", key="bulk_assign"):
                    if bulk_analyst != "— Select —":
                        for retailer in retailer_counts.keys():
                            if st.session_state.get(f"check_{retailer}", False):
                                st.session_state["retailer_assignments"][retailer] = bulk_analyst
                                st.session_state[f"check_{retailer}"] = False
                        logger.info(f"Bulk assign to {bulk_analyst}")

            st.divider()

            # ── Unassigned Retailers ──────────────────
            unassigned_retailers = {
                r: c for r, c in retailer_counts.items()
                if st.session_state["retailer_assignments"].get(r) is None
            }

            if unassigned_retailers:
                st.markdown(f"**📋 Unassigned — {len(unassigned_retailers)} retailers**")
                for retailer, count in unassigned_retailers.items():
                    row_col1, row_col2, row_col3 = st.columns([1, 4, 3])

                    with row_col1:
                        st.session_state[f"check_{retailer}"] = st.checkbox(
                            "",
                            value = st.session_state.get(f"check_{retailer}", False),
                            key   = f"checkbox_{retailer}"
                        )

                    row_col2.write(f"**{retailer}** — {count} ALIs")

                    with row_col3:
                        quick_assign = st.selectbox(
                            "Quick assign",
                            options = ["— Select —"] + analyst_names + ["Split"],
                            key     = f"quick_{retailer}"
                        )
                        if quick_assign != "— Select —":
                            st.session_state["retailer_assignments"][retailer] = quick_assign

            st.divider()

            # ── Assigned Retailers ────────────────────
            assigned_retailers = {
                r: c for r, c in retailer_counts.items()
                if st.session_state["retailer_assignments"].get(r) is not None
            }

            if assigned_retailers:
                st.markdown(f"**✅ Assigned — {len(assigned_retailers)} retailers**")
                for retailer, count in assigned_retailers.items():
                    assignment = st.session_state["retailer_assignments"][retailer]
                    a_col1, a_col2, a_col3 = st.columns([4, 3, 2])
                    a_col1.write(f"**{retailer}** — {count} ALIs")
                    a_col2.write(f"→ {assignment}")
                    if a_col3.button("↩ Unassign", key=f"unassign_{retailer}"):
                        del st.session_state["retailer_assignments"][retailer]

            st.divider()

            # ── Split Section ─────────────────────────
            split_retailers = {
                r: c for r, c in retailer_counts.items()
                if st.session_state["retailer_assignments"].get(r) == "Split"
            }

            if split_retailers:
                st.subheader("Split Retailers")
                for retailer, count in split_retailers.items():
                    st.markdown(f"**{retailer}** — {count} ALIs")
                    split_cols  = st.columns(num_analysts)
                    split_input = {}

                    for i, (sc, name) in enumerate(zip(split_cols, analyst_names)):
                        already_assigned = sum(
                            retailer_counts.get(r, 0)
                            for r, a in st.session_state["retailer_assignments"].items()
                            if a == name and r != retailer
                        )
                        analyst_target   = target + remainder if i == 0 else target
                        remaining_needed = max(0, analyst_target - already_assigned)

                        val = sc.number_input(
                            f"{name} (needs {remaining_needed})",
                            min_value = 0,
                            max_value = count,
                            value     = min(remaining_needed, count),
                            key       = f"split_{retailer}_{name}"
                        )
                        split_input[name] = val

                    total_split = sum(split_input.values())
                    if total_split != count:
                        st.warning(f"⚠️ Split total {total_split} does not match {count}. Difference: {abs(count - total_split)}")
                    else:
                        st.success(f"✅ Split adds up — {total_split} ALIs")

                    st.session_state["split_counts"][retailer] = split_input
                st.divider()

            # ── Generate Excel ────────────────────────
            if st.button("Generate Excel", key="multi_generate"):
                st.session_state["confirm_generate"] = False
                st.session_state["show_confirm"]     = False

                final_assignments = {name: pd.DataFrame() for name in analyst_names}

                for retailer, assignment in st.session_state["retailer_assignments"].items():
                    retailer_df = df_launcher[df_launcher[LIST_NAME_COL] == retailer].copy()

                    if assignment == "Split":
                        if retailer in st.session_state["split_counts"]:
                            try:
                                split_result = random_split_retailer(
                                    df_launcher,
                                    retailer,
                                    st.session_state["split_counts"][retailer]
                                )
                                for name, split_df in split_result.items():
                                    final_assignments[name] = pd.concat(
                                        [final_assignments[name], split_df],
                                        ignore_index=True
                                    )
                            except ValueError as e:
                                st.error(str(e))
                                st.stop()

                    elif assignment in analyst_names:
                        final_assignments[assignment] = pd.concat(
                            [final_assignments[assignment], retailer_df],
                            ignore_index=True
                        )

                total_assigned   = sum(len(v) for v in final_assignments.values())
                unassigned_count = total_alis - total_assigned

                st.session_state["pending_assignments"] = final_assignments

                if unassigned_count > 0:
                    st.session_state["unassigned_count"] = unassigned_count
                    st.session_state["show_confirm"]     = True
                else:
                    st.session_state["confirm_generate"] = True

            # ── Confirmation Warning ──────────────────
            if st.session_state.get("show_confirm"):
                st.warning(f"⚠️ {st.session_state['unassigned_count']} ALIs are still unassigned. Do you still want to generate?")
                if st.button("Yes, Generate Anyway", key="confirm_anyway"):
                    st.session_state["confirm_generate"] = True
                    st.session_state["show_confirm"]     = False

            # ── Download ─────────────────────────────
            task_name = st.text_input(
                "Task Name",
                placeholder = "e.g. Five Below June 2026",
                key         = "multi_task_name"
            )

            if st.session_state.get("confirm_generate") and st.session_state["pending_assignments"] is not None:

                with st.spinner("Building task list..."):
                    sheets_dict = build_output_excel(st.session_state["pending_assignments"])
                    from utils.file_handler import write_multi_sheet_excel
                    from datetime import datetime
                    clean_name = task_name.strip().replace(" ", "_") if task_name else "TaskList"
                    filename   = f"{clean_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                    output     = write_multi_sheet_excel(sheets_dict, filename)

                st.success("✅ Task list ready")
                st.download_button(
                    label     = "📥 Download Task List",
                    data      = output,
                    file_name = filename,
                    mime      = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                st.session_state["confirm_generate"]    = False
                st.session_state["pending_assignments"] = None
                logger.info(f"Multi mode Excel generated | {filename}")






