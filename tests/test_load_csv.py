"""Loader unit tests — exercise the pandas read path without touching Teradata."""
from __future__ import annotations

import pandas as pd


def test_pipe_parsing_matches_schema(tmp_path):
    from ingestion.schemas import TABLES
    cols = TABLES["reason"]  # 3 cols, tiny
    fake = tmp_path / "reason.dat"
    fake.write_text("1|AAAA|unsatisfied\n2|BBBB|\n", encoding="utf-8")
    df = pd.read_csv(
        fake, sep="|", header=None, names=cols,
        dtype=str, keep_default_na=False, na_values=[""],
    )
    assert list(df.columns) == cols
    assert len(df) == 2
    assert df.loc[0, "r_reason_desc"] == "unsatisfied"
    assert pd.isna(df.loc[1, "r_reason_desc"])  # empty → NULL
