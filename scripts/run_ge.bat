@echo off
setlocal
cd /d %~dp0\..
python -m dq.run_expectations %*
