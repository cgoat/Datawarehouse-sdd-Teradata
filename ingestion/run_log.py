"""Writes pipeline run events to DW_DQ.run_log — powers the reliability dashboard."""
from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime

from .db import connect, db_names


@dataclass
class Step:
    batch_id: str
    layer: str
    step: str
    _started_at: datetime | None = None
    _t0: float | None = None

    def __enter__(self):
        self._started_at = datetime.utcnow().replace(microsecond=0)
        self._t0 = time.time()
        _insert(self, status="started", rows_in=None, rows_out=None,
                tool=None, message=None)
        return self

    def __exit__(self, exc_type, exc, _tb):
        ended_at = datetime.utcnow().replace(microsecond=0)
        duration = round(time.time() - (self._t0 or 0), 2)
        if exc_type is None:
            _update(self, "success", ended_at, duration, message=None,
                    rows_in=getattr(self, "rows_in", None),
                    rows_out=getattr(self, "rows_out", None),
                    tool=getattr(self, "tool", None))
        else:
            _update(self, "failed", ended_at, duration,
                    message=str(exc)[:3900], tool=getattr(self, "tool", None))
        return False  # never swallow

    def record(
        self,
        rows_in: int | None = None,
        rows_out: int | None = None,
        tool: str | None = None,
    ) -> None:
        self.rows_in = rows_in
        self.rows_out = rows_out
        if tool is not None:
            self.tool = tool


def _insert(s: Step, *, status, rows_in, rows_out, tool, message) -> None:
    dq = db_names()["dq"]
    sql = (
        f"INSERT INTO {dq}.run_log "
        "(batch_id, layer, step, status, rows_in, rows_out, "
        " started_at, ended_at, duration_sec, tool, message) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?)"
    )
    with connect() as conn, conn.cursor() as cur:
        cur.execute(sql, [s.batch_id, s.layer, s.step, status, rows_in, rows_out,
                          s._started_at, None, None, tool, message])


def _update(s: Step, status, ended_at, duration, *,
            message, rows_in=None, rows_out=None, tool=None) -> None:
    dq = db_names()["dq"]
    sql = (
        f"UPDATE {dq}.run_log SET status=?, ended_at=?, duration_sec=?, "
        "rows_in=?, rows_out=?, tool=COALESCE(?, tool), message=? "
        "WHERE batch_id=? AND step=? AND status='started'"
    )
    with connect() as conn, conn.cursor() as cur:
        cur.execute(sql, [status, ended_at, duration, rows_in, rows_out, tool, message,
                          s.batch_id, s.step])
