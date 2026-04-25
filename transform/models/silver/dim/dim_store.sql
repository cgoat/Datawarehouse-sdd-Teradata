SELECT
    s_store_sk                                          AS store_key,
    s_store_id                                          AS store_id,
    TRIM(s_store_name)                                  AS store_name,
    TRIM(s_manager)                                     AS manager,
    TRIM(s_company_name)                                AS company_name,
    s_number_employees                                  AS employees,
    s_floor_space                                       AS floor_space,
    TRIM(s_hours)                                       AS hours,
    TRIM(s_city)                                        AS city,
    TRIM(s_county)                                      AS county,
    s_state                                             AS state,
    TRIM(s_zip)                                         AS zip,
    TRIM(s_country)                                     AS country,
    s_gmt_offset                                        AS gmt_offset,
    s_tax_precentage                                    AS tax_percentage,
    s_rec_start_date                                    AS rec_start_date,
    s_rec_end_date                                      AS rec_end_date,
    CASE WHEN s_rec_end_date IS NULL THEN 1 ELSE 0 END  AS is_current
FROM {{ source('bronze', 'store') }}
WHERE s_store_sk IS NOT NULL
