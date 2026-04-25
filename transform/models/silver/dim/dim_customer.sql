-- SCD1 customer dim: current address + current demographics joined in.
-- Any customer missing surrogate key is excluded (handled upstream).

SELECT
    c.c_customer_sk                                     AS customer_key,
    c.c_customer_id                                     AS customer_id,
    TRIM(c.c_salutation)                                AS salutation,
    TRIM(c.c_first_name)                                AS first_name,
    TRIM(c.c_last_name)                                 AS last_name,
    TRIM(c.c_first_name) || ' ' || TRIM(c.c_last_name)  AS customer_name,
    CASE WHEN UPPER(c.c_preferred_cust_flag) = 'Y' THEN 1 ELSE 0 END AS is_preferred_customer,
    c.c_birth_year                                      AS birth_year,
    c.c_birth_country                                   AS birth_country,
    c.c_email_address                                   AS email_address,
    c.c_first_sales_date_sk                             AS first_sales_date_key,
    c.c_first_shipto_date_sk                            AS first_shipto_date_key,

    a.ca_city                                           AS city,
    a.ca_county                                         AS county,
    a.ca_state                                          AS state,
    a.ca_zip                                            AS zip,
    a.ca_country                                        AS country,
    a.ca_gmt_offset                                     AS gmt_offset,

    cdem.cd_gender                                      AS gender,
    cdem.cd_marital_status                              AS marital_status,
    cdem.cd_education_status                            AS education_status,
    cdem.cd_credit_rating                               AS credit_rating,
    cdem.cd_purchase_estimate                           AS purchase_estimate,
    cdem.cd_dep_count                                   AS dependent_count,

    TRIM(hdem.hd_buy_potential)                         AS buy_potential,
    hdem.hd_vehicle_count                               AS vehicle_count,
    ib.ib_lower_bound                                   AS income_lower_bound,
    ib.ib_upper_bound                                   AS income_upper_bound
FROM {{ source('bronze', 'customer') }} c
LEFT JOIN {{ source('bronze', 'customer_address') }} a
       ON c.c_current_addr_sk = a.ca_address_sk
LEFT JOIN {{ source('bronze', 'customer_demographics') }} cdem
       ON c.c_current_cdemo_sk = cdem.cd_demo_sk
LEFT JOIN {{ source('bronze', 'household_demographics') }} hdem
       ON c.c_current_hdemo_sk = hdem.hd_demo_sk
LEFT JOIN {{ source('bronze', 'income_band') }} ib
       ON hdem.hd_income_band_sk = ib.ib_income_band_sk
WHERE c.c_customer_sk IS NOT NULL
