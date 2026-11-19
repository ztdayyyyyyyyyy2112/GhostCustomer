"""SQLite storage foundation (BE-03); existing JSON-backed API remains the consumer contract."""
from contextlib import contextmanager
from pathlib import Path
import sqlite3

SCHEMA = Path(__file__).resolve().parents[1] / "sql" / "schema.sql"

@contextmanager
def connect(path: Path):
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def initialize(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as conn:
        conn.executescript(SCHEMA.read_text(encoding="utf-8"))
