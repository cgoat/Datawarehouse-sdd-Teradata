-- Unified returns across all three channels + anomaly tagging.
-- Subquery (not WITH) to avoid nested CTEs when inlined ephemerally.

SELECT
    u.*,
    CASE
        WHEN item_sk IS NULL                                           THEN 'missing_item_sk'
        WHEN return_order_id IS NULL                                   THEN 'missing_order_id'
        WHEN returned_date_sk IS NULL                                  THEN 'missing_returned_date'
        WHEN return_quantity IS NOT NULL AND return_quantity <= 0      THEN 'non_positive_quantity'
        WHEN return_amt IS NOT NULL AND return_amt < 0                 THEN 'negative_return_amt'
        ELSE NULL
    END AS _anomaly_reason
FROM (
    SELECT * FROM {{ ref('stg_store_returns') }}
    UNION ALL
    SELECT * FROM {{ ref('stg_catalog_returns') }}
    UNION ALL
    SELECT * FROM {{ ref('stg_web_returns') }}
) u
