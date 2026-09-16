import pandas as pd

from rxguard.metrics import adherence_proxy, executive_kpis, generic_opportunity, unusual_cost_increases


def _claims() -> pd.DataFrame:
    months = pd.date_range("2025-01-01", periods=4, freq="MS")
    return pd.DataFrame({
        "claim_id": ["1", "2", "3", "4", "5", "6"],
        "client_name": ["Client A"] * 6,
        "client_id": ["A"] * 6,
        "member_id": ["M1", "M1", "M1", "M1", "M2", "M2"],
        "service_date": [*months, months[0], months[1]],
        "ndc": ["N1"] * 4 + ["N2", "N2"],
        "drug_name": ["Drug A"] * 4 + ["Brand B", "Brand B"],
        "therapeutic_class": ["Cardio"] * 4 + ["Respiratory", "Respiratory"],
        "brand_generic": ["Generic"] * 4 + ["Brand", "Brand"],
        "generic_equivalent_available": [False] * 4 + [True, True],
        "maintenance_flag": [True] * 6,
        "days_supply": [30] * 6,
        "claim_status": ["PAID", "PAID", "PAID", "PAID", "PAID", "REJECTED"],
        "gross_cost": [100, 100, 100, 150, 500, 0],
        "member_payment": [10, 10, 10, 15, 50, 0],
        "plan_payment": [90, 90, 90, 135, 450, 0],
    })


def test_executive_kpis_use_paid_claim_denominators():
    kpis = executive_kpis(_claims())
    assert kpis["total_claims"] == 6
    assert kpis["paid_claims"] == 5
    assert kpis["gross_drug_cost"] == 950
    assert kpis["generic_dispensing_rate"] == 0.8
    assert kpis["rejection_rate"] == 1 / 6
    assert kpis["cost_per_paid_claim"] == 190


def test_adherence_and_drug_signals():
    frame = _claims()
    adherence = adherence_proxy(frame)
    assert not adherence.empty
    assert adherence["pdc_proxy"].between(0, 1).all()
    opportunity = generic_opportunity(frame)
    assert opportunity.iloc[0]["drug_name"] == "Brand B"
    anomalies = unusual_cost_increases(frame, minimum_increase=0.20)
    assert anomalies.iloc[0]["drug_name"] == "Drug A"
