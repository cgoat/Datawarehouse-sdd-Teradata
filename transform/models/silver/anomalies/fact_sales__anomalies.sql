-- Sales rows that failed business rules. _anomaly_reason names the rule
-- (single prioritized cause — see int_sales_unioned).

SELECT
    _anomaly_reason,
    channel, sale_order_id, item_sk, customer_sk, cdemo_sk, hdemo_sk, addr_sk,
    store_sk, call_center_sk, catalog_page_sk, warehouse_sk, web_page_sk, web_site_sk,
    ship_mode_sk, promo_sk, sold_date_sk, ship_date_sk, sold_time_sk,
    quantity, wholesale_cost, list_price, sales_price,
    ext_discount_amt, ext_sales_price, ext_wholesale_cost, ext_list_price,
    ext_tax, coupon_amt, ext_ship_cost,
    net_paid, net_paid_inc_tax, net_paid_inc_ship, net_paid_inc_ship_tax, net_profit,
    _batch_id
FROM {{ ref('int_sales_unioned') }}
WHERE _anomaly_reason IS NOT NULL
