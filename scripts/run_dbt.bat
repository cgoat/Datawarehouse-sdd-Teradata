@echo off
setlocal
cd /d %~dp0\..\transform
set DBT_PROFILES_DIR=%cd%
dbt %*
