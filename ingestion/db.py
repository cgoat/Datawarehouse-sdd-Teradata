"""Teradata connection helpers. All functions share the same env-driven config."""
from __future__ import annotations

import os
from contextlib import contextmanager

import teradatasql
from dotenv import load_dotenv

load_dotenv()


def _cfg() -> dict:
    missing = [k for k in ("TD_HOST", "TD_USER", "TD_PASSWORD") if not os.getenv(k)]
    if missing:
        raise RuntimeError(f"Missing env vars: {missing}. Copy .env.example → .env.")
    return {
        "host": os.environ["TD_HOST"],
        "user": os.environ["TD_USER"],
        "password": os.environ["TD_PASSWORD"],
        "dbs_port": os.getenv("TD_PORT", "1025"),
        "logmech": os.getenv("TD_LOGMECH", "TD2"),
    }


@contextmanager
def connect(database: str | None = None):
    conn = teradatasql.connect(**_cfg())
    try:
        if database:
            with conn.cursor() as cur:
                cur.execute(f"DATABASE {database}")
        yield conn
    finally:
        conn.close()


def db_names() -> dict[str, str]:
    return {
        "bronze": os.getenv("TD_DB_BRONZE", "DW_BRONZE"),
        "silver": os.getenv("TD_DB_SILVER", "DW_SILVER"),
        "gold":   os.getenv("TD_DB_GOLD",   "DW_GOLD"),
        "dq":     os.getenv("TD_DB_DQ",     "DW_DQ"),
    }
