"""Benchmark queries — exercise different access patterns the BA marts hit:
full scan + group by, FK joins, date-range filters, multi-join.

Each query embeds a /* {tag} */ comment so Teradata's plan/result cache
treats successive runs as distinct (otherwise we'd just measure cache hits).
"""
from __future__ import annotations

QUERIES: dict[str, str] = {
    # Full scan + group by — heavy aggregate, no filter. Tests COLLECT STATISTICS
    # on (channel) and join distribution to dim_date.
    "annual_sales_by_channel": """
        SELECT /* {tag} */ d.calendar_year, fs.channel,
               SUM(fs.net_paid)  AS revenue,
               SUM(fs.quantity)  AS units,
               COUNT(*)          AS line_count
        FROM DW_SILVER.fact_sales fs
        INNER JOIN DW_SILVER.dim_date d ON fs.sold_date_sk = d.date_key
        GROUP BY d.calendar_year, fs.channel
        ORDER BY d.calendar_year, fs.channel
    """,

    # Group by high-cardinality customer_sk + join. Tests stats on join column.
    "top_25_customers": """
        SELECT TOP 25 /* {tag} */
               c.customer_id, c.customer_name,
               SUM(fs.net_paid)               AS lifetime_value,
               COUNT(DISTINCT fs.channel)     AS channels_used
        FROM DW_SILVER.fact_sales fs
        INNER JOIN DW_SILVER.dim_customer c ON fs.customer_sk = c.customer_key
        GROUP BY c.customer_id, c.customer_name
        ORDER BY lifetime_value DESC
    """,

    # FK join on item + filter on dim — tests stats on (item_sk) and dim filter.
    "sales_by_category": """
        SELECT /* {tag} */ i.category,
               SUM(fs.net_paid)            AS revenue,
               COUNT(DISTINCT fs.customer_sk) AS unique_customers
        FROM DW_SILVER.fact_sales fs
        INNER JOIN DW_SILVER.dim_item i ON fs.item_sk = i.item_key
        WHERE i.is_current = 1
        GROUP BY i.category
        ORDER BY revenue DESC
    """,

    # Date-range filter + group by date — biggest PPI win candidate.
    "daily_sales_one_month": """
        SELECT /* {tag} */ d.calendar_date, fs.channel,
               SUM(fs.quantity)  AS units,
               SUM(fs.net_paid)  AS revenue
        FROM DW_SILVER.fact_sales fs
        INNER JOIN DW_SILVER.dim_date d ON fs.sold_date_sk = d.date_key
        WHERE d.calendar_year = 2002 AND d.month_of_year = 1
        GROUP BY d.calendar_date, fs.channel
        ORDER BY d.calendar_date, fs.channel
    """,

    # Sales-vs-returns multi-join — exercises join-column stats on both facts.
    "returns_rate_by_brand": """
        SELECT /* {tag} */ i.brand,
               SUM(fs.quantity)  AS units_sold,
               COALESCE(SUM(fr.return_quantity), 0) AS units_returned,
               CAST(COALESCE(SUM(fr.return_quantity), 0) AS DECIMAL(20,4))
                  / NULLIF(SUM(fs.quantity), 0) AS returns_rate
        FROM DW_SILVER.fact_sales fs
        INNER JOIN DW_SILVER.dim_item i ON fs.item_sk = i.item_key
        LEFT JOIN DW_SILVER.fact_returns fr
               ON fs.item_sk = fr.item_sk
              AND fs.sale_order_id = fr.return_order_id
        WHERE i.is_current = 1
        GROUP BY i.brand
        HAVING SUM(fs.quantity) > 1000
        ORDER BY returns_rate DESC
    """,
}
