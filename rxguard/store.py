"""Read-only accessors for the refreshed SQLite analytical layer."""
from __future__ import annotations

from pathlib import Path
import sqlite3

import pandas as pd

from rxguard.config import DB_PATH
from rxguard.etl import refresh


def ensure_database(db_path: Path = DB_PATH) -> Path:
    path = Path(db_path)
    if not path.exists():
        refresh(db_path=path)
    return path


def _read_sql(query: str, db_path: Path = DB_PATH, params: tuple = ()) -> pd.DataFrame:
    path = ensure_database(db_path)
    with sqlite3.connect(path) as connection:
        return pd.read_sql_query(query, connection, params=params)


def claims(valid_only: bool = True, db_path: Path = DB_PATH) -> pd.DataFrame:
    where = "WHERE is_valid_claim = 1" if valid_only else ""
    frame = _read_sql(f"SELECT * FROM vw_claims_enriched {where}", db_path)
    for column in ["service_date", "processed_at"]:
        frame[column] = pd.to_datetime(frame[column], errors="coerce")
    for column in ["maintenance_flag", "generic_equivalent_available", "is_valid_claim"]:
        if column in frame:
            frame[column] = frame[column].fillna(0).astype(bool)
    return frame


def quality_details(db_path: Path = DB_PATH) -> pd.DataFrame:
    return _read_sql("SELECT * FROM vw_claim_quality WHERE issue_count > 0 ORDER BY issue_count DESC, claim_id", db_path)


def quality_summary(db_path: Path = DB_PATH) -> pd.DataFrame:
    return _read_sql((Path(__file__).resolve().parents[1] / "sql" / "quality_checks.sql").read_text(encoding="utf-8"), db_path)


def clients(db_path: Path = DB_PATH) -> pd.DataFrame:
    return _read_sql("SELECT * FROM clients_raw ORDER BY client_name", db_path)


def date_bounds(db_path: Path = DB_PATH) -> tuple[pd.Timestamp, pd.Timestamp]:
    frame = _read_sql("SELECT MIN(service_date) AS min_date, MAX(service_date) AS max_date FROM vw_claims_enriched WHERE is_valid_claim = 1", db_path)
    return pd.Timestamp(frame.loc[0, "min_date"]), pd.Timestamp(frame.loc[0, "max_date"])
