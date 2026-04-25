@echo off
REM Phase 3: apply tunings (COLLECT STATISTICS + PPI on fact_sales).
setlocal
cd /d %~dp0\..
python -m perf.tune %*
