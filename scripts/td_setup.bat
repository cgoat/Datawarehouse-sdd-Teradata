@echo off
REM Runs all DDL scripts in teradata/ddl/ against the configured Teradata host.
REM Idempotent — already-exists errors are treated as a pass.
setlocal
cd /d %~dp0\..
python -m ingestion.td_setup
