@echo off
REM Phase 3: capture post-tuning timings; --run-id must match the baseline run.
setlocal
cd /d %~dp0\..
python -m perf.benchmark --phase after --iterations 3 %*
