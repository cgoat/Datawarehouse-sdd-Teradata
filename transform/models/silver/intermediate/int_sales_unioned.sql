-- Unified sales across all three channels with prioritized anomaly tagging.
-- fact_sales filters reason IS NULL; fact_sales__anomalies filters reason IS NOT NULL.
-- Subquery (not WITH) to avoid nested CTEs when this model is inlined ephemerally.

SELECT
    u.*,
    CASE
        WHEN item_sk IS NULL                               THEN 'missing_item_sk'
        WHEN sale_order_id IS NULL                         THEN 'missing_order_id'
        WHEN sold_date_sk IS NULL                          THEN 'missing_sold_date'
        WHEN quantity IS NOT NULL AND quantity <= 0        THEN 'non_positive_quantity'
        WHEN sales_price IS NOT NULL AND sales_price < 0   THEN 'negative_sales_price'
        WHEN net_paid IS NOT NULL AND net_paid < 0         THEN 'negative_net_paid'
        ELSE NULL
    END AS _anomaly_reason
FROM (
    SELECT * FROM {{ ref('stg_store_sales') }}
    UNION ALL
    SELECT * FROM {{ ref('stg_catalog_sales') }}
    UNION ALL
    SELECT * FROM {{ ref('stg_web_sales') }}
) u
