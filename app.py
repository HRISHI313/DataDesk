import streamlit as st
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
tab1, tab2, tab3 = st.tabs(["Analyser", "Comparator", "Launcher"])

# ─── ANALYSER TAB ───────────────────────────────────
with tab1:
    st.subheader("Analyser")
    
    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "xls"])
    
    if uploaded_file:
        with st.spinner("Reading file..."):
            df = read_excel(uploaded_file)
        
        try:
            validate_file_not_empty(df)
            validate_required_columns(df)
        except ValueError as e:
            st.error(str(e))
            st.stop()
        
        with st.spinner("Analysing..."):
            results = get_full_analysis(df)
        
        # ── Volume ──────────────────────────────
        col1, col2 = st.columns(2)
        col1.metric("Total Records", results["total_records"])
        col2.metric("Unique Retailers", results["unique_retailers_count"])
        
        st.divider()
        
        # ── Per Retailer ─────────────────────────
        st.subheader("Records Per Retailer")
        st.dataframe(results["per_retailer"], use_container_width=True)
        
        st.divider()
        
        # ── Construction Flag ────────────────────
        st.subheader("Construction Flag Breakdown")
        st.dataframe(results["construction_flag"], use_container_width=True)
        
        st.divider()
        
        # ── Polygon Status ───────────────────────
        st.subheader("Polygon Status Breakdown")
        st.dataframe(results["polygon_status"], use_container_width=True)
        
        st.divider()
        
        # ── Duplicate ALI ────────────────────────
        st.subheader("Duplicate ALI Analysis")
        col3, col4, col5 = st.columns(3)
        col3.metric("Total Records", results["duplicate_ali"]["total"])
        col4.metric("Unique ALIs", results["duplicate_ali"]["unique_ali"])
        col5.metric("Duplicate ALIs", results["duplicate_ali"]["duplicate_count"])
        
        if results["duplicate_ali"]["duplicate_count"] > 0:
            st.warning("Duplicate ALIs found")
            st.dataframe(results["duplicate_ali"]["duplicate_rows"])

# ─── COMPARATOR TAB ─────────────────────────────────
with tab2:
    st.subheader("Comparator")
    st.info("Coming soon")

# ─── LAUNCHER TAB ───────────────────────────────────
with tab3:
    st.subheader("Launcher")
    st.info("Coming soon")