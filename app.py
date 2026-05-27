import streamlit as st
import pandas as pd
import logging
from utils.logger import setup_logger
from utils.file_handler import read_excel
from utils.validators import validate_required_columns, validate_file_not_empty
from modules.analyser import get_full_analysis

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

    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "xls"])

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
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total Records",    results["total_records"])
        col2.metric("Unique Retailers", results["unique_retailers_count"])
        col3.metric("Verified QA",      results["polygon_pct"]["Verified QA"]["count"])
        col4.metric("Duplicate ALIs",   results["duplicate_ali"]["duplicate_count"])
        col5.metric("Unique ALIs",      results["duplicate_ali"]["unique_ali"])

        st.divider()

        # ── Construction Flag Percentages ────────────
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

        # ── Polygon Status Percentages ───────────────
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

        # ── Construction Flag Breakdown Table ────────
        st.subheader("Construction Flag Breakdown")
        st.dataframe(results["construction_flag"], use_container_width=True)

        st.divider()

        # ── Polygon Status Breakdown Table ───────────
        st.subheader("Polygon Status Breakdown")
        st.dataframe(results["polygon_status"], use_container_width=True)

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

        # ── Parent ALI ───────────────────────────────
        st.subheader("Parent ALI")

        pa1, pa2 = st.columns(2)
        pa1.metric("Connected to Property",
                results["parent_ali"]["connected"]["count"],
                f'{results["parent_ali"]["connected"]["pct"]}%')
        pa2.metric("Unknown / Not Assigned",
                results["parent_ali"]["unknown"]["count"],
                f'{results["parent_ali"]["unknown"]["pct"]}%')

        st.dataframe(
            results["parent_ali"]["per_retailer"],
            use_container_width=True
        )

# ─── COMPARATOR TAB ─────────────────────────────────
with tab2:
    st.subheader("Comparator")
    st.info("Coming soon")

# ─── LAUNCHER TAB ───────────────────────────────────
with tab3:
    st.subheader("Launcher")
    st.info("Coming soon")