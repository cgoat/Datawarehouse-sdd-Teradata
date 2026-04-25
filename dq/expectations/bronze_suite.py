"""Programmatic Great Expectations suite for Bronze — built as code, not JSON,
so it version-controls cleanly and diffs sensibly in review."""
from __future__ import annotations

from typing import Any


def bronze_expectations() -> dict[str, list[dict[str, Any]]]:
    """Map table → list of expectation dicts (type + kwargs)."""
    return {
        "customer": [
            {"expectation_type": "expect_column_values_to_not_be_null",
             "kwargs": {"column": "c_customer_sk"}},
            {"expectation_type": "expect_column_values_to_be_unique",
             "kwargs": {"column": "c_customer_sk"}},
            {"expectation_type": "expect_column_values_to_be_unique",
             "kwargs": {"column": "c_customer_id"}},
            # c_preferred_cust_flag intentionally NOT tested at Bronze:
            # teradatasql returns CHAR(1) values padded to display width (e.g.
            # 'Y ' with a trailing space), so any value_set check fails
            # spuriously. The Silver dim_customer.is_preferred_customer column
            # (INT 0/1) is the cleaned form — test there if needed.
        ],
        "store_sales": [
            {"expectation_type": "expect_column_values_to_not_be_null",
             "kwargs": {"column": "ss_item_sk"}},
            {"expectation_type": "expect_column_values_to_not_be_null",
             "kwargs": {"column": "ss_ticket_number"}},
            {"expectation_type": "expect_column_values_to_be_between",
             "kwargs": {"column": "ss_quantity", "min_value": 0, "max_value": 1000,
                        "mostly": 0.999}},
            {"expectation_type": "expect_column_values_to_be_between",
             "kwargs": {"column": "ss_sales_price", "min_value": 0, "max_value": 100000,
                        "mostly": 0.999}},
        ],
        "catalog_sales": [
            {"expectation_type": "expect_column_values_to_not_be_null",
             "kwargs": {"column": "cs_item_sk"}},
            {"expectation_type": "expect_column_values_to_not_be_null",
             "kwargs": {"column": "cs_order_number"}},
        ],
        "web_sales": [
            {"expectation_type": "expect_column_values_to_not_be_null",
             "kwargs": {"column": "ws_item_sk"}},
            {"expectation_type": "expect_column_values_to_not_be_null",
             "kwargs": {"column": "ws_order_number"}},
        ],
        "date_dim": [
            {"expectation_type": "expect_column_values_to_be_unique",
             "kwargs": {"column": "d_date_sk"}},
            {"expectation_type": "expect_column_values_to_not_be_null",
             "kwargs": {"column": "d_date_sk"}},
            {"expectation_type": "expect_column_values_to_be_between",
             "kwargs": {"column": "d_year", "min_value": 1900, "max_value": 2100}},
        ],
        "item": [
            {"expectation_type": "expect_column_values_to_be_unique",
             "kwargs": {"column": "i_item_sk"}},
        ],
        "store": [
            {"expectation_type": "expect_column_values_to_be_unique",
             "kwargs": {"column": "s_store_sk"}},
        ],
    }
