@echo off
REM Serves the PHP reliability dashboard at http://localhost:8080/index.php
REM (separate port if Airflow is running; change 8080 to 8090 below in that case)
setlocal
cd /d %~dp0\..\dashboard
php -S localhost:8090
