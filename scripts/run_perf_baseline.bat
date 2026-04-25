@echo off
REM Phase 3: capture baseline timings (3 iterations of 5 benchmark queries).
REM Pass --run-id <id> to chain a later --phase after run.
setlocal
cd /d %~dp0\..
python -m perf.benchmark --phase before --iterations 3 %*
