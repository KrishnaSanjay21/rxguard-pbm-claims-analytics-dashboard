"""CSV-to-SQLite refresh pipeline with logged row counts and quality results."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import sqlite3

import pandas as pd

from rxguard.config import DB_PATH, REFRESH_LOG, ROOT, SOURCE_DIR
from rxguard.synthetic import generate_synthetic_data


REQUIRED_COLUMNS = {
    "clients": {"client_id", "client_name", "industry", "region", "cost_factor"},
    "members": {"member_id", "client_id", "age", "sex", "risk_level", "effective_date", "termination_date"},
    "drugs": {"ndc", "drug_name", "therapeutic_class", "brand_generic", "maintenance_flag", "generic_equivalent_available", "reference_cost"},
    "claims": {"claim_id", "client_id", "member_id", "service_date", "ndc", "days_supply", "claim_status", "rejection_reason", "gross_cost", "member_payment", "plan_payment", "pharmacy_type", "processed_at"},
}


def _load_csv(source_dir: Path, name: str) -> pd.DataFrame:
    path = source_dir / f"{name}.csv"
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    missing = REQUIRED_COLUMNS[name] - set(frame.columns)
    if missing:
        raise ValueError(f"{path.name} missing columns: {', '.join(sorted(missing))}")
    return frame


def _hash_sources(source_dir: Path) -> str:
    digest = hashlib.sha256()
    for name in sorted(REQUIRED_COLUMNS):
        path = source_dir / f"{name}.csv"
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _coerce_types(frames: dict[str, pd.DataFrame]) -> None:
    for column in ["age"]:
        frames["members"][column] = pd.to_numeric(frames["members"][column], errors="coerce")
    for column in ["cost_factor"]:
        frames["clients"][column] = pd.to_numeric(frames["clients"][column], errors="coerce")
    for column in ["maintenance_flag", "generic_equivalent_available"]:
        frames["drugs"][column] = frames["drugs"][column].map({"True": 1, "False": 0, "1": 1, "0": 0}).fillna(0).astype(int)
    frames["drugs"]["reference_cost"] = pd.to_numeric(frames["drugs"]["reference_cost"], errors="coerce")
    for column in ["days_supply", "gross_cost", "member_payment", "plan_payment"]:
        frames["claims"][column] = pd.to_numeric(frames["claims"][column], errors="coerce")


def refresh(
    source_dir: Path = SOURCE_DIR,
    db_path: Path = DB_PATH,
    log_path: Path = REFRESH_LOG,
    generate_if_missing: bool = True,
) -> dict:
    source_dir, db_path, log_path = Path(source_dir), Path(db_path), Path(log_path)
    if generate_if_missing and not all((source_dir / f"{name}.csv").exists() for name in REQUIRED_COLUMNS):
        generate_synthetic_data(output_dir=source_dir, negative_dir=source_dir.parent / "negative")

    started = datetime.now(timezone.utc)
    frames = {name: _load_csv(source_dir, name) for name in REQUIRED_COLUMNS}
    _coerce_types(frames)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as connection:
        for name, frame in frames.items():
            frame.to_sql(f"{name}_raw", connection, if_exists="replace", index=False)
        connection.executescript((ROOT / "sql" / "model.sql").read_text(encoding="utf-8"))
        checks = dict(connection.execute((ROOT / "sql" / "quality_checks.sql").read_text(encoding="utf-8")).fetchall())
        valid_claims = connection.execute("SELECT COUNT(*) FROM vw_claims_enriched WHERE is_valid_claim = 1").fetchone()[0]
        connection.commit()

    result = {
        "refreshed_at_utc": started.isoformat(timespec="seconds"),
        "status": "PASS_WITH_WARNINGS" if any(checks.values()) else "PASS",
        "source_sha256": _hash_sources(source_dir),
        "source_claims": len(frames["claims"]),
        "valid_claims": valid_claims,
        "quality_issues": int(sum(checks.values())),
    }
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_frame = pd.DataFrame([result])
    log_frame.to_csv(log_path, mode="a", header=not log_path.exists(), index=False)
    return result


def read_refresh_log(log_path: Path = REFRESH_LOG, limit: int = 20) -> pd.DataFrame:
    path = Path(log_path)
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path).tail(limit).sort_index(ascending=False).reset_index(drop=True)
