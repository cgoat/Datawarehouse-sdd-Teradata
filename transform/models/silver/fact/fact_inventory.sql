-- Weekly inventory snapshot per item per warehouse. Grain: (date, item, warehouse).

{{ config(
    materialized='table',
    post_hook=[
        "COLLECT STATISTICS ON {{ this }} COLUMN (item_sk)",
        "COLLECT STATISTICS ON {{ this }} COLUMN (date_sk)"
    ]
) }}

SELECT
    inv_date_sk              AS date_sk,
    inv_item_sk              AS item_sk,
    inv_warehouse_sk         AS warehouse_sk,
    inv_quantity_on_hand     AS quantity_on_hand,
    _batch_id
FROM {{ source('bronze', 'inventory') }}
WHERE inv_item_sk IS NOT NULL
  AND inv_warehouse_sk IS NOT NULL
  AND inv_date_sk IS NOT NULL
