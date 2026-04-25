@echo off
REM Full Phase 0 pipeline: bronze load -> dbt source tests -> GE.
setlocal
cd /d %~dp0\..
python -m ingestion.run_pipeline
