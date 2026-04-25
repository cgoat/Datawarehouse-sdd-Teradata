@echo off
REM Brings Airflow up via Docker Compose. UI: http://localhost:8080  (admin/admin)
setlocal
cd /d %~dp0\..
docker compose -f airflow\docker-compose.yml --env-file .env up -d --build
