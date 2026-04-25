"""Apply Teradata performance tunings between benchmark runs.

Tuning 1 — comprehensive COLLECT STATISTICS on Silver/Gold join + filter cols.
   Cheapest, safest win. The optimizer makes much better plans with fresh stats.

Tuning 2 — recreate fact_sales with PPI by year on sold_date_sk.
   Big win for date-filtered queries (`daily_sales_one_month` benchmark).
   Recreates the table via DROP + CREATE TABLE AS SELECT — no dbt involvement.
   Skip if dbt manages this table strictly; we accept that the next dbt build
   will recreate without PPI unless the model config is updated to match.

Run with:
    python -m perf.tune                  # both tunings
    python -m perf.tune --only stats     # just stats
    python -m perf.tune --only ppi       # just PPI
"""
from __future__ import annotations

import argparse
import time

from ingestion.db import connect, db_names

# (table, [columns or column-groups]) — string passed as-is into COLLECT STATS.
SILVER_STATS: dict[str, list[str]] = {
    "fact_sales": [
        "channel",
        "item_sk",
        "customer_sk",
        "sold_date_sk",
        "store_sk",
        "promo_sk",
        "(channel, sold_date_sk)",
        "(item_sk, sold_date_sk)",
    ],
    "fact_returns": [
        "channel",
        "item_sk",
        "refunded_customer_sk",
        "returned_date_sk",
        "(item_sk, return_order_id)",
    ],
    "fact_inventory": [
        "item_sk",
        "warehouse_sk",
        "date_sk",
    ],
    "dim_customer": ["customer_key", "customer_id", "state", "segment_dummy_skip"],
    "dim_date":     ["date_key", "calendar_year", "month_of_year", "(calendar_year, month_of_year)"],
    "dim_item":     ["item_key", "category", "brand", "is_current"],
    "dim_store":    ["store_key", "state"],
    "dim_promotion":["promo_key"],
}

GOLD_STATS: dict[str, list[str]] = {
    "mart_sales_performance": ["date_key", "channel", "(calendar_year, month_of_year)"],
    "mart_customer_360":      ["customer_key", "segment", "preferred_channel"],
    "mart_product_analytics": ["item_key", "category", "brand"],
    "mart_channel_comparison":["(calendar_year, month_of_year)", "channel"],
}


def _collect(database: str, table: str, expr: str, cur) -> str:
    """Run one COLLECT STATISTICS. Returns 'OK' or 'SKIP: <reason>'."""
    if "skip" in expr.lower():
        return "skip"
    sql = f"COLLECT STATISTICS COLUMN {expr} ON {database}.{table}"
    try:
        cur.execute(sql)
        return "ok"
    except Exception as e:
        msg = str(e).split(']')[2] if ']' in str(e) else str(e)
        return f"err: {msg[:80].strip()}"


def collect_stats() -> None:
    sl = db_names()["silver"]
    gd = db_names()["gold"]
    with connect() as conn, conn.cursor() as cur:
        for db, plan in [(sl, SILVER_STATS), (gd, GOLD_STATS)]:
            for table, cols in plan.items():
                for expr in cols:
                    t0 = time.time()
                    status = _collect(db, table, expr, cur)
                    if status == "skip":
                        continue
                    dur = round(time.time() - t0, 2)
                    print(f"  {db}.{table:25s} {expr:50s} {status:8s} {dur}s")


def recreate_fact_sales_ppi() -> None:
    """Recreate fact_sales with PARTITION BY year(sold_date_sk).
    sold_date_sk is a Julian-style integer; we split by year-bucket using
    a date-range macro derived from dim_date."""
    sl = db_names()["silver"]
    with connect() as conn, conn.cursor() as cur:
        # Pull min/max of populated sold_date_sk so the partition range covers data.
        cur.execute(f"SELECT MIN(sold_date_sk), MAX(sold_date_sk) FROM {sl}.fact_sales WHERE sold_date_sk IS NOT NULL")
        min_sk, max_sk = cur.fetchone()
        # Pad ±1 year (~365 days each side).
        min_sk = int(min_sk) - 365
        max_sk = int(max_sk) + 365
        each = 365
        print(f"  partition range: {min_sk}..{max_sk} EACH {each}")

        ppi_clause = (
            f"PRIMARY INDEX (item_sk, sale_order_id) "
            f"PARTITION BY RANGE_N(sold_date_sk BETWEEN {min_sk} AND {max_sk} "
            f"EACH {each}, NO RANGE, UNKNOWN)"
        )

        # DROP + CREATE TABLE AS SELECT (CTAS) is fastest. Stage-and-rename would be
        # safer for prod (zero-downtime), but our facts are rebuilt by dbt anyway.
        new_table = f"{sl}.fact_sales_ppi"
        cur.execute(f"DROP TABLE {new_table}") if False else None  # idempotency below
        try:
            cur.execute(f"DROP TABLE {new_table}")
        except Exception:
            pass
        print(f"  creating {new_table} with PPI...")
        t0 = time.time()
        # Teradata CTAS: `AS source_table WITH NO DATA` (no parens, no SELECT).
        # Index/partition clauses follow after.
        cur.execute(
            f"CREATE TABLE {new_table} AS {sl}.fact_sales WITH NO DATA "
            f"{ppi_clause}"
        )
        cur.execute(f"INSERT INTO {new_table} SELECT * FROM {sl}.fact_sales")
        cur.execute(f"SELECT COUNT(*) FROM {new_table}")
        n = cur.fetchone()[0]
        dur = round(time.time() - t0, 1)
        print(f"  inserted {n:,} rows into {new_table} ({dur}s)")

        # Atomic swap: rename original out, rename new in.
        try:
            cur.execute(f"DROP TABLE {sl}.fact_sales_pre_ppi")
        except Exception:
            pass
        cur.execute(f"RENAME TABLE {sl}.fact_sales TO {sl}.fact_sales_pre_ppi")
        cur.execute(f"RENAME TABLE {sl}.fact_sales_ppi TO {sl}.fact_sales")
        print(f"  swapped: fact_sales now has PPI; old version preserved as fact_sales_pre_ppi")

        # Stats on new table.
        for expr in SILVER_STATS["fact_sales"]:
            if "skip" in expr.lower():
                continue
            try:
                cur.execute(f"COLLECT STATISTICS COLUMN {expr} ON {sl}.fact_sales")
            except Exception as e:
                print(f"  warn: stat {expr} failed: {str(e)[:80]}")
        print("  collected stats on new fact_sales")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=["stats", "ppi", "both"], default="both")
    args = ap.parse_args()

    if args.only in ("stats", "both"):
        print("=== Tuning 1: COLLECT STATISTICS ===")
        collect_stats()
    if args.only in ("ppi", "both"):
        print("\n=== Tuning 2: PPI on fact_sales ===")
        try:
            recreate_fact_sales_ppi()
        except Exception as e:
            print(f"  PPI tune failed: {e}")
            print("  (stats tuning still applied; benchmark will reflect that.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
