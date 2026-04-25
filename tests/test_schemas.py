"""Pure-Python tests — no Teradata needed. Guards the column-contract that
load_csv relies on: column count matches the file's pipe count, no dups,
every .dat file we ship has a schema."""
from __future__ import annotations

from pathlib import Path

import pytest

from ingestion.schemas import TABLES

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# TPC-DS v2.10 canonical column counts.
EXPECTED_COUNTS = {
    "call_center": 31, "catalog_page": 9, "catalog_returns": 27, "catalog_sales": 34,
    "customer": 18, "customer_address": 13, "customer_demographics": 9, "date_dim": 28,
    "dbgen_version": 4, "household_demographics": 5, "income_band": 3, "inventory": 4,
    "item": 22, "promotion": 19, "reason": 3, "ship_mode": 6, "store": 29,
    "store_returns": 20, "store_sales": 23, "time_dim": 10, "warehouse": 14,
    "web_page": 14, "web_returns": 24, "web_sales": 34, "web_site": 26,
}


def test_all_25_tables_defined():
    assert set(TABLES) == set(EXPECTED_COUNTS)


@pytest.mark.parametrize("table", sorted(EXPECTED_COUNTS))
def test_column_count_matches_spec(table: str):
    assert len(TABLES[table]) == EXPECTED_COUNTS[table], \
        f"{table}: got {len(TABLES[table])}, expected {EXPECTED_COUNTS[table]}"


@pytest.mark.parametrize("table", sorted(EXPECTED_COUNTS))
def test_no_duplicate_columns(table: str):
    cols = TABLES[table]
    assert len(set(cols)) == len(cols), f"{table} has duplicate column names"


@pytest.mark.skipif(not DATA_DIR.exists(), reason="data/ not present")
@pytest.mark.parametrize("table", sorted(EXPECTED_COUNTS))
def test_column_count_matches_file(table: str):
    """Reads one line from each .dat and checks the pipe count matches the schema."""
    path = DATA_DIR / f"{table}.dat"
    if not path.exists():
        pytest.skip(f"{path.name} not present")
    with path.open("r", encoding="utf-8", errors="replace") as f:
        line = f.readline().rstrip("\r\n")
    # dbgen -terminate n → no trailing pipe → fields = pipes + 1
    fields = line.count("|") + 1
    assert fields == len(TABLES[table]), \
        f"{table}.dat has {fields} fields but schema has {len(TABLES[table])}"
