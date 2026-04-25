-- One-time setup. Run as DBC.
-- Adjust PERM sizes to fit your appliance/VM.

CREATE DATABASE DW_BRONZE FROM DBC AS PERM = 2e9;
CREATE DATABASE DW_SILVER FROM DBC AS PERM = 2e9;
CREATE DATABASE DW_GOLD   FROM DBC AS PERM = 1e9;
CREATE DATABASE DW_DQ     FROM DBC AS PERM = 5e8;

-- Run log table used by ingestion + dbt + GE to report pipeline state.
CREATE TABLE DW_DQ.run_log (
    batch_id        VARCHAR(64)  NOT NULL,
    layer           VARCHAR(16)  NOT NULL,     -- bronze | silver | gold | dq
    step            VARCHAR(128) NOT NULL,     -- e.g. 'load_store_sales', 'dbt_test', 'ge_bronze'
    status          VARCHAR(16)  NOT NULL,     -- started | success | failed
    rows_in         BIGINT,
    rows_out        BIGINT,
    started_at      TIMESTAMP(0) NOT NULL,
    ended_at        TIMESTAMP(0),
    duration_sec    DECIMAL(10,2),
    tool            VARCHAR(32),                -- e.g. 'fastload' | 'executemany' | 'dbt' | 'ge'
    message         VARCHAR(4000)
)
PRIMARY INDEX (batch_id, step);

-- DQ failure log (filled by Great Expectations runner).
CREATE TABLE DW_DQ.dq_result (
    batch_id        VARCHAR(64)  NOT NULL,
    suite           VARCHAR(128) NOT NULL,
    table_name      VARCHAR(128) NOT NULL,
    expectation     VARCHAR(256) NOT NULL,
    success         BYTEINT      NOT NULL,    -- 0 | 1
    observed_value  VARCHAR(4000),
    run_at          TIMESTAMP(0) NOT NULL
)
PRIMARY INDEX (batch_id, suite);

-- Phase 3 — perf benchmark log. Each row is one execution of a benchmark
-- query, tagged with `phase` ('before' or 'after' the tune step) so the
-- dashboard can render a side-by-side delta.
CREATE TABLE DW_DQ.perf_log (
    run_id          VARCHAR(64)  NOT NULL,    -- groups N runs of the same suite
    phase           VARCHAR(16)  NOT NULL,    -- before | after
    query_name      VARCHAR(128) NOT NULL,
    iteration       INTEGER      NOT NULL,    -- 1..N within run_id
    duration_sec    DECIMAL(10,3) NOT NULL,
    rows_returned   BIGINT,
    started_at      TIMESTAMP(0) NOT NULL,
    notes           VARCHAR(4000)
)
PRIMARY INDEX (run_id, query_name);
