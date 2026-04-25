-- Per-customer 360: demographics + LTV + RFM scoring + segment + preferred channel.
-- "Today" is anchored to MAX(d_date) seen in fact_sales — TPC-DS data is historical,
-- so anchoring to dataset-relative now keeps RFM math meaningful.

{{ config(
    materialized='table',
    post_hook=[
        "COLLECT STATISTICS ON {{ this }} COLUMN (customer_key)",
        "COLLECT STATISTICS ON {{ this }} COLUMN (segment)"
    ]
) }}

WITH date_anchor AS (
    SELECT MAX(d.calendar_date) AS today
    FROM {{ ref('fact_sales') }} fs
    INNER JOIN {{ ref('dim_date') }} d ON fs.sold_date_sk = d.date_key
),
customer_sales AS (
    SELECT
        customer_sk,
        MIN(sold_date_sk) AS first_purchase_date_key,
        MAX(sold_date_sk) AS last_purchase_date_key,
        COUNT(DISTINCT channel || '-' || CAST(sale_order_id AS VARCHAR(20))) AS frequency,
        SUM(quantity)     AS lifetime_units,
        SUM(net_paid)     AS lifetime_value,
        COUNT(DISTINCT channel) AS channels_used
    FROM {{ ref('fact_sales') }}
    WHERE customer_sk IS NOT NULL
    GROUP BY customer_sk
),
preferred_channel AS (
    SELECT customer_sk, channel
    FROM (
        SELECT
            customer_sk, channel,
            ROW_NUMBER() OVER (PARTITION BY customer_sk ORDER BY SUM(net_paid) DESC) AS rn
        FROM {{ ref('fact_sales') }}
        WHERE customer_sk IS NOT NULL
        GROUP BY customer_sk, channel
    ) t
    WHERE rn = 1
),
rfm_scored AS (
    SELECT
        csale.customer_sk,
        csale.first_purchase_date_key,
        csale.last_purchase_date_key,
        d_last.calendar_date                                                  AS last_purchase_date,
        CAST((da.today - d_last.calendar_date) AS INTEGER)                    AS recency_days,
        csale.frequency,
        csale.lifetime_value                                            AS monetary,
        csale.lifetime_units,
        csale.channels_used,
        {{ quintile('(da.today - d_last.calendar_date)', 'DESC') }}      AS r_score,
        {{ quintile('csale.frequency',      'ASC') }}                    AS f_score,
        {{ quintile('csale.lifetime_value', 'ASC') }}                    AS m_score
    FROM customer_sales csale
    INNER JOIN {{ ref('dim_date') }} d_last
           ON csale.last_purchase_date_key = d_last.date_key
    CROSS JOIN date_anchor da
)
SELECT
    c.customer_key,
    c.customer_id,
    c.customer_name,
    c.email_address,
    c.city, c.state, c.zip, c.country,
    c.gender, c.marital_status, c.education_status,
    c.credit_rating,
    c.income_lower_bound, c.income_upper_bound,
    c.is_preferred_customer,
    rfm.first_purchase_date_key,
    rfm.last_purchase_date_key,
    rfm.last_purchase_date,
    rfm.recency_days,
    rfm.frequency,
    rfm.monetary                                                     AS lifetime_value,
    rfm.lifetime_units,
    rfm.channels_used,
    rfm.r_score, rfm.f_score, rfm.m_score,
    CAST(rfm.r_score AS VARCHAR(1))
        || CAST(rfm.f_score AS VARCHAR(1))
        || CAST(rfm.m_score AS VARCHAR(1))                           AS rfm_code,
    CASE
        WHEN rfm.r_score >= 4 AND rfm.f_score >= 4 AND rfm.m_score >= 4 THEN 'Champion'
        WHEN rfm.r_score >= 3 AND rfm.f_score >= 3                       THEN 'Loyal'
        WHEN rfm.r_score >= 4 AND rfm.f_score <= 2                       THEN 'New'
        WHEN rfm.r_score <= 2 AND rfm.f_score >= 3                       THEN 'At Risk'
        WHEN rfm.r_score = 1                                              THEN 'Lost'
        WHEN rfm.r_score IS NULL                                          THEN 'Inactive'
        ELSE 'Potential'
    END                                                              AS segment,
    pc.channel                                                       AS preferred_channel
FROM {{ ref('dim_customer') }} c
LEFT JOIN rfm_scored        rfm ON c.customer_key = rfm.customer_sk
LEFT JOIN preferred_channel pc  ON c.customer_key = pc.customer_sk
