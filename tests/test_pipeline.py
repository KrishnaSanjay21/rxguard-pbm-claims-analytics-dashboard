from pathlib import Path
import sqlite3

from rxguard.etl import refresh
from rxguard.store import claims, quality_summary
from rxguard.synthetic import generate_synthetic_data


def test_synthetic_generation_and_sql_quality_pipeline(tmp_path: Path):
    source = tmp_path / "source"
    negative = tmp_path / "negative"
    counts = generate_synthetic_data(source, negative, seed=7, member_count=120)
    assert counts["clients"] == 5
    assert counts["drugs"] == 20
    assert counts["claims"] > 500
    assert (negative / "claims_broken.csv").exists()

    db = tmp_path / "rxguard.db"
    log = tmp_path / "refresh.csv"
    result = refresh(source, db, log, generate_if_missing=False)
    assert result["status"] == "PASS_WITH_WARNINGS"
    assert result["source_claims"] > result["valid_claims"]
    assert result["quality_issues"] >= 8

    valid = claims(True, db)
    all_rows = claims(False, db)
    assert len(valid) < len(all_rows)
    assert valid["is_valid_claim"].all()
    checks = quality_summary(db).set_index("check_name")["issue_count"]
    assert checks["duplicate_claims"] >= 2
    assert checks["reconciliation_failures"] >= 1
    assert checks["invalid_amounts"] >= 1
