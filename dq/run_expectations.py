"""Execute GE expectations against Teradata and persist results to DW_DQ.dq_result.

Uses GE's PandasDataset (pre-v1.0 API) — pulls a sample per table, validates,
writes results. Same output shape feeds both Bronze and Silver suites.

Usage:
    python -m dq.run_expectations                    # default: bronze
    python -m dq.run_expectations --suite silver
"""
from __future__ import annotations

import argparse
import os
import uuid
from datetime import datetime

import great_expectations as ge
import pandas as pd

from ingestion.db import connect, db_names
from dq.expectations.bronze_suite import bronze_expectations
from dq.expectations.silver_suite import silver_expectations
from dq.expectations.gold_suite import gold_expectations

SAMPLE_ROWS = int(os.getenv("GE_SAMPLE_ROWS", "50000"))

SUITES = {
    "bronze": (bronze_expectations, "bronze"),
    "silver": (silver_expectations, "silver"),
    "gold":   (gold_expectations,   "gold"),
}


def _load_sample(database: str, table: str, columns: list[str]) -> pd.DataFrame:
    col_list = ",".join(columns)
    sql = f"SELECT TOP {SAMPLE_ROWS} {col_list} FROM {database}.{table}"
    with connect() as conn:
        return pd.read_sql(sql, conn)


def _persist(batch_id: str, suite: str, table: str, results: list[dict]) -> None:
    dq = db_names()["dq"]
    run_at = datetime.utcnow().replace(microsecond=0)
    rows = []
    for r in results:
        expectation = r.get("expectation_config", {}).get("expectation_type", "?")
        observed = str(r.get("result", {}).get("observed_value", ""))[:3900]
        rows.append((batch_id, suite, table, expectation,
                     1 if r.get("success") else 0, observed, run_at))
    with connect() as conn, conn.cursor() as cur:
        cur.executemany(
            f"INSERT INTO {dq}.dq_result "
            "(batch_id, suite, table_name, expectation, success, observed_value, run_at) "
            "VALUES (?,?,?,?,?,?,?)",
            rows,
        )


def run_suite(suite_name: str, batch_id: str) -> int:
    if suite_name not in SUITES:
        raise ValueError(f"Unknown suite: {suite_name}. Choose from {list(SUITES)}")
    loader, persist_label = SUITES[suite_name]
    database = db_names()[suite_name]  # DW_BRONZE or DW_SILVER

    suites = loader()
    failures = 0
    for table, expectations in suites.items():
        columns = sorted({e["kwargs"]["column"] for e in expectations if "column" in e["kwargs"]})
        df = _load_sample(database, table, columns)
        dataset = ge.from_pandas(df)
        results = []
        for exp in expectations:
            fn = getattr(dataset, exp["expectation_type"])
            r = fn(**exp["kwargs"])
            results.append(r.to_json_dict() if hasattr(r, "to_json_dict") else dict(r))
        _persist(batch_id, persist_label, table, results)
        n_fail = sum(1 for r in results if not r.get("success"))
        if n_fail:
            failures += n_fail
            print(f"[ge:{suite_name}] {table}: {n_fail} failed of {len(results)}")
        else:
            print(f"[ge:{suite_name}] {table}: all {len(results)} passed")
    return failures


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch-id", default=f"ge-{uuid.uuid4().hex[:8]}")
    ap.add_argument("--suite", choices=list(SUITES), default="bronze")
    args = ap.parse_args()

    failures = run_suite(args.suite, args.batch_id)
    if failures:
        print(f"[ge] {failures} expectation failures for batch_id={args.batch_id}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
