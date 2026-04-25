-- Per-item performance: lifetime sales, returns rate, ranks within category.
-- One row per current item version (is_current=1) so the BA gets one row per
-- product even though dim_item is SCD2.

{{ config(
    materialized='table',
    post_hook=[
        "COLLECT STATISTICS ON {{ this }} COLUMN (item_key)",
        "COLLECT STATISTICS ON {{ this }} COLUMN (category)"
    ]
) }}

WITH item_sales AS (
    SELECT
        item_sk,
        SUM(quantity)                       AS units_sold,
        SUM(ext_sales_price)                AS gross_revenue,
        SUM(net_paid)                       AS net_revenue,
        SUM(net_profit)                     AS net_profit,
        COUNT(DISTINCT customer_sk)         AS distinct_customers,
        AVG(sales_price)                    AS avg_sales_price
    FROM {{ ref('fact_sales') }}
    GROUP BY item_sk
),
item_returns AS (
    SELECT
        item_sk,
        SUM(return_quantity)                AS units_returned,
        SUM(return_amt)                     AS returns_amount
    FROM {{ ref('fact_returns') }}
    GROUP BY item_sk
),
item_top_channel AS (
    SELECT item_sk, channel
    FROM (
        SELECT
            item_sk, channel,
            ROW_NUMBER() OVER (PARTITION BY item_sk ORDER BY SUM(quantity) DESC) AS rn
        FROM {{ ref('fact_sales') }}
        GROUP BY item_sk, channel
    ) t
    WHERE rn = 1
)
SELECT
    i.item_key,
    i.item_id,
    i.product_name,
    i.brand,
    i.category,
    i.item_class,
    i.manufacturer,
    i.size,
    i.color,
    i.current_price,
    i.wholesale_cost,
    COALESCE(s.units_sold, 0)               AS units_sold,
    COALESCE(s.gross_revenue, 0)            AS gross_revenue,
    COALESCE(s.net_revenue, 0)              AS net_revenue,
    COALESCE(s.net_profit, 0)               AS net_profit,
    s.avg_sales_price,
    COALESCE(s.distinct_customers, 0)       AS distinct_customers,
    COALESCE(r.units_returned, 0)           AS units_returned,
    COALESCE(r.returns_amount, 0)           AS returns_amount,
    CAST(COALESCE(r.units_returned, 0) AS DECIMAL(15,4))
        / NULLIF(s.units_sold, 0)           AS returns_rate,
    tc.channel                              AS top_channel,
    RANK() OVER (ORDER BY COALESCE(s.gross_revenue, 0) DESC)
                                            AS rank_by_revenue,
    RANK() OVER (PARTITION BY i.category ORDER BY COALESCE(s.gross_revenue, 0) DESC)
                                            AS rank_in_category
FROM {{ ref('dim_item') }} i
LEFT JOIN item_sales       s  ON i.item_key = s.item_sk
LEFT JOIN item_returns     r  ON i.item_key = r.item_sk
LEFT JOIN item_top_channel tc ON i.item_key = tc.item_sk
WHERE i.is_current = 1
