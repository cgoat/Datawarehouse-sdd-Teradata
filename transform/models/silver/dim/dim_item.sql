-- TPC-DS item is SCD2 — multiple rows per i_item_id, unique per i_item_sk.
-- We retain all versions; is_current flags the active one so marts can
-- filter to current prices without losing history joins on fact.item_sk.

SELECT
    i_item_sk                                           AS item_key,
    i_item_id                                           AS item_id,
    i_item_desc                                         AS item_description,
    TRIM(i_product_name)                                AS product_name,
    TRIM(i_brand)                                       AS brand,
    i_brand_id                                          AS brand_id,
    TRIM(i_class)                                       AS item_class,
    i_class_id                                          AS item_class_id,
    TRIM(i_category)                                    AS category,
    i_category_id                                       AS category_id,
    TRIM(i_manufact)                                    AS manufacturer,
    i_manufact_id                                       AS manufacturer_id,
    TRIM(i_size)                                        AS size,
    TRIM(i_color)                                       AS color,
    TRIM(i_units)                                       AS units,
    TRIM(i_container)                                   AS container,
    i_manager_id                                        AS manager_id,
    i_current_price                                     AS current_price,
    i_wholesale_cost                                    AS wholesale_cost,
    i_rec_start_date                                    AS rec_start_date,
    i_rec_end_date                                      AS rec_end_date,
    CASE WHEN i_rec_end_date IS NULL THEN 1 ELSE 0 END  AS is_current
FROM {{ source('bronze', 'item') }}
WHERE i_item_sk IS NOT NULL
