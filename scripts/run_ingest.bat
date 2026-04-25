@echo off
REM Load all .dat files into Bronze. Single-table mode: pass --table store_sales.
setlocal
cd /d %~dp0\..
python -m ingestion.load_csv %*
