"""Run benchmark queries N times each, persist timings to DW_DQ.perf_log.

Usage:
    python -m perf.benchmark --phase before --iterations 3
    python -m perf.benchmark --phase after  --iterations 3 --run-id same-run-id
"""
from __future__ import annotations

import argparse
import time
import uuid
from datetime import datetime

from ingestion.db import connect, db_names
from perf.queries import QUERIES


def _persist(rows: list[tuple]) -> None:
    dq = db_names()["dq"]
    sql = (
        f"INSERT INTO {dq}.perf_log "
        "(run_id, phase, query_name, iteration, duration_sec, rows_returned, started_at, notes) "
        "VALUES (?,?,?,?,?,?,?,?)"
    )
    with connect() as conn, conn.cursor() as cur:
        cur.executemany(sql, rows)


def run_one(name: str, sql_template: str, phase: str, iteration: int, tag: str) -> tuple[float, int]:
    sql = sql_template.format(tag=tag)
    started = datetime.utcnow().replace(microsecond=0)
    t0 = time.time()
    with connect() as conn, conn.cursor() as cur:
        cur.execute(sql)
        n = sum(1 for _ in cur.fetchall())
    elapsed = round(time.time() - t0, 3)
    print(f"  [{phase}] {name:30s} iter={iteration} {elapsed:>7.3f}s  rows={n}")
    return elapsed, n, started


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", choices=["before", "after"], required=True)
    ap.add_argument("--iterations", type=int, default=3)
    ap.add_argument("--run-id", default=f"perf-{uuid.uuid4().hex[:8]}")
    args = ap.parse_args()

    print(f"[perf] run_id={args.run_id}  phase={args.phase}  iterations={args.iterations}")
    rows_to_log: list[tuple] = []
    for name, sql in QUERIES.items():
        for i in range(1, args.iterations + 1):
            tag = f"{args.run_id}:{args.phase}:{name}:iter{i}"
            elapsed, n_rows, started = run_one(name, sql, args.phase, i, tag)
            rows_to_log.append(
                (args.run_id, args.phase, name, i, elapsed, n_rows, started, None)
            )
    _persist(rows_to_log)
    print(f"[perf] persisted {len(rows_to_log)} rows under run_id={args.run_id}")
    print(f"\nTo run the AFTER phase later:")
    print(f"  python -m perf.benchmark --phase after --run-id {args.run_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
