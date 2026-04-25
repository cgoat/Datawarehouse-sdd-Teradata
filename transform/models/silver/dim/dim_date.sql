SELECT
    d_date_sk                                             AS date_key,
    d_date                                                AS calendar_date,
    d_year                                                AS calendar_year,
    d_moy                                                 AS month_of_year,
    d_dom                                                 AS day_of_month,
    d_qoy                                                 AS quarter_of_year,
    TRIM(d_quarter_name)                                  AS quarter_name,
    d_week_seq                                            AS week_seq,
    d_month_seq                                           AS month_seq,
    d_quarter_seq                                         AS quarter_seq,
    d_dow                                                 AS day_of_week,
    TRIM(d_day_name)                                      AS day_name,
    CASE WHEN UPPER(d_weekend) = 'Y' THEN 1 ELSE 0 END    AS is_weekend,
    CASE WHEN UPPER(d_holiday) = 'Y' THEN 1 ELSE 0 END    AS is_holiday,
    CASE WHEN UPPER(d_current_day)  = 'Y' THEN 1 ELSE 0 END AS is_current_day,
    CASE WHEN UPPER(d_current_week) = 'Y' THEN 1 ELSE 0 END AS is_current_week,
    CASE WHEN UPPER(d_current_month)= 'Y' THEN 1 ELSE 0 END AS is_current_month,
    CASE WHEN UPPER(d_current_year) = 'Y' THEN 1 ELSE 0 END AS is_current_year
FROM {{ source('bronze', 'date_dim') }}
WHERE d_date_sk IS NOT NULL
