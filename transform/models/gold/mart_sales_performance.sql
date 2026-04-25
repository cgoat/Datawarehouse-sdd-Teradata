-- Daily rollup of sales by channel + date. Returns joined LEFT so a sales-only day
-- still shows up. Roll up to month/quarter/year on the consumer side.

{{ config(
    materialized='table',
    post_hook=[
        "COLLECT STATISTICS ON {{ this }} COLUMN (date_key)",
        "COLLECT STATISTICS ON {{ this }} COLUMN (channel)"
    ]
) }}

WITH daily_sales AS (
    SELECT
        sold_date_sk                              AS date_key,
        channel,
        SUM(quantity)                             AS units_sold,
        COUNT(DISTINCT sale_order_id)             AS order_count,
        SUM(ext_sales_price)                      AS gross_sales,
        SUM(ext_discount_amt)                     AS discount_amount,
        SUM(ext_tax)                              AS tax_amount,
        SUM(net_paid)                             AS net_sales,
        SUM(net_profit)                           AS net_profit
    FROM {{ ref('fact_sales') }}
    GROUP BY sold_date_sk, channel
),
daily_returns AS (
    SELECT
        returned_date_sk                          AS date_key,
        channel,
        SUM(return_quantity)                      AS units_returned,
        SUM(return_amt)                           AS returns_amount
    FROM {{ ref('fact_returns') }}
    GROUP BY returned_date_sk, channel
)
SELECT
    s.date_key,
    d.calendar_date,
    d.calendar_year,
    d.quarter_of_year,
    d.month_of_year,
    d.day_of_week,
    d.day_name,
    d.is_weekend,
    s.channel,
    s.units_sold,
    s.order_count,
    CAST(s.net_sales AS DECIMAL(15,2)) / NULLIF(s.order_count, 0)   AS avg_order_value,
    s.gross_sales,
    s.discount_amount,
    s.tax_amount,
    s.net_sales,
    s.net_profit,
    CAST(s.net_profit AS DECIMAL(15,4)) / NULLIF(s.gross_sales, 0)  AS profit_margin,
    COALESCE(r.units_returned, 0)                                   AS units_returned,
    COALESCE(r.returns_amount, 0)                                   AS returns_amount,
    s.gross_sales - COALESCE(r.returns_amount, 0)                   AS net_revenue,
    CAST(COALESCE(r.units_returned, 0) AS DECIMAL(15,4))
        / NULLIF(s.units_sold, 0)                                   AS returns_rate
FROM daily_sales s
INNER JOIN {{ ref('dim_date') }} d
       ON s.date_key = d.date_key
LEFT JOIN daily_returns r
       ON s.date_key = r.date_key
      AND s.channel  = r.channel
