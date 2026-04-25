"""Run DDL scripts idempotently against Teradata.

Splits on `;`, skips comments/blanks, and treats "already exists" errors
(3802 = table, 3803 = database) as a pass — so re-running is safe.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from .db import connect

DDL_DIR = Path(__file__).resolve().parent.parent / "teradata" / "ddl"
ALREADY_EXISTS_CODES = {"3802", "3803", "5303", "5628"}  # table/db/database obj already exists


def _strip_comments(sql: str) -> str:
    sql = re.sub(r"--[^\n]*", "", sql)
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
    return sql


def _statements(sql: str) -> list[str]:
    return [s.strip() for s in _strip_comments(sql).split(";") if s.strip()]


def run_file(path: Path) -> None:
    print(f"\n=== {path.name} ===")
    with connect() as conn, conn.cursor() as cur:
        for stmt in _statements(path.read_text()):
            head = stmt[:60].replace("\n", " ")
            try:
                cur.execute(stmt)
                print(f"  OK  {head}")
            except Exception as e:
                msg = str(e)
                if any(code in msg for code in ALREADY_EXISTS_CODES):
                    print(f"  SKIP(exists)  {head}")
                else:
                    print(f"  FAIL  {head}\n    {msg[:300]}")
                    raise


def main(files: list[str] | None = None) -> int:
    targets = [DDL_DIR / f for f in files] if files else sorted(DDL_DIR.glob("*.sql"))
    for p in targets:
        run_file(p)
    print("\nSetup complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or None))
