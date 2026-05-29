import streamlit as st
import pandas as pd
import logging
from utils.logger import setup_logger
from config import *
from utils.file_handler import read_excel
from utils.validators import validate_required_columns, validate_file_not_empty
from modules.analyser import get_full_analysis
from modules.comparator import get_comparison_summary

# ─── LOGGING SETUP ──────────────────────────────────
logger = setup_logger()
logger.info("DataDesk started")

# ─── PAGE CONFIG ────────────────────────────────────
st.set_page_config(
    page_title = "DataDesk",
    layout     = "wide"
)

# ─── HEADER ─────────────────────────────────────────
st.title("DataDesk")
st.caption("Internal Data Operations Platform")
st.divider()

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

        # ── Top Summary Cards ────────────────────────
        col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
        col1.metric("Total Records",         results["total_records"])
        col2.metric("Unique Retailers",      results["unique_retailers_count"])
        col3.metric("Verified QA",           results["polygon_pct"]["Verified QA"]["count"])
        col4.metric("Duplicate ALIs",        results["duplicate_ali"]["duplicate_count"])
        col5.metric("Unique ALIs",           results["duplicate_ali"]["unique_ali"])
        col6.metric("Connected to Property", results["parent_ali"]["connected"]["count"])
        col7.metric("Pending Property",      results["parent_ali"]["unknown"]["count"])

        st.divider()

        # ── Construction Flag ────────────────────────
        st.subheader("Construction Flag")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Construction",
                  results["construction_pct"]["Construction"]["count"],
                  f'{results["construction_pct"]["Construction"]["pct"]}%')
        c2.metric("Mall Tenant",
                  results["construction_pct"]["Mall Tenant"]["count"],
                  f'{results["construction_pct"]["Mall Tenant"]["pct"]}%')
        c3.metric("Multi Level",
                  results["construction_pct"]["Multi Level"]["count"],
                  f'{results["construction_pct"]["Multi Level"]["pct"]}%')
        c4.metric("Normal",
                  results["construction_pct"]["Normal"]["count"],
                  f'{results["construction_pct"]["Normal"]["pct"]}%')

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

            logger.info(f"Displaying results | matched: {len(results['matched'])} | only_file1: {len(results['only_file1'])} | only_file2: {len(results['only_file2'])} | conflicts: {len(results['conflicts'])}")

            # summary cards
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("File 1 Total",   len(df1))
            c2.metric("File 2 Total",   len(df2))
            c3.metric("Matched",        len(results["matched"]))
            c4.metric("Only in File 1", len(results["only_file1"]))
            c5.metric("Only in File 2", len(results["only_file2"]))

            st.divider()

            with st.expander(f"✅ Matched — {len(results['matched'])} records"):
                st.dataframe(results["matched"], use_container_width=True)

            with st.expander(f"📁 Only in File 1 — {len(results['only_file1'])} records"):
                st.dataframe(results["only_file1"], use_container_width=True)

            with st.expander(f"📁 Only in File 2 — {len(results['only_file2'])} records"):
                st.dataframe(results["only_file2"], use_container_width=True)

            if len(results["conflicts"]) > 0:
                logger.info(f"Conflicts found: {len(results['conflicts'])}")
                with st.expander(f"⚠️ Conflicts — {len(results['conflicts'])} records"):
                    st.dataframe(results["conflicts"], use_container_width=True)
            else:
                logger.info("No conflicts found")
                st.success("✅ No conflicts found")

        # ── Type 3 Migration Results ─────────────────
        elif comparison_type == COMPARISON_MIGRATION:

            logger.info(f"Migration results | ali_changed_polygon_lost: {len(results['ali_changed_polygon_lost'])} | ali_changed_never_marked: {len(results['ali_changed_never_marked'])} | clean: {len(results['clean'])}")

            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Only in Old",                len(results["only_old"]))
            m2.metric("Only in New",                len(results["only_new"]))
            m3.metric("ALI Changed + Poly Lost",    len(results["ali_changed_polygon_lost"]))
            m4.metric("ALI Changed + Never Marked", len(results["ali_changed_never_marked"]))
            m5.metric("Clean Migration",            len(results["clean"]))

            st.divider()

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
    st.subheader("Launcher")
    st.info("Coming soon")