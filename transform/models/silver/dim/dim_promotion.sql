SELECT
    p_promo_sk                                               AS promo_key,
    p_promo_id                                               AS promo_id,
    TRIM(p_promo_name)                                       AS promo_name,
    p_cost                                                   AS cost,
    p_response_target                                        AS response_target,
    TRIM(p_purpose)                                          AS purpose,
    CASE WHEN UPPER(p_discount_active)= 'Y' THEN 1 ELSE 0 END AS is_active,
    CASE WHEN UPPER(p_channel_dmail) = 'Y' THEN 1 ELSE 0 END  AS via_dmail,
    CASE WHEN UPPER(p_channel_email) = 'Y' THEN 1 ELSE 0 END  AS via_email,
    CASE WHEN UPPER(p_channel_catalog)= 'Y' THEN 1 ELSE 0 END AS via_catalog,
    CASE WHEN UPPER(p_channel_tv)    = 'Y' THEN 1 ELSE 0 END  AS via_tv,
    CASE WHEN UPPER(p_channel_radio) = 'Y' THEN 1 ELSE 0 END  AS via_radio,
    CASE WHEN UPPER(p_channel_press) = 'Y' THEN 1 ELSE 0 END  AS via_press,
    CASE WHEN UPPER(p_channel_event) = 'Y' THEN 1 ELSE 0 END  AS via_event,
    CASE WHEN UPPER(p_channel_demo)  = 'Y' THEN 1 ELSE 0 END  AS via_demo,
    p_start_date_sk                                          AS start_date_key,
    p_end_date_sk                                            AS end_date_key,
    p_item_sk                                                AS item_key
FROM {{ source('bronze', 'promotion') }}
WHERE p_promo_sk IS NOT NULL
