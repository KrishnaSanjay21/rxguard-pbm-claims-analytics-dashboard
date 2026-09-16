"""Deterministic, fully synthetic PBM portfolio generator."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from rxguard.config import SOURCE_DIR, NEGATIVE_DIR


CLIENTS = [
    ("CL001", "Atlas Manufacturing", "Manufacturing", "Midwest", 0.92),
    ("CL002", "BrightPath Schools", "Education", "Northeast", 0.84),
    ("CL003", "Cedar Retail Group", "Retail", "South", 1.05),
    ("CL004", "Northstar Logistics", "Transportation", "West", 1.12),
    ("CL005", "Summit Tech Labs", "Technology", "National", 1.28),
]

DRUGS = [
    ("00011-1111-01", "Atorvastatin 20 mg", "Cardiovascular", "Generic", True, False, 18.0),
    ("00022-2222-02", "Rosuvastatin 10 mg", "Cardiovascular", "Generic", True, False, 24.0),
    ("00033-3333-03", "Lipitor 20 mg", "Cardiovascular", "Brand", True, True, 185.0),
    ("00044-4444-04", "Lisinopril 10 mg", "Cardiovascular", "Generic", True, False, 12.0),
    ("00055-5555-05", "Metformin 500 mg", "Diabetes", "Generic", True, False, 16.0),
    ("00066-6666-06", "Januvia 100 mg", "Diabetes", "Brand", True, True, 515.0),
    ("00077-7777-07", "Ozempra Pen", "Diabetes", "Brand", True, False, 965.0),
    ("00088-8888-08", "Levothyroxine 50 mcg", "Endocrine", "Generic", True, False, 14.0),
    ("00099-9999-09", "Synthroid 50 mcg", "Endocrine", "Brand", True, True, 96.0),
    ("00110-1010-10", "Sertraline 50 mg", "Behavioral Health", "Generic", True, False, 17.0),
    ("00121-1111-11", "Escitalopram 10 mg", "Behavioral Health", "Generic", True, False, 19.0),
    ("00132-1212-12", "HumiraFlex", "Inflammatory", "Brand", True, False, 6_150.0),
    ("00143-1313-13", "EnbrelSure", "Inflammatory", "Brand", True, False, 5_720.0),
    ("00154-1414-14", "Albuterol HFA", "Respiratory", "Generic", False, False, 38.0),
    ("00165-1515-15", "Advair Diskus", "Respiratory", "Brand", True, True, 335.0),
    ("00176-1616-16", "Fluticasone/Salmeterol", "Respiratory", "Generic", True, False, 118.0),
    ("00187-1717-17", "Amoxicillin 500 mg", "Anti-infective", "Generic", False, False, 14.0),
    ("00198-1818-18", "Azithromycin 250 mg", "Anti-infective", "Generic", False, False, 22.0),
    ("00209-1919-19", "MigraRelief", "Neurology", "Brand", False, True, 410.0),
    ("00210-2020-20", "Sumatriptan 50 mg", "Neurology", "Generic", False, False, 32.0),
]


def _clients() -> pd.DataFrame:
    return pd.DataFrame(CLIENTS, columns=["client_id", "client_name", "industry", "region", "cost_factor"])


def _drugs() -> pd.DataFrame:
    return pd.DataFrame(
        DRUGS,
        columns=["ndc", "drug_name", "therapeutic_class", "brand_generic", "maintenance_flag",
                 "generic_equivalent_available", "reference_cost"],
    )


def _members(rng: np.random.Generator, clients: pd.DataFrame, count: int) -> pd.DataFrame:
    client_ids = np.resize(clients["client_id"].to_numpy(), count)
    rng.shuffle(client_ids)
    ages = np.clip(rng.normal(46, 15, count).round(), 18, 84).astype(int)
    effective = pd.to_datetime("2024-01-01") + pd.to_timedelta(rng.integers(0, 335, count), unit="D")
    terminated = rng.random(count) < 0.07
    termination = pd.Series(pd.NaT, index=range(count), dtype="datetime64[ns]")
    termination.loc[terminated] = pd.to_datetime("2026-01-01") + pd.to_timedelta(
        rng.integers(0, 180, terminated.sum()), unit="D"
    )
    return pd.DataFrame({
        "member_id": [f"MBR{i:06d}" for i in range(1, count + 1)],
        "client_id": client_ids,
        "age": ages,
        "sex": rng.choice(["F", "M", "X"], size=count, p=[0.50, 0.48, 0.02]),
        "risk_level": np.select([ages >= 65, ages >= 50], ["High", "Medium"], default="Low"),
        "effective_date": effective,
        "termination_date": termination,
    })


def _claim_rows(
    rng: np.random.Generator,
    members: pd.DataFrame,
    clients: pd.DataFrame,
    drugs: pd.DataFrame,
    start: str,
    end: str,
) -> pd.DataFrame:
    start_date, end_date = pd.Timestamp(start), pd.Timestamp(end)
    days = (end_date - start_date).days + 1
    client_factor = clients.set_index("client_id")["cost_factor"].to_dict()
    drug_weights = np.array([9, 5, 2, 8, 10, 4, 3, 7, 2, 8, 6, 1, 1, 5, 2, 3, 7, 4, 2, 4], dtype=float)
    drug_weights /= drug_weights.sum()
    rows: list[dict] = []
    claim_no = 1

    for member in members.itertuples(index=False):
        n_claims = int(rng.poisson(10) + 3)
        member_drugs = rng.choice(len(drugs), size=n_claims, replace=True, p=drug_weights)
        dates = np.sort(rng.integers(0, days, size=n_claims))
        for offset, drug_idx in zip(dates, member_drugs):
            drug = drugs.iloc[int(drug_idx)]
            service_date = start_date + pd.Timedelta(days=int(offset))
            status = rng.choice(["PAID", "REJECTED", "REVERSED"], p=[0.885, 0.085, 0.03])
            days_supply = int(rng.choice([30, 30, 30, 60, 90])) if drug["maintenance_flag"] else int(rng.choice([5, 7, 10, 14, 30]))
            trend = 1 + 0.0035 * max((service_date.year - 2025) * 12 + service_date.month - 1, 0)
            # One synthetic drug has a visible late-period price increase for anomaly analysis.
            if drug["drug_name"] == "Januvia 100 mg" and service_date >= pd.Timestamp("2026-04-01"):
                trend *= 1.30
            gross = max(float(drug["reference_cost"] * client_factor[member.client_id] * trend * rng.lognormal(0, 0.11)), 1)
            if status == "REJECTED":
                gross = member_pay = plan_pay = 0.0
                rejection = rng.choice(
                    ["Prior authorization required", "Refill too soon", "Drug not covered", "Invalid member ID", "Quantity limit"],
                    p=[0.31, 0.28, 0.20, 0.08, 0.13],
                )
            else:
                coinsurance = float(rng.choice([0.05, 0.10, 0.20, 0.25], p=[0.18, 0.42, 0.30, 0.10]))
                member_pay = min(gross * coinsurance, 250.0)
                plan_pay = gross - member_pay
                rejection = ""
            rows.append({
                "claim_id": f"CLM{claim_no:08d}",
                "client_id": member.client_id,
                "member_id": member.member_id,
                "service_date": service_date,
                "ndc": drug["ndc"],
                "days_supply": days_supply,
                "claim_status": status,
                "rejection_reason": rejection,
                "gross_cost": round(gross, 2),
                "member_payment": round(member_pay, 2),
                "plan_payment": round(plan_pay, 2),
                "pharmacy_type": rng.choice(["Retail", "Mail", "Specialty"], p=[0.77, 0.17, 0.06]),
                "processed_at": service_date + pd.to_timedelta(rng.integers(0, 3), unit="D"),
            })
            claim_no += 1

    frame = pd.DataFrame(rows)
    return frame.sort_values(["service_date", "claim_id"]).reset_index(drop=True)


def _inject_quality_issues(claims: pd.DataFrame) -> pd.DataFrame:
    """Add traceable, deliberately broken rows for the Data Quality page."""
    bad = claims.iloc[:8].copy()
    bad["claim_id"] = [
        claims.iloc[0]["claim_id"],
        "BAD-MISSING-MEMBER",
        "BAD-MISSING-NDC",
        "BAD-NEGATIVE-AMOUNT",
        "BAD-RECONCILIATION",
        "BAD-DATE",
        "BAD-CLIENT",
        "BAD-STATUS-REASON",
    ]
    bad.loc[bad.index[1], "member_id"] = ""
    bad.loc[bad.index[2], "ndc"] = ""
    bad.loc[bad.index[3], ["gross_cost", "member_payment", "plan_payment"]] = [-25.0, 0.0, -25.0]
    bad.loc[bad.index[4], ["gross_cost", "member_payment", "plan_payment"]] = [100.0, 20.0, 60.0]
    bad.loc[bad.index[5], "service_date"] = "2023-01-01"
    bad.loc[bad.index[6], "client_id"] = "UNKNOWN"
    bad.loc[bad.index[7], ["claim_status", "rejection_reason"]] = ["REJECTED", ""]
    return pd.concat([claims, bad], ignore_index=True)


def generate_synthetic_data(
    output_dir: Path = SOURCE_DIR,
    negative_dir: Path = NEGATIVE_DIR,
    seed: int = 42,
    member_count: int = 800,
) -> dict[str, int]:
    output_dir, negative_dir = Path(output_dir), Path(negative_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    negative_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    clients = _clients()
    drugs = _drugs()
    members = _members(rng, clients, member_count)
    valid_claims = _claim_rows(rng, members, clients, drugs, "2025-01-01", "2026-06-30")
    claims = _inject_quality_issues(valid_claims)

    for frame, name in [(clients, "clients"), (members, "members"), (drugs, "drugs"), (claims, "claims")]:
        frame.to_csv(output_dir / f"{name}.csv", index=False, date_format="%Y-%m-%d")
    claims.tail(8).to_csv(negative_dir / "claims_broken.csv", index=False, date_format="%Y-%m-%d")
    return {"clients": len(clients), "members": len(members), "drugs": len(drugs), "claims": len(claims)}
