import streamlit as st
import logging
from utils.logger import setup_logger
from utils.file_handler import read_excel
from utils.validators import validate_required_columns, validate_file_not_empty

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
        
        st.success(f"File loaded — {len(df)} rows")
        st.dataframe(df)

# ─── COMPARATOR TAB ─────────────────────────────────
with tab2:
    st.subheader("Comparator")
    st.info("Coming soon")

# ─── LAUNCHER TAB ───────────────────────────────────
with tab3:
    st.subheader("Launcher")
    st.info("Coming soon")