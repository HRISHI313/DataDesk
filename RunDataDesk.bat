@echo off
title DataDesk
cd /d "%~dp0"
call venv\Scripts\activate
streamlit run app.py
pause