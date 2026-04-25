"""Daily DW pipeline. Must finish before 07:00 America/Chicago (CEO SLA).

Schedule: 03:00 local; ~4h budget before the 07:00 cutoff.

Task order:
  load_bronze → dbt_source_tests → ge_bronze → dbt_silver → ge_silver
"""
from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

PROJECT_ROOT = "/opt/project"
DBT_DIR = f"{PROJECT_ROOT}/transform"

default_args = {
    "owner": "reliability",
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
    "sla": timedelta(hours=4),
}


def _load_bronze(**context) -> None:
    import sys
    sys.path.insert(0, PROJECT_ROOT)
    from pathlib import Path
    from ingestion.load_csv import load_all

    batch_id = context["run_id"]
    counts = load_all(Path(f"{PROJECT_ROOT}/data"), batch_id)
    print(f"bronze loaded: {sum(counts.values()):,} rows across {len(counts)} tables")


with DAG(
    dag_id="dw_pipeline",
    description="CSV → Bronze → dbt tests → GE → Silver (dims, facts, anomalies) → GE",
    default_args=default_args,
    start_date=datetime(2026, 4, 1),
    schedule="0 3 * * *",
    catchup=False,
    tags=["dw", "teradata"],
) as dag:

    load_bronze = PythonOperator(
        task_id="load_bronze",
        python_callable=_load_bronze,
    )

    dbt_deps = BashOperator(
        task_id="dbt_deps",
        bash_command=f"cd {DBT_DIR} && DBT_PROFILES_DIR={DBT_DIR} dbt deps",
    )

    dbt_seed = BashOperator(
        task_id="dbt_seed",
        bash_command=f"cd {DBT_DIR} && DBT_PROFILES_DIR={DBT_DIR} dbt seed",
    )

    dbt_source_tests = BashOperator(
        task_id="dbt_source_tests",
        bash_command=(
            f"cd {DBT_DIR} && DBT_PROFILES_DIR={DBT_DIR} "
            "dbt test --select 'source:*'"
        ),
    )

    ge_bronze = BashOperator(
        task_id="ge_bronze",
        bash_command=(
            f"cd {PROJECT_ROOT} && "
            "python -m dq.run_expectations --suite bronze --batch-id {{ run_id }}"
        ),
    )

    dbt_silver = BashOperator(
        task_id="dbt_silver",
        env={"DW_BATCH_ID": "{{ run_id }}"},
        append_env=True,
        bash_command=(
            f"cd {DBT_DIR} && DBT_PROFILES_DIR={DBT_DIR} "
            "dbt build --select silver"
        ),
    )

    ge_silver = BashOperator(
        task_id="ge_silver",
        bash_command=(
            f"cd {PROJECT_ROOT} && "
            "python -m dq.run_expectations --suite silver --batch-id {{ run_id }}"
        ),
    )

    dbt_gold = BashOperator(
        task_id="dbt_gold",
        env={"DW_BATCH_ID": "{{ run_id }}"},
        append_env=True,
        bash_command=(
            f"cd {DBT_DIR} && DBT_PROFILES_DIR={DBT_DIR} "
            "dbt build --select gold"
        ),
    )

    ge_gold = BashOperator(
        task_id="ge_gold",
        bash_command=(
            f"cd {PROJECT_ROOT} && "
            "python -m dq.run_expectations --suite gold --batch-id {{ run_id }}"
        ),
    )

    (load_bronze >> dbt_deps >> dbt_seed >> dbt_source_tests >> ge_bronze
     >> dbt_silver >> ge_silver >> dbt_gold >> ge_gold)
