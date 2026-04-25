"""Gold GE suite — light-touch sanity checks on the marts. Most semantic
correctness is enforced upstream (Silver tests + business rules). Here we
just guard against catastrophic regressions: empty marts, weird ranges."""
from __future__ import annotations

from typing import Any


def gold_expectations() -> dict[str, list[dict[str, Any]]]:
    return {
        "mart_sales_performance": [
            {"expectation_type": "expect_column_values_to_not_be_null",
             "kwargs": {"column": "date_key"}},
            {"expectation_type": "expect_column_values_to_be_in_set",
             "kwargs": {"column": "channel", "value_set": ["store", "catalog", "web"]}},
            {"expectation_type": "expect_column_values_to_be_between",
             "kwargs": {"column": "units_sold", "min_value": 1}},
        ],
        "mart_customer_360": [
            {"expectation_type": "expect_column_values_to_not_be_null",
             "kwargs": {"column": "customer_key"}},
            {"expectation_type": "expect_column_values_to_be_unique",
             "kwargs": {"column": "customer_key"}},
            {"expectation_type": "expect_column_values_to_be_in_set",
             "kwargs": {"column": "segment",
                        "value_set": ["Champion", "Loyal", "New", "At Risk",
                                       "Lost", "Inactive", "Potential", None]}},
        ],
        "mart_product_analytics": [
            {"expectation_type": "expect_column_values_to_be_unique",
             "kwargs": {"column": "item_key"}},
            {"expectation_type": "expect_column_values_to_be_between",
             "kwargs": {"column": "returns_rate", "min_value": 0, "max_value": 1,
                        "mostly": 0.99}},
        ],
        "mart_channel_comparison": [
            {"expectation_type": "expect_column_values_to_be_in_set",
             "kwargs": {"column": "channel", "value_set": ["store", "catalog", "web"]}},
            {"expectation_type": "expect_column_values_to_be_between",
             "kwargs": {"column": "share_of_total", "min_value": 0, "max_value": 1,
                        "mostly": 0.99}},
        ],
    }
