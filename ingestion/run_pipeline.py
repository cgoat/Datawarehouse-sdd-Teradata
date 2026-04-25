"""Orchestrates the full DW pipeline locally:
   load → dbt source tests → GE(bronze) → dbt silver → GE(silver) → dbt gold → GE(gold).

Airflow does the same steps as separate tasks; this module is for dev runs
against a real Teradata instance.
"""
from __future__ import annotations

import os
import subprocess
import sys
import uuid
from pathlib import Path

from .load_csv import load_all
from .run_log import Step

ROOT = Path(__file__).resolve().parent.parent
DBT_DIR = ROOT / "transform"


def _dbt(args: list[str], step_name: str, layer: str, batch_id: str) -> None:
    env = {**os.environ, "DBT_PROFILES_DIR": str(DBT_DIR), "DW_BATCH_ID": batch_id}
    with Step(batch_id=batch_id, layer=layer, step=step_name) as s:
        s.tool = "dbt"
        subprocess.run(["dbt", *args, "--project-dir", str(DBT_DIR)], check=True, env=env)


def _ge(suite: str, batch_id: str) -> None:
    with Step(batch_id=batch_id, layer="dq", step=f"ge_{suite}") as s:
        s.tool = "great_expectations"
        subprocess.run(
            [sys.executable, "-m", "dq.run_expectations",
             "--suite", suite, "--batch-id", batch_id],
            check=True, cwd=ROOT,
        )


def main() -> int:
    batch_id = os.getenv("DW_BATCH_ID") or f"run-{uuid.uuid4().hex[:8]}"
    data_dir = Path(os.getenv("DATA_DIR", ROOT / "data"))
    print(f"[pipeline] batch_id={batch_id} data_dir={data_dir}")

    counts = load_all(data_dir, batch_id)
    print(f"[pipeline] bronze loaded: {sum(counts.values()):,} rows across {len(counts)} tables")

    _dbt(["deps"], "dbt_deps", "bronze", batch_id)
    _dbt(["seed"], "dbt_seed", "silver", batch_id)
    _dbt(["test", "--select", "source:*"], "dbt_source_tests", "bronze", batch_id)
    _ge("bronze", batch_id)

    _dbt(["build", "--select", "silver"], "dbt_build_silver", "silver", batch_id)
    _ge("silver", batch_id)

    _dbt(["build", "--select", "gold"], "dbt_build_gold", "gold", batch_id)
    _ge("gold", batch_id)

    print(f"[pipeline] batch_id={batch_id} OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
