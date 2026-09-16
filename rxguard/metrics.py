"""Governed KPI calculations used by every dashboard page."""
from __future__ import annotations

import numpy as np
import pandas as pd


def safe_ratio(numerator: float, denominator: float) -> float | None:
    return float(numerator) / float(denominator) if denominator else None


def executive_kpis(claims: pd.DataFrame) -> dict[str, float | int | None]:
    paid = claims[claims["claim_status"] == "PAID"]
    rejected = claims[claims["claim_status"] == "REJECTED"]
    gross = float(paid["gross_cost"].sum())
    return {
        "total_claims": int(len(claims)),
        "paid_claims": int(len(paid)),
        "gross_drug_cost": gross,
        "member_cost": float(paid["member_payment"].sum()),
        "plan_cost": float(paid["plan_payment"].sum()),
        "generic_dispensing_rate": safe_ratio(int((paid["brand_generic"] == "Generic").sum()), len(paid)),
        "rejection_rate": safe_ratio(len(rejected), len(claims)),
        "cost_per_paid_claim": safe_ratio(gross, len(paid)),
    }


def client_summary(claims: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (client_id, client_name), group in claims.groupby(["client_id", "client_name"], dropna=False):
        kpi = executive_kpis(group)
        rows.append({"client_id": client_id, "client_name": client_name, **kpi})
    return pd.DataFrame(rows).sort_values("plan_cost", ascending=False).reset_index(drop=True)


def monthly_summary(claims: pd.DataFrame) -> pd.DataFrame:
    frame = claims.copy()
    frame["month"] = frame["service_date"].dt.to_period("M").dt.to_timestamp()
    rows = []
    for dimensions, group in frame.groupby(["month", "client_id", "client_name"], dropna=False):
        rows.append({"month": dimensions[0], "client_id": dimensions[1], "client_name": dimensions[2], **executive_kpis(group)})
    return pd.DataFrame(rows)


def adherence_proxy(claims: pd.DataFrame, threshold: float = 0.80) -> pd.DataFrame:
    """Simple portfolio proxy; not a certified PDC or HEDIS measure."""
    eligible = claims[(claims["claim_status"] == "PAID") & claims["maintenance_flag"].astype(bool)].copy()
    if eligible.empty:
        return pd.DataFrame(columns=["client_name", "member_id", "drug_name", "fills", "days_supplied", "measurement_days", "pdc_proxy", "below_threshold"])
    eligible = eligible.sort_values("service_date")
    grouped = eligible.groupby(["client_name", "member_id", "drug_name"], as_index=False).agg(
        fills=("claim_id", "count"),
        days_supplied=("days_supply", "sum"),
        first_fill=("service_date", "min"),
        last_fill=("service_date", "max"),
        last_fill_days=("days_supply", "last"),
    )
    grouped = grouped[grouped["fills"] >= 2].copy()
    grouped["measurement_days"] = (
        (grouped["last_fill"] - grouped["first_fill"]).dt.days + grouped["last_fill_days"]
    ).clip(lower=1)
    grouped["pdc_proxy"] = (grouped["days_supplied"] / grouped["measurement_days"]).clip(upper=1.0)
    grouped["below_threshold"] = grouped["pdc_proxy"] < threshold
    return grouped.sort_values("pdc_proxy").reset_index(drop=True)


def drug_cost_trends(claims: pd.DataFrame) -> pd.DataFrame:
    paid = claims[claims["claim_status"] == "PAID"].copy()
    paid["month"] = paid["service_date"].dt.to_period("M").dt.to_timestamp()
    return paid.groupby(["month", "ndc", "drug_name", "therapeutic_class", "brand_generic"], as_index=False).agg(
        paid_claims=("claim_id", "count"),
        gross_cost=("gross_cost", "sum"),
        plan_cost=("plan_payment", "sum"),
        average_cost=("gross_cost", "mean"),
    )


def unusual_cost_increases(claims: pd.DataFrame, minimum_increase: float = 0.20) -> pd.DataFrame:
    trends = drug_cost_trends(claims).sort_values(["drug_name", "month"])
    if trends.empty:
        return trends
    rows = []
    for drug, group in trends.groupby("drug_name"):
        group = group.sort_values("month")
        if len(group) < 4:
            continue
        candidates = []
        for index in range(3, len(group)):
            current = group.iloc[index]
            baseline = float(group.iloc[index - 3:index]["average_cost"].mean())
            change = safe_ratio(float(current["average_cost"]) - baseline, baseline)
            if change is not None and change >= minimum_increase:
                candidates.append((change, current, baseline))
        if candidates:
            change, current, baseline = max(candidates, key=lambda item: item[0])
            rows.append({
                "drug_name": drug,
                "therapeutic_class": current["therapeutic_class"],
                "flagged_month": current["month"],
                "flagged_average_cost": float(current["average_cost"]),
                "prior_3_month_average": baseline,
                "increase_rate": change,
                "flagged_paid_claims": int(current["paid_claims"]),
            })
    return pd.DataFrame(rows).sort_values("increase_rate", ascending=False) if rows else pd.DataFrame(
        columns=["drug_name", "therapeutic_class", "flagged_month", "flagged_average_cost", "prior_3_month_average", "increase_rate", "flagged_paid_claims"]
    )


def generic_opportunity(claims: pd.DataFrame) -> pd.DataFrame:
    paid = claims[(claims["claim_status"] == "PAID") & claims["generic_equivalent_available"].astype(bool) & (claims["brand_generic"] == "Brand")]
    if paid.empty:
        return pd.DataFrame(columns=["drug_name", "therapeutic_class", "paid_claims", "gross_cost", "plan_cost", "average_cost"])
    return paid.groupby(["drug_name", "therapeutic_class"], as_index=False).agg(
        paid_claims=("claim_id", "count"),
        gross_cost=("gross_cost", "sum"),
        plan_cost=("plan_payment", "sum"),
        average_cost=("gross_cost", "mean"),
    ).sort_values("plan_cost", ascending=False)
