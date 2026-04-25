"""Load TPC-DS .dat files into Bronze.

Pipe-delimited, no header, no trailing pipe (dbgen -terminate n).
Empty fields become NULL. Writes row counts to DW_DQ.run_log.

Loader picks one of two paths per file by size:
  >= FASTLOAD_MIN_BYTES  -> teradatasql FastLoad-over-JDBC ({fn teradata_try_fastload})
  smaller                 -> standard executemany
The threshold is a tradeoff: FastLoad has per-load setup cost; for tiny
lookup tables (call_center=12, store=12, ship_mode=20) it's pure overhead.
"""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

import pandas as pd

from .db import connect, db_names
from .run_log import Step
from .schemas import TABLES, columns_for

BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10000"))
FASTLOAD_MIN_BYTES = int(os.getenv("FASTLOAD_MIN_BYTES", "1000000"))  # 1 MB


def _placeholders(n: int) -> str:
    return ",".join(["?"] * n)


def pick_tool(path: Path) -> str:
    """Return 'fastload' for files >= FASTLOAD_MIN_BYTES, else 'executemany'.
    Bronze tables are always TRUNCATEd before load, so FastLoad eligibility
    (empty target) holds for both paths."""
    return "fastload" if path.stat().st_size >= FASTLOAD_MIN_BYTES else "executemany"


def truncate(table: str) -> None:
    bronze = db_names()["bronze"]
    with connect() as conn, conn.cursor() as cur:
        cur.execute(f"DELETE FROM {bronze}.{table} ALL")


def load_file(path: Path, table: str, batch_id: str) -> tuple[int, str]:
    """Load a .dat file into the given Bronze table. Returns (rows_inserted, tool_used).

    FastLoad path: every executemany call with the {fn teradata_try_fastload}
    escape opens its own FastLoad session and commits at end. So we MUST send
    all rows in a single executemany — chunking would commit chunk 1 then fail
    chunk 2 with "table must be empty".

    Executemany path: standard chunked streaming, low memory.
    """
    if table not in TABLES:
        raise ValueError(f"Unknown table: {table}")
    cols = columns_for(table)
    meta_cols = ["_ingested_at", "_source_file", "_batch_id"]
    all_cols = cols + meta_cols
    bronze = db_names()["bronze"]
    tool = pick_tool(path)

    base_insert = (
        f"INSERT INTO {bronze}.{table} ({','.join(all_cols)}) "
        f"VALUES ({_placeholders(len(all_cols))})"
    )
    insert_sql = (
        "{fn teradata_try_fastload}" + base_insert if tool == "fastload" else base_insert
    )

    ingested_at = datetime.utcnow().replace(microsecond=0)
    source_file = path.name

    def _materialize_chunk(chunk: pd.DataFrame) -> list[tuple]:
        chunk = chunk.where(pd.notna(chunk), None)
        return [
            tuple(row) + (ingested_at, source_file, batch_id)
            for row in chunk.itertuples(index=False, name=None)
        ]

    total = 0
    with connect() as conn, conn.cursor() as cur:
        if tool == "fastload":
            # One executemany, one FastLoad session. Materialize the whole file.
            # SF1's largest is store_sales ~2.88M rows; ~700 MB peak Python memory.
            df = pd.read_csv(
                path, sep="|", header=None, names=cols, dtype=str,
                keep_default_na=False, na_values=[""], engine="c",
            )
            rows = _materialize_chunk(df)
            cur.executemany(insert_sql, rows)
            total = len(rows)
        else:
            for chunk in pd.read_csv(
                path, sep="|", header=None, names=cols, dtype=str,
                keep_default_na=False, na_values=[""],
                chunksize=BATCH_SIZE, engine="c",
            ):
                rows = _materialize_chunk(chunk)
                cur.executemany(insert_sql, rows)
                total += len(rows)
    return total, tool


def load_all(
    data_dir: Path,
    batch_id: str,
    include: set[str] | None = None,
    exclude: set[str] | None = None,
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for table in TABLES:
        if include and table not in include:
            continue
        if exclude and table in exclude:
            print(f"  skip {table}")
            continue
        path = data_dir / f"{table}.dat"
        if not path.exists():
            continue
        with Step(batch_id=batch_id, layer="bronze", step=f"load_{table}") as s:
            truncate(table)
            n, tool = load_file(path, table, batch_id)
            s.record(rows_in=n, rows_out=n, tool=tool)
            counts[table] = n
            print(f"  {table:30s} {n:>10,} rows  via {tool}", flush=True)
    return counts


if __name__ == "__main__":
    import argparse
    import uuid

    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=os.getenv("DATA_DIR", "./data"))
    ap.add_argument("--table", help="Load a single table (default: all)")
    ap.add_argument("--batch-id", default=f"manual-{uuid.uuid4().hex[:8]}")
    ap.add_argument("--exclude", nargs="*", default=[],
                    help="Tables to skip (space-separated)")
    ap.add_argument("--include", nargs="*", default=None,
                    help="Restrict to these tables (space-separated)")
    args = ap.parse_args()

    data_dir = Path(args.data_dir)
    if args.table:
        path = data_dir / f"{args.table}.dat"
        with Step(batch_id=args.batch_id, layer="bronze", step=f"load_{args.table}") as s:
            truncate(args.table)
            n, tool = load_file(path, args.table, args.batch_id)
            s.record(rows_in=n, rows_out=n, tool=tool)
            print(f"{args.table}: {n:,} rows via {tool}")
    else:
        counts = load_all(
            data_dir, args.batch_id,
            include=set(args.include) if args.include else None,
            exclude=set(args.exclude),
        )
        print(f"\nTotal: {sum(counts.values()):,} rows across {len(counts)} tables")
