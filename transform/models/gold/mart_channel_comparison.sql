-- Monthly channel side-by-side: gross, net, profit, returns, share-of-total.
-- Grain: (calendar_year, month, channel). Adds share_of_total so the BA can
-- graph channel mix over time without re-aggregating.

{{ config(
    materialized='table',
    post_hook=[
        "COLLECT STATISTICS ON {{ this }} COLUMN (calendar_year, month_of_year)",
        "COLLECT STATISTICS ON {{ this }} COLUMN (channel)"
    ]
) }}

WITH monthly_sales AS (
    SELECT
        d.calendar_year,
        d.month_of_year,
        d.quarter_of_year,
        fs.channel,
        SUM(fs.quantity)                          AS units_sold,
        COUNT(DISTINCT fs.sale_order_id)          AS order_count,
        SUM(fs.ext_sales_price)                   AS gross_sales,
        SUM(fs.net_paid)                          AS net_sales,
        SUM(fs.net_profit)                        AS net_profit,
        COUNT(DISTINCT fs.customer_sk)            AS unique_customers
    FROM {{ ref('fact_sales') }} fs
    INNER JOIN {{ ref('dim_date') }} d ON fs.sold_date_sk = d.date_key
    GROUP BY d.calendar_year, d.month_of_year, d.quarter_of_year, fs.channel
),
monthly_returns AS (
    SELECT
        d.calendar_year,
        d.month_of_year,
        fr.channel,
        SUM(fr.return_quantity)                   AS units_returned,
        SUM(fr.return_amt)                        AS returns_amount
    FROM {{ ref('fact_returns') }} fr
    INNER JOIN {{ ref('dim_date') }} d ON fr.returned_date_sk = d.date_key
    GROUP BY d.calendar_year, d.month_of_year, fr.channel
),
monthly_total AS (
    SELECT calendar_year, month_of_year, SUM(gross_sales) AS total_gross
    FROM monthly_sales
    GROUP BY calendar_year, month_of_year
)
SELECT
    s.calendar_year,
    s.month_of_year,
    s.quarter_of_year,
    s.channel,
    s.units_sold,
    s.order_count,
    s.unique_customers,
    s.gross_sales,
    s.net_sales,
    s.net_profit,
    CAST(s.units_sold AS DECIMAL(15,2)) / NULLIF(s.order_count, 0)   AS avg_basket_size,
    CAST(s.net_sales AS DECIMAL(15,2)) / NULLIF(s.order_count, 0)    AS avg_order_value,
    CAST(s.net_profit AS DECIMAL(15,4)) / NULLIF(s.gross_sales, 0)   AS profit_margin,
    COALESCE(r.units_returned, 0)                                    AS units_returned,
    COALESCE(r.returns_amount, 0)                                    AS returns_amount,
    CAST(COALESCE(r.returns_amount, 0) AS DECIMAL(15,4))
        / NULLIF(s.gross_sales, 0)                                   AS returns_rate,
    CAST(s.gross_sales AS DECIMAL(15,4))
        / NULLIF(t.total_gross, 0)                                   AS share_of_total
FROM monthly_sales s
LEFT JOIN monthly_returns r
       ON s.calendar_year   = r.calendar_year
      AND s.month_of_year   = r.month_of_year
      AND s.channel         = r.channel
LEFT JOIN monthly_total t
       ON s.calendar_year   = t.calendar_year
      AND s.month_of_year   = t.month_of_year
