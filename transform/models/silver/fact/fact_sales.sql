-- Clean sales rows across all channels. Rows failing any business rule
-- go to fact_sales__anomalies — never silently dropped.

{{ config(
    materialized='table',
    post_hook=[
        "COLLECT STATISTICS ON {{ this }} COLUMN (item_sk)",
        "COLLECT STATISTICS ON {{ this }} COLUMN (sold_date_sk)",
        "COLLECT STATISTICS ON {{ this }} COLUMN (customer_sk)",
        "COLLECT STATISTICS ON {{ this }} COLUMN (channel)"
    ]
) }}

-- Drop _source_file from facts to keep DW_SILVER under PERM. Provenance can be
-- recovered via _batch_id (kept) joined back to DW_DQ.run_log.
SELECT
    channel, sale_order_id, item_sk, customer_sk, cdemo_sk, hdemo_sk, addr_sk,
    store_sk, call_center_sk, catalog_page_sk, warehouse_sk, web_page_sk, web_site_sk,
    ship_mode_sk, promo_sk, sold_date_sk, ship_date_sk, sold_time_sk,
    quantity, wholesale_cost, list_price, sales_price,
    ext_discount_amt, ext_sales_price, ext_wholesale_cost, ext_list_price,
    ext_tax, coupon_amt, ext_ship_cost,
    net_paid, net_paid_inc_tax, net_paid_inc_ship, net_paid_inc_ship_tax, net_profit,
    _batch_id
FROM {{ ref('int_sales_unioned') }}
WHERE _anomaly_reason IS NULL
