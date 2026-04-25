"""FastAPI endpoints powering the PHP dashboard.

Start:  uvicorn api.main:app --reload --port 8000
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ingestion.db import connect, db_names

app = FastAPI(title="DW Reliability API", version="0.1.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"],
)


def _rows(sql: str, params: tuple = ()) -> list[dict]:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        cols = [d[0].lower() for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


@app.get("/runs")
def runs(limit: int = 50) -> list[dict]:
    dq = db_names()["dq"]
    sql = (
        f"SELECT TOP {int(limit)} batch_id, layer, step, status, rows_in, rows_out, "
        f"CAST(started_at AS VARCHAR(25)) AS started_at, duration_sec, tool "
        f"FROM {dq}.run_log ORDER BY started_at DESC"
    )
    return _rows(sql)


@app.get("/dq/latest")
def dq_latest(suite: str | None = None) -> list[dict]:
    dq = db_names()["dq"]
    where_suite = f"AND suite = '{suite}'" if suite in ("bronze", "silver") else ""
    sql = (
        f"SELECT suite, table_name, expectation, success, observed_value, "
        f"CAST(run_at AS VARCHAR(25)) AS run_at "
        f"FROM {dq}.dq_result "
        f"WHERE batch_id = (SELECT MAX(batch_id) FROM {dq}.dq_result) "
        f"{where_suite} "
        f"ORDER BY success ASC, suite, table_name, expectation"
    )
    return _rows(sql)


@app.get("/silver/counts")
def silver_counts() -> list[dict]:
    """Row counts for Silver fact/dim tables + their anomaly sidecars.
    Powers the Phase 1 Silver dashboard tab."""
    silver = db_names()["silver"]
    tables = [
        "dim_customer", "dim_item", "dim_date", "dim_store", "dim_promotion",
        "fact_sales", "fact_returns", "fact_inventory",
        "fact_sales__anomalies", "fact_returns__anomalies",
    ]
    out: list[dict] = []
    with connect() as conn, conn.cursor() as cur:
        for t in tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {silver}.{t}")
                out.append({"table": t, "row_count": int(cur.fetchone()[0])})
            except Exception as e:
                out.append({"table": t, "row_count": None, "error": str(e)[:200]})
    return out


@app.get("/silver/anomaly_breakdown")
def silver_anomaly_breakdown() -> list[dict]:
    """Anomaly counts grouped by fact + reason — what the BA + reliability eng both want."""
    silver = db_names()["silver"]
    unions = []
    for fact in ("fact_sales__anomalies", "fact_returns__anomalies"):
        unions.append(
            f"SELECT '{fact}' AS source_table, _anomaly_reason, COUNT(*) AS cnt "
            f"FROM {silver}.{fact} GROUP BY _anomaly_reason"
        )
    sql = " UNION ALL ".join(unions) + " ORDER BY source_table, cnt DESC"
    try:
        return _rows(sql)
    except Exception as e:
        return [{"error": str(e)[:500]}]


@app.get("/gold/counts")
def gold_counts() -> list[dict]:
    """Row counts for the 4 marts."""
    gold = db_names()["gold"]
    tables = [
        "mart_sales_performance", "mart_customer_360",
        "mart_product_analytics", "mart_channel_comparison",
    ]
    out: list[dict] = []
    with connect() as conn, conn.cursor() as cur:
        for t in tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {gold}.{t}")
                out.append({"table": t, "row_count": int(cur.fetchone()[0])})
            except Exception as e:
                out.append({"table": t, "row_count": None, "error": str(e)[:200]})
    return out


@app.get("/gold/sales_summary")
def gold_sales_summary() -> dict:
    """Headline KPIs for the home dashboard."""
    gold = db_names()["gold"]
    try:
        rows = _rows(
            f"SELECT channel, "
            f"  SUM(units_sold) AS units_sold, "
            f"  SUM(order_count) AS order_count, "
            f"  SUM(gross_sales) AS gross_sales, "
            f"  SUM(net_sales) AS net_sales, "
            f"  SUM(net_profit) AS net_profit, "
            f"  SUM(returns_amount) AS returns_amount "
            f"FROM {gold}.mart_sales_performance GROUP BY channel ORDER BY channel"
        )
        return {"by_channel": rows}
    except Exception as e:
        return {"error": str(e)[:500]}


@app.get("/gold/top_products")
def gold_top_products(limit: int = 20) -> list[dict]:
    gold = db_names()["gold"]
    try:
        return _rows(
            f"SELECT TOP {int(limit)} item_id, product_name, brand, category, "
            f"  units_sold, gross_revenue, returns_rate, top_channel, rank_by_revenue "
            f"FROM {gold}.mart_product_analytics "
            f"ORDER BY rank_by_revenue ASC"
        )
    except Exception as e:
        return [{"error": str(e)[:500]}]


@app.get("/perf/runs")
def perf_runs() -> list[dict]:
    """List benchmark runs with phase coverage so the UI can pick one."""
    dq = db_names()["dq"]
    sql = (
        f"SELECT run_id, "
        f"  MAX(CASE WHEN phase='before' THEN 1 ELSE 0 END) AS has_before, "
        f"  MAX(CASE WHEN phase='after'  THEN 1 ELSE 0 END) AS has_after, "
        f"  MIN(CAST(started_at AS VARCHAR(25))) AS first_at, "
        f"  COUNT(*) AS row_count "
        f"FROM {dq}.perf_log "
        f"GROUP BY run_id ORDER BY MAX(started_at) DESC"
    )
    try:
        return _rows(sql)
    except Exception as e:
        return [{"error": str(e)[:500]}]


@app.get("/perf/compare")
def perf_compare(run_id: str | None = None) -> list[dict]:
    """Median timings per query, before vs after, with delta + speedup."""
    dq = db_names()["dq"]
    where_run = f"WHERE run_id = '{run_id}'" if run_id else ""
    # Teradata lacks PERCENTILE_CONT in older versions — approximate median by
    # picking the middle row from a sorted set per (query, phase).
    sql = (
        f"WITH ranked AS ( "
        f"  SELECT query_name, phase, duration_sec, "
        f"         ROW_NUMBER() OVER (PARTITION BY query_name, phase ORDER BY duration_sec) AS rn, "
        f"         COUNT(*) OVER (PARTITION BY query_name, phase) AS cnt "
        f"  FROM {dq}.perf_log "
        f"  {where_run}"
        f"), "
        f"medians AS ( "
        f"  SELECT query_name, phase, AVG(duration_sec) AS median_sec "
        f"  FROM ranked WHERE rn IN ((cnt+1)/2, (cnt+2)/2) "
        f"  GROUP BY query_name, phase "
        f"), "
        f"pivot AS ( "
        f"  SELECT query_name, "
        f"         MAX(CASE WHEN phase='before' THEN median_sec END) AS before_sec, "
        f"         MAX(CASE WHEN phase='after'  THEN median_sec END) AS after_sec "
        f"  FROM medians GROUP BY query_name "
        f") "
        f"SELECT query_name, "
        f"       CAST(before_sec AS DECIMAL(10,3)) AS before_sec, "
        f"       CAST(after_sec  AS DECIMAL(10,3)) AS after_sec, "
        f"       CAST(before_sec - after_sec AS DECIMAL(10,3)) AS delta_sec, "
        f"       CAST(before_sec / NULLIF(after_sec, 0) AS DECIMAL(10,2)) AS speedup_x "
        f"FROM pivot ORDER BY query_name"
    )
    try:
        return _rows(sql)
    except Exception as e:
        return [{"error": str(e)[:500]}]


@app.get("/perf/raw")
def perf_raw(run_id: str | None = None) -> list[dict]:
    dq = db_names()["dq"]
    where_run = f"WHERE run_id = '{run_id}'" if run_id else ""
    sql = (
        f"SELECT run_id, phase, query_name, iteration, duration_sec, rows_returned, "
        f"  CAST(started_at AS VARCHAR(25)) AS started_at "
        f"FROM {dq}.perf_log "
        f"{where_run} "
        f"ORDER BY query_name, phase, iteration"
    )
    try:
        return _rows(sql)
    except Exception as e:
        return [{"error": str(e)[:500]}]


@app.get("/gold/segments")
def gold_segments() -> list[dict]:
    gold = db_names()["gold"]
    try:
        return _rows(
            f"SELECT segment, COUNT(*) AS customers, "
            f"  CAST(AVG(lifetime_value) AS DECIMAL(15,2)) AS avg_ltv, "
            f"  CAST(AVG(frequency) AS DECIMAL(10,2)) AS avg_frequency, "
            f"  CAST(AVG(recency_days) AS INTEGER) AS avg_recency_days "
            f"FROM {gold}.mart_customer_360 "
            f"WHERE segment IS NOT NULL "
            f"GROUP BY segment ORDER BY customers DESC"
        )
    except Exception as e:
        return [{"error": str(e)[:500]}]


@app.get("/health")
def health() -> dict:
    try:
        _rows("SELECT 1 AS ok")
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
