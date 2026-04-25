SELECT
    _anomaly_reason,
    channel, return_order_id, item_sk, refunded_customer_sk, returning_customer_sk,
    refunded_cdemo_sk, refunded_hdemo_sk, refunded_addr_sk,
    store_sk, call_center_sk, catalog_page_sk, warehouse_sk, web_page_sk, ship_mode_sk,
    reason_sk, returned_date_sk, returned_time_sk,
    return_quantity, return_amt, return_tax, return_amt_inc_tax, fee, return_ship_cost,
    refunded_cash, reversed_charge, credit, net_loss,
    _batch_id
FROM {{ ref('int_returns_unioned') }}
WHERE _anomaly_reason IS NOT NULL
