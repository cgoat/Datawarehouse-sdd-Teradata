"""Silver GE suite — verifies cleaning rules held (no anomalies leaked into fact)
and dim keys are unique. Ran against DW_SILVER."""
from __future__ import annotations

from typing import Any


def silver_expectations() -> dict[str, list[dict[str, Any]]]:
    return {
        "fact_sales": [
            {"expectation_type": "expect_column_values_to_not_be_null",
             "kwargs": {"column": "item_sk"}},
            {"expectation_type": "expect_column_values_to_not_be_null",
             "kwargs": {"column": "sold_date_sk"}},
            {"expectation_type": "expect_column_values_to_be_in_set",
             "kwargs": {"column": "channel", "value_set": ["store", "catalog", "web"]}},
            {"expectation_type": "expect_column_values_to_be_between",
             "kwargs": {"column": "quantity", "min_value": 1, "max_value": 1000}},
            {"expectation_type": "expect_column_values_to_be_between",
             "kwargs": {"column": "sales_price", "min_value": 0, "max_value": 100000,
                        "mostly": 0.999}},
        ],
        "fact_returns": [
            {"expectation_type": "expect_column_values_to_not_be_null",
             "kwargs": {"column": "item_sk"}},
            {"expectation_type": "expect_column_values_to_be_in_set",
             "kwargs": {"column": "channel", "value_set": ["store", "catalog", "web"]}},
            {"expectation_type": "expect_column_values_to_be_between",
             "kwargs": {"column": "return_quantity", "min_value": 1, "max_value": 1000}},
        ],
        "dim_customer": [
            {"expectation_type": "expect_column_values_to_not_be_null",
             "kwargs": {"column": "customer_key"}},
            {"expectation_type": "expect_column_values_to_be_unique",
             "kwargs": {"column": "customer_key"}},
        ],
        "dim_item": [
            {"expectation_type": "expect_column_values_to_not_be_null",
             "kwargs": {"column": "item_key"}},
            {"expectation_type": "expect_column_values_to_be_unique",
             "kwargs": {"column": "item_key"}},
        ],
        "dim_date": [
            {"expectation_type": "expect_column_values_to_not_be_null",
             "kwargs": {"column": "date_key"}},
            {"expectation_type": "expect_column_values_to_be_unique",
             "kwargs": {"column": "date_key"}},
            {"expectation_type": "expect_column_values_to_be_between",
             "kwargs": {"column": "calendar_year", "min_value": 1900, "max_value": 2100}},
        ],
        "dim_store": [
            {"expectation_type": "expect_column_values_to_be_unique",
             "kwargs": {"column": "store_key"}},
        ],
    }
